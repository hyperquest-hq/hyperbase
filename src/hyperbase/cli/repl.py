import argparse
import json
import sys
import time
import traceback
from collections.abc import Iterable
from pathlib import Path
from typing import Any, cast

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from hyperbase.builders import hedge
from hyperbase.constants import EdgeType
from hyperbase.hyperedge import Atom, Hyperedge
from hyperbase.parsers import Parser, get_parser, list_parsers
from hyperbase.parsers.badness import badness_check
from hyperbase.parsers.repl_api import (
    CommandHandler,
    PostResultHook,
    PreResultHook,
    ReplContext,
    StatsProvider,
)

SETTINGS_FILE = Path.home() / ".hyperbase_repl_settings.json"

DEFAULT_PARSER = "generative"

# Legacy setting key -> current key. Applied once when loading saved
# settings so users upgrading across the plugin-extension refactor
# don't lose parser-specific config (e.g. the old CLI's ``--language``
# maps to the alphabeta parser's ``lang`` accepted_param).
LEGACY_SETTING_RENAMES: dict[str, str] = {
    "language": "lang",
}

# Built-in REPL settings (parser-independent). Parser plugins may add
# their own via ``register_setting`` from ``install_repl``.
BUILTIN_REPL_SETTINGS: dict[str, dict[str, Any]] = {
    "statistics": {
        "type": bool,
        "default": False,
        "description": "Show parse statistics after each parse.",
    },
    "check_badness": {
        "type": bool,
        "default": False,
        "description": "Run badness_check after each parse.",
    },
}


TYPE_COLORS = {
    EdgeType.CONCEPT: "#4A9EFF",
    EdgeType.MODIFIER: "#00E5CC",
    EdgeType.BUILDER: "#5DC4FF",
    EdgeType.PREDICATE: "#FF8C42",
    EdgeType.TRIGGER: "#00CDB8",
    EdgeType.CONJUNCTION: "#00FF87",
    EdgeType.RELATION: "#FFD700",
    EdgeType.SPECIFIER: "#FF6EC7",
}


def load_saved_settings() -> dict:
    try:
        return json.loads(SETTINGS_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_settings(settings: dict) -> None:
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2, default=str) + "\n")


def _coerce(value: Any, type_: type) -> Any:  # noqa: ANN401
    """Convert *value* (typically a string from the REPL) to *type_*."""
    if value is None:
        return None
    if isinstance(value, type_):
        return value
    if type_ is bool:
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "on")
        return bool(value)
    if type_ is int:
        return int(value)
    if type_ is float:
        return float(value)
    if type_ is str:
        return str(value)
    return value


def _build_parser_kwargs(parser_cls: type[Parser], settings: dict) -> dict[str, Any]:
    """Build keyword arguments for ``parser_cls(**kwargs)`` from settings."""
    kwargs: dict[str, Any] = {}
    for name in parser_cls.accepted_params():
        if name in settings and settings[name] is not None:
            kwargs[name] = settings[name]
    return kwargs


class FilteredFileHistory(FileHistory):
    """Custom history that filters out commands and duplicates."""

    def __init__(self, filename: str) -> None:
        super().__init__(filename)
        self.last_saved: str | None = None

    def store_string(self, string: str) -> None:
        if string.startswith("/"):
            return
        if string == self.last_saved:
            return
        if not string.strip():
            return
        super().store_string(string)
        self.last_saved = string


class HyperedgeFormatter:
    """Formats Hyperedges with LISP-style indentation and rich colors."""

    def __init__(self, console: Console) -> None:
        self.console = console

    def format_atom(self, atom: Atom) -> Text:
        parts = atom.parts()
        result = Text()

        if len(parts) == 0:
            return result

        mtype = atom.mtype()
        type_color = TYPE_COLORS.get(mtype, "white")

        root = parts[0]
        result.append(root, style="white")

        if len(parts) >= 2:
            result.append("/", style=f"{type_color}")
            role_parts = parts[1].split(".")
            result.append(role_parts[0], style=f"{type_color}")
            if len(role_parts) > 1:
                result.append(".", style=f"dim {type_color}")
                result.append(role_parts[1], style=f"italic {type_color}")

        for i in range(2, len(parts)):
            result.append("/", style="dim white")
            result.append(parts[i], style="dim white")

        return result

    def format_hyperedge(
        self, edge: Hyperedge, indent_level: int = 0, inline: bool = False
    ) -> Text:
        if edge is None:
            return Text("None", style="dim red")

        if edge.atom:
            atom = cast(Atom, edge)
            return self.format_atom(atom)

        result = Text()

        edge_type = edge.mtype()
        paren_color = TYPE_COLORS.get(edge_type, "white")

        result.append("(", style=f"bold {paren_color}")

        should_inline = inline or (edge.depth() <= 1 and edge.size() <= 3)

        if should_inline:
            for i, sub_edge in enumerate(edge):
                if i > 0:
                    result.append(" ")
                result.append(
                    self.format_hyperedge(sub_edge, indent_level + 1, inline=True)
                )
        else:
            for i, sub_edge in enumerate(edge):
                if i > 0:
                    result.append("\n")
                    result.append(" " * (indent_level + 1) * 2)
                result.append(
                    self.format_hyperedge(sub_edge, indent_level + 1, inline=False)
                )

        result.append(")", style=f"bold {paren_color}")

        return result

    def format(self, edge: Hyperedge) -> Text:
        return self.format_hyperedge(edge, indent_level=0, inline=False)


class CommandCompleter(Completer):
    """Auto-completer for slash commands."""

    def __init__(self, commands: dict) -> None:
        self.commands = commands

    def get_completions(
        self,
        document: Document,
        complete_event: Any,  # noqa: ANN401
    ) -> Iterable[Completion]:
        text = document.text_before_cursor
        if text.startswith("/"):
            word = text[1:]
            for cmd_name in self.commands:
                if cmd_name.startswith(word):
                    yield Completion(
                        cmd_name,
                        start_position=-len(word),
                        display=f"/{cmd_name}",
                        display_meta=self.commands[cmd_name]["help"],
                    )


class ReplSession:
    """Interactive REPL session.

    Plugin parsers extend this session via :meth:`Parser.install_repl`,
    which can register additional commands, settings, hooks, and stats
    providers. The core REPL contains no parser-specific behavior.
    """

    def __init__(self, parser_name: str, settings: dict[str, Any]) -> None:
        self.console = Console(force_terminal=True, color_system="auto")
        self.formatter = HyperedgeFormatter(self.console)

        self.settings: dict[str, Any] = dict(settings)
        self.settings.setdefault("parser", parser_name)

        # Per-parser registrations -- everything in these collections is
        # cleared and re-installed whenever the active parser changes.
        self._extra_settings: dict[str, dict[str, Any]] = {}
        self._extra_commands: dict[str, dict[str, Any]] = {}
        self._pre_result_hooks: list[PreResultHook] = []
        self._post_result_hooks: list[PostResultHook] = []
        self._stats_providers: list[StatsProvider] = []

        # Parser cache: cache_key -> Parser instance.
        self.parser_cache: dict[tuple, Parser] = {}
        self.parser_name: str = parser_name
        self.parser: Parser = self._init_parser(parser_name)

        history_file = Path.home() / ".hyperbase_repl_history"
        self.history = FilteredFileHistory(str(history_file))

        self._builtin_commands: dict[str, dict[str, Any]] = {
            "quit": {"help": "Exit the REPL", "handler": self.cmd_quit},
            "exit": {"help": "Exit the REPL", "handler": self.cmd_quit},
            "help": {"help": "Show available commands", "handler": self.cmd_help},
            "settings": {
                "help": "Show current settings",
                "handler": self.cmd_settings,
            },
            "set": {
                "help": "Change a setting (e.g. /set parser generative)",
                "handler": self.cmd_set,
            },
            "clear": {"help": "Clear the screen", "handler": self.cmd_clear},
            "parsers": {
                "help": "List all cached parsers",
                "handler": self.cmd_parsers,
            },
            "clear-parsers": {
                "help": "Clear all parsers from cache except the current one",
                "handler": self.cmd_clear_parsers,
            },
        }

        self.session = PromptSession(
            history=self.history,
            completer=CommandCompleter(self._all_commands()),
            complete_while_typing=False,
        )

    # ------------------------------------------------------------------
    # Plugin registration API (called from Parser.install_repl)
    # ------------------------------------------------------------------

    def register_command(
        self, name: str, help_str: str, handler: CommandHandler
    ) -> None:
        """Register a custom slash command. Cleared on parser switch."""
        self._extra_commands[name] = {"help": help_str, "handler": handler}

    def register_setting(
        self,
        name: str,
        default: Any,  # noqa: ANN401
        type_: type,
        description: str = "",
    ) -> None:
        """Register an extra REPL-only setting (display toggles, etc.).

        The setting is added to ``self.settings`` and shown in
        ``/settings`` / ``/set``. Existing values from saved settings
        take precedence over *default*.
        """
        self._extra_settings[name] = {
            "type": type_,
            "default": default,
            "description": description,
        }
        if name not in self.settings:
            self.settings[name] = default

    def register_pre_result_hook(self, hook: PreResultHook) -> None:
        self._pre_result_hooks.append(hook)

    def register_post_result_hook(self, hook: PostResultHook) -> None:
        self._post_result_hooks.append(hook)

    def register_stats_provider(self, provider: StatsProvider) -> None:
        self._stats_providers.append(provider)

    # ------------------------------------------------------------------
    # Parser lifecycle
    # ------------------------------------------------------------------

    def _reset_plugin_state(self) -> None:
        """Drop everything that was registered by the previous parser."""
        for name in self._extra_settings:
            self.settings.pop(name, None)
        self._extra_settings.clear()
        self._extra_commands.clear()
        self._pre_result_hooks.clear()
        self._post_result_hooks.clear()
        self._stats_providers.clear()

    def _init_parser(self, parser_name: str) -> Parser:
        """Instantiate *parser_name*, run its REPL installer, cache it."""
        parsers = list_parsers()
        if parser_name not in parsers:
            available = ", ".join(sorted(parsers)) or "(none)"
            raise ValueError(
                f"Parser {parser_name!r} is not installed. "
                f"Available parsers: {available}"
            )
        parser_cls = parsers[parser_name].load()

        # Make sure every accepted_param has at least its declared default
        # so the parser-class can rely on settings.get(name) below.
        for name, info in parser_cls.accepted_params().items():
            if (
                name not in self.settings or self.settings.get(name) is None
            ) and info.get("default") is not None:
                self.settings[name] = info["default"]

        # Fail fast if any required parameter is missing, so parser
        # constructors don't blow up with an opaque KeyError.
        missing = [
            name
            for name, info in parser_cls.accepted_params().items()
            if info.get("required") and self.settings.get(name) is None
        ]
        if missing:
            raise ValueError(
                f"Parser {parser_name!r} requires: {', '.join(missing)}. "
                f"Provide on the command line (e.g. --{missing[0]} <value>) "
                f"or inside the REPL with /set {missing[0]} <value>."
            )

        self._reset_plugin_state()
        kwargs = _build_parser_kwargs(parser_cls, self.settings)
        cache_key = parser_cls.cache_key_from_settings(self.settings)

        if cache_key in self.parser_cache:
            self.console.print("[dim]Using cached parser[/dim]")
            parser = self.parser_cache[cache_key]
        else:
            parser = get_parser(parser_name, **kwargs)
            self.parser_cache[cache_key] = parser

        parser.install_repl(self)

        # Apply plugin defaults the parser added on top, after potentially
        # overriding from saved settings.
        for name, info in self._extra_settings.items():
            cur = self.settings.get(name)
            if cur is None:
                self.settings[name] = info["default"]
        return parser

    def _switch_parser(self, parser_name: str) -> bool:
        try:
            self.parser = self._init_parser(parser_name)
            self.parser_name = parser_name
            self.settings["parser"] = parser_name
            # Refresh completer with the new command set.
            self.session.completer = CommandCompleter(self._all_commands())
            return True
        except Exception as e:
            self.console.print(f"[red]Failed to load parser {parser_name!r}: {e}[/red]")
            return False

    # ------------------------------------------------------------------
    # Command surface
    # ------------------------------------------------------------------

    def _all_commands(self) -> dict[str, dict[str, Any]]:
        merged: dict[str, dict[str, Any]] = {}
        merged.update(self._builtin_commands)
        merged.update(self._extra_commands)
        return merged

    def show_banner(self) -> None:
        available = sorted(list_parsers().keys())
        banner = Panel(
            Text.from_markup(
                "[bold cyan]Hyperbase REPL[/bold cyan]\n"
                "[dim]Interactive Semantic Hypergraph Parser[/dim]\n\n"
                f"[yellow]Parser:[/yellow] [green]{self.parser_name}[/green]\n"
                "[yellow]Installed parsers:[/yellow] "
                f"[green]{', '.join(available) or 'none'}[/green]\n\n"
                "[dim]Type [bold]/help[/bold] to see available commands[/dim]"
            ),
            box=box.DOUBLE,
            border_style="cyan",
            padding=(1, 2),
        )
        self.console.print(banner)
        self.console.print()

    def show_command_hints(self) -> None:
        table = Table(
            show_header=True,
            header_style="bold magenta",
            box=box.SIMPLE,
            padding=(0, 1),
        )
        table.add_column("Command", style="cyan")
        table.add_column("Description", style="white")

        for cmd_name, cmd_info in self._all_commands().items():
            table.add_row(f"/{cmd_name}", cmd_info["help"])

        self.console.print("\n[bold]Available Commands:[/bold]")
        self.console.print(table)
        self.console.print()

    def cmd_quit(self, args: list) -> bool:
        save_settings(self.settings)
        self.console.print("\n[yellow]Exiting...[/yellow]\n")
        return True

    def cmd_help(self, args: list) -> bool:
        self.show_command_hints()
        return False

    def cmd_settings(self, args: list) -> bool:
        table = Table(
            show_header=True,
            header_style="bold magenta",
            box=box.ROUNDED,
            padding=(0, 1),
        )
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        for key, value in self.settings.items():
            if value is not None:
                table.add_row(key, str(value))

        self.console.print()
        self.console.print(
            Panel(table, title="[bold]Current Settings[/bold]", border_style="blue")
        )
        self.console.print()
        return False

    def _setting_type(self, name: str) -> type | None:
        """Look up the declared type for *name* across all sources."""
        if name == "parser":
            return str
        if name in BUILTIN_REPL_SETTINGS:
            return BUILTIN_REPL_SETTINGS[name]["type"]
        if name in self._extra_settings:
            return self._extra_settings[name]["type"]
        params = type(self.parser).accepted_params()
        if name in params:
            return params[name].get("type")
        return None

    def cmd_set(self, args: list) -> bool:
        if len(args) < 2:
            self.console.print(
                "[red]Error:[/red] /set requires two arguments: "
                "[cyan]/set <setting> <value>[/cyan]"
            )
            self.console.print("[dim]Example:[/dim] /set parser generative")
            return False

        setting_name = args[0]
        raw_value: Any = " ".join(args[1:])

        type_ = self._setting_type(setting_name)
        if type_ is None:
            self.console.print(
                f"[red]Error:[/red] Unknown setting '[cyan]{setting_name}[/cyan]'"
            )
            self.console.print(
                f"[dim]Available settings:[/dim] {', '.join(self.settings.keys())}"
            )
            return False

        try:
            value = _coerce(raw_value, type_)
        except (TypeError, ValueError) as e:
            self.console.print(
                f"[red]Error:[/red] Invalid value for {setting_name}: {e}"
            )
            return False

        if setting_name == "parser":
            available = list_parsers()
            if value not in available:
                avail_str = ", ".join(sorted(available)) or "(none)"
                self.console.print(
                    f"[red]Error:[/red] parser must be one of: {avail_str}"
                )
                return False
            if not self._switch_parser(value):
                return False
            save_settings(self.settings)
            self.console.print(
                f"[green]✓[/green] Set [cyan]parser[/cyan] = [green]{value}[/green]"
            )
            return False

        self.settings[setting_name] = value
        save_settings(self.settings)
        self.console.print(
            f"[green]✓[/green] Set [cyan]{setting_name}[/cyan] = [green]{value}[/green]"
        )

        # If this setting affects parser instantiation, re-init the parser.
        parser_params = type(self.parser).accepted_params()
        if setting_name in parser_params and not self._switch_parser(self.parser_name):
            self.console.print(
                "[red]Failed to reload parser. Keeping previous parser.[/red]"
            )
        return False

    def cmd_clear(self, args: list) -> bool:
        self.console.clear()
        self.show_banner()
        return False

    def cmd_parsers(self, args: list) -> bool:
        table = Table(
            show_header=True,
            header_style="bold magenta",
            box=box.ROUNDED,
            padding=(0, 1),
        )
        table.add_column("Type", style="cyan")
        table.add_column("Settings", style="white")
        table.add_column("Current", style="green")

        current_key = type(self.parser).cache_key_from_settings(self.settings)

        for cache_key, cached_parser in self.parser_cache.items():
            cls = type(cached_parser)
            settings_str = cls.format_cache_key(cache_key)
            is_current = "✓" if cache_key == current_key else ""
            table.add_row(cls.__name__, settings_str, is_current)

        self.console.print()
        self.console.print(
            Panel(table, title="[bold]Cached Parsers[/bold]", border_style="blue")
        )
        self.console.print(
            f"[dim]Total: {len(self.parser_cache)} parser(s) in cache[/dim]\n"
        )
        return False

    def cmd_clear_parsers(self, args: list) -> bool:
        current_key = type(self.parser).cache_key_from_settings(self.settings)
        old_count = len(self.parser_cache)
        self.parser_cache = {current_key: self.parser}
        cleared_count = old_count - 1
        self.console.print(
            f"[green]✓[/green] Cleared [cyan]{cleared_count}[/cyan] "
            "parser(s) from cache"
        )
        return False

    def handle_command(self, text: str) -> bool:
        if not text.startswith("/"):
            return False

        parts = text[1:].split()
        if not parts:
            return False

        cmd_name = parts[0]
        cmd_args = parts[1:]

        commands = self._all_commands()
        if cmd_name not in commands:
            self.console.print(
                f"[red]Error:[/red] Unknown command '[cyan]/{cmd_name}[/cyan]'"
            )
            self.console.print(
                "[dim]Type[/dim] [bold]/help[/bold] "
                "[dim]to see available commands[/dim]"
            )
            return False

        return commands[cmd_name]["handler"](cmd_args)

    # ------------------------------------------------------------------
    # Parsing flow
    # ------------------------------------------------------------------

    def parse_text(self, text: str) -> None:
        try:
            start_time = time.perf_counter()
            parse_result = self.parser.parse(text)
            elapsed_time = time.perf_counter() - start_time

            if not parse_result:
                self.console.print()
                self.console.print(
                    Panel(
                        Text("FAILED", style="bold red"),
                        title="[yellow]Parse Result[/yellow]",
                        border_style="red",
                        box=box.ROUNDED,
                    )
                )
            else:
                total = len(parse_result)
                for i, result in enumerate(parse_result):
                    ctx = ReplContext(
                        session=self,
                        text=text,
                        parse_result=parse_result,
                        result=result,
                        edge=result.edge,
                        tokens=result.tokens,
                        elapsed_time=elapsed_time,
                    )

                    for hook in self._pre_result_hooks:
                        try:
                            hook(ctx)
                        except Exception as e:
                            self.console.print(
                                f"[red]pre-result hook failed: {e}[/red]"
                            )

                    self.console.print()

                    title = (
                        "[yellow]Parse Result[/yellow]"
                        if total == 1
                        else f"[yellow]Parse Result {i + 1}/{total}[/yellow]"
                    )
                    if total > 1:
                        self.console.print(Text(result.text, style="dim italic"))

                    if result.edge is None:
                        result_panel = Panel(
                            Text("FAILED", style="bold red"),
                            title=title,
                            border_style="red",
                            box=box.ROUNDED,
                        )
                    else:
                        result_panel = Panel(
                            self.formatter.format(result.edge),
                            title=title,
                            border_style="green",
                            box=box.ROUNDED,
                        )
                    self.console.print(result_panel)

                    for hook in self._post_result_hooks:
                        try:
                            hook(ctx)
                        except Exception as e:
                            self.console.print(
                                f"[red]post-result hook failed: {e}[/red]"
                            )

                    if self.settings.get("check_badness", False):
                        self._render_badness(ctx)

                    if (
                        result.edge is not None
                        and result.tokens is not None
                        and self.settings.get("statistics", False)
                    ):
                        self._render_statistics(ctx)

            # Display timing
            if elapsed_time < 0.1:
                time_color = "green"
            elif elapsed_time < 1.0:
                time_color = "yellow"
            else:
                time_color = "red"

            time_text = Text()
            time_text.append("Parse time: ", style="dim")
            time_text.append(f"{elapsed_time * 1000:.2f}ms", style=f"bold {time_color}")
            time_text.append(f" ({elapsed_time:.4f}s)", style="dim")

            self.console.print(time_text)
            self.console.print()

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Interrupted[/yellow]\n")
        except Exception as e:
            self.console.print(f"\n[red]Error:[/red] {e}\n")
            if hasattr(self.console, "print_exception"):
                self.console.print_exception()
            else:
                traceback.print_exc()
            self.console.print()

    def _render_badness(self, ctx: ReplContext) -> None:
        """Print the badness check panel for the current parse result."""
        if ctx.edge is None or ctx.tokens is None:
            return

        _edge = hedge(ctx.edge)
        if _edge is None:
            return
        badness_errors = badness_check(_edge, ctx.tokens)

        self.console.print()
        if not badness_errors:
            self.console.print(
                Panel(
                    Text("No errors found", style="green"),
                    title="[bold green]Badness Check[/bold green]",
                    border_style="green",
                    box=box.ROUNDED,
                )
            )
            return

        error_table = Table(
            show_header=True,
            header_style="bold red",
            box=box.SIMPLE,
            padding=(0, 1),
        )
        error_table.add_column("Type", style="cyan")
        error_table.add_column("Message", style="white")

        for key, errors in badness_errors.items():
            context = key
            if not isinstance(errors, list):
                continue
            for error in errors:
                if isinstance(error, tuple) and len(error) >= 2:
                    code, msg = error[0], error[1]
                    sev = error[2] if len(error) > 2 else "?"
                    error_table.add_row(
                        f"{code} [dim](sev:{sev})[/dim]\n[dim]({context})[/dim]",
                        msg,
                    )
                else:
                    error_table.add_row(f"[dim]({context})[/dim]", str(error))

        self.console.print(
            Panel(
                error_table,
                title="[bold red]Badness Check Failed[/bold red]",
                border_style="red",
                box=box.ROUNDED,
            )
        )

    def _render_statistics(self, ctx: ReplContext) -> None:
        """Print the statistics panel using core + plugin-provided rows."""
        self.console.print()
        stats_table = Table(
            show_header=False,
            box=box.SIMPLE,
            padding=(0, 1),
        )
        stats_table.add_column("Stat", style="cyan")
        stats_table.add_column("Value", style="green", justify="right")

        if ctx.tokens is not None:
            stats_table.add_row("External tokens", str(len(ctx.tokens)))

        for provider in self._stats_providers:
            try:
                rows = provider(ctx) or []
            except Exception as e:
                self.console.print(f"[red]stats provider failed: {e}[/red]")
                continue
            for label, value in rows:
                stats_table.add_row(label, value)

        if ctx.edge is not None:
            _edge = hedge(ctx.edge)
            if _edge:
                stats_table.add_row("Atoms", str(len(_edge.all_atoms())))

        self.console.print(
            Panel(
                stats_table,
                title="[bold blue]Statistics[/bold blue]",
                border_style="blue",
                box=box.ROUNDED,
            )
        )

    def get_bottom_toolbar(self) -> HTML:
        return HTML(
            "<b>Commands:</b> /help, /settings, /quit  |  "
            "<b>History:</b> up/down arrows"
        )

    def run(self) -> None:
        self.show_banner()

        while True:
            try:
                text = self.session.prompt(
                    HTML("<ansigreen><b>></b></ansigreen> "),
                    bottom_toolbar=self.get_bottom_toolbar,
                ).strip()

                if not text:
                    continue

                if text.startswith("/"):
                    should_quit = self.handle_command(text)
                    if should_quit:
                        break
                else:
                    self.parse_text(text)

            except KeyboardInterrupt:
                self.console.print("\n[yellow]Use /quit or /exit to exit[/yellow]\n")
                continue
            except EOFError:
                save_settings(self.settings)
                self.console.print("\n[yellow]Exiting...[/yellow]\n")
                break


def run_repl(args: argparse.Namespace) -> None:
    saved = load_saved_settings()

    # Migrate legacy saved-setting keys in place so users upgrading
    # across the plugin-extension refactor don't need to edit the file.
    for old_key, new_key in LEGACY_SETTING_RENAMES.items():
        if old_key in saved and new_key not in saved:
            saved[new_key] = saved.pop(old_key)

    parser_name: str = (
        getattr(args, "parser", None) or saved.get("parser") or DEFAULT_PARSER
    )

    # Build initial settings: saved -> CLI args (CLI overrides saved).
    settings: dict[str, Any] = {}
    settings.update(saved)
    for key, value in vars(args).items():
        if value is None:
            continue
        settings[key] = value

    # Built-in REPL settings get their declared defaults if absent.
    for name, info in BUILTIN_REPL_SETTINGS.items():
        if name not in settings or settings.get(name) is None:
            settings[name] = info["default"]

    settings["parser"] = parser_name

    try:
        session = ReplSession(parser_name, settings)
    except ValueError as e:
        console = Console(force_terminal=True, color_system="auto")
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    session.run()
