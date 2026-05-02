import argparse
import contextlib
import json
import sys
import time
import traceback
from collections import Counter
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any, cast

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion, PathCompleter
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
    "search_recursive": {
        "type": bool,
        "default": True,
        "description": (
            "When /search runs, also match every sub-edge of each loaded edge."
        ),
    },
    "search_page_size": {
        "type": int,
        "default": 10,
        "description": "Number of /search results shown per page.",
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
    """Custom history that filters out blanks and consecutive duplicates."""

    def __init__(self, filename: str) -> None:
        super().__init__(filename)
        self.last_saved: str | None = None

    def store_string(self, string: str) -> None:
        if not string.strip():
            return
        if string == self.last_saved:
            return
        super().store_string(string)
        self.last_saved = string


class HyperedgeFormatter:
    """Formats Hyperedges with LISP-style indentation and rich colors."""

    def __init__(self, console: Console) -> None:
        self.console = console

    def format_atom(self, atom: Atom, dim: bool = False) -> Text:
        parts = atom.parts()
        result = Text()

        if len(parts) == 0:
            return result

        mtype = atom.mtype()
        type_color = TYPE_COLORS.get(mtype, "white")
        d = "dim " if dim else ""

        root = parts[0]
        result.append(root, style=f"{d}white")

        if len(parts) >= 2:
            result.append("/", style=f"{d}{type_color}")
            role_parts = parts[1].split(".")
            result.append(role_parts[0], style=f"{d}{type_color}")
            if len(role_parts) > 1:
                result.append(".", style=f"dim {type_color}")
                result.append(role_parts[1], style=f"italic {d}{type_color}")

        for i in range(2, len(parts)):
            result.append("/", style="dim white")
            result.append(parts[i], style="dim white")

        return result

    def format_hyperedge(
        self,
        edge: Hyperedge,
        indent_level: int = 0,
        inline: bool = False,
        highlight: Hyperedge | None = None,
        in_highlight: bool = False,
    ) -> Text:
        if edge is None:
            return Text("None", style="dim red")

        is_target = highlight is not None and edge is highlight
        dim_outside = highlight is not None and not in_highlight and not is_target
        descendant_in = in_highlight or is_target

        if edge.atom:
            atom = cast(Atom, edge)
            result = self.format_atom(atom, dim=dim_outside)
            if is_target:
                result.stylize("bold")
            return result

        result = Text()

        edge_type = edge.mtype()
        paren_color = TYPE_COLORS.get(edge_type, "white")
        d = "dim " if dim_outside else ""

        result.append("(", style=f"{d}bold {paren_color}")

        should_inline = inline or (edge.depth() <= 1 and edge.size() <= 3)

        if should_inline:
            for i, sub_edge in enumerate(edge):
                if i > 0:
                    result.append(" ")
                result.append(
                    self.format_hyperedge(
                        sub_edge,
                        indent_level + 1,
                        inline=True,
                        highlight=highlight,
                        in_highlight=descendant_in,
                    )
                )
        else:
            for i, sub_edge in enumerate(edge):
                if i > 0:
                    result.append("\n")
                    result.append(" " * (indent_level + 1) * 2)
                result.append(
                    self.format_hyperedge(
                        sub_edge,
                        indent_level + 1,
                        inline=False,
                        highlight=highlight,
                        in_highlight=descendant_in,
                    )
                )

        result.append(")", style=f"{d}bold {paren_color}")

        if is_target:
            result.stylize("bold")

        return result

    def format(self, edge: Hyperedge, highlight: Hyperedge | None = None) -> Text:
        return self.format_hyperedge(
            edge, indent_level=0, inline=False, highlight=highlight
        )


class CommandCompleter(Completer):
    """Auto-completer for slash commands."""

    # Commands whose argument is a filesystem path. The completer
    # delegates to ``PathCompleter`` once the user has typed past the
    # command name.
    PATH_ARG_COMMANDS = frozenset({"load"})

    def __init__(self, commands: dict) -> None:
        self.commands = commands
        self.path_completer = PathCompleter(expanduser=True)

    def get_completions(
        self,
        document: Document,
        complete_event: Any,  # noqa: ANN401
    ) -> Iterable[Completion]:
        text = document.text_before_cursor
        if not text.startswith("/"):
            return

        stripped = text[1:]
        if " " in stripped:
            cmd_name, _, arg = stripped.partition(" ")
            if cmd_name in self.PATH_ARG_COMMANDS:
                sub_doc = Document(text=arg, cursor_position=len(arg))
                yield from self.path_completer.get_completions(sub_doc, complete_event)
            return

        word = stripped
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

        # In-memory hyperedges loaded via /load or --load. Available for
        # parser-independent commands to operate on.
        self.edges: list[Hyperedge] = []
        self.edges_source: Path | None = None

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
            "load": {
                "help": "Load hyperedges from a .jsonl parse-results file",
                "handler": self.cmd_load,
            },
            "edges": {
                "help": "Show in-memory edges (count and source file)",
                "handler": self.cmd_edges,
            },
            "search": {
                "help": "Search loaded edges for hyperedges matching a pattern",
                "handler": self.cmd_search,
            },
            "count": {
                "help": "Count pattern matches across loaded edges (most common first)",
                "handler": self.cmd_count,
            },
            "types": {
                "help": (
                    "Count atom types across loaded edges "
                    "(optional main-type filter, e.g. /types M)"
                ),
                "handler": self.cmd_types,
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

    def _iter_subedges_ordered(self, edge: Hyperedge) -> Iterable[Hyperedge]:
        """Depth-first, document-order walk yielding edge then every descendant.
        Atoms terminate naturally because their __iter__ is empty."""
        yield edge
        if not edge.atom:
            for child in edge:
                yield from self._iter_subedges_ordered(child)

    def cmd_load(self, args: list) -> bool:
        if len(args) < 1:
            self.console.print(
                "[red]Error:[/red] /load requires a file path: "
                "[cyan]/load <path>[/cyan]"
            )
            return False

        path = Path(" ".join(args)).expanduser()
        if not path.is_file():
            self.console.print(f"[red]Error:[/red] file not found: [cyan]{path}[/cyan]")
            return False

        try:
            edges, skipped = self._load_edges_from_jsonl(path)
        except Exception as e:
            self.console.print(f"[red]Error:[/red] failed to read {path}: {e}")
            return False

        self.edges = edges
        self.edges_source = path
        self.console.print(
            f"[green]✓[/green] Loaded [cyan]{len(edges)}[/cyan] hyperedge(s) "
            f"from [cyan]{path}[/cyan]"
        )
        if skipped > 0:
            self.console.print(
                f"[yellow]Skipped {skipped} line(s) that could not be parsed[/yellow]"
            )
        return False

    def cmd_edges(self, args: list) -> bool:
        if not self.edges:
            self.console.print("[yellow]No edges loaded.[/yellow]")
            self.console.print(
                "[dim]Use[/dim] [cyan]/load <path>[/cyan] "
                "[dim]to load edges from a .jsonl file.[/dim]"
            )
            return False

        self.console.print(
            f"[green]{len(self.edges)}[/green] edge(s) loaded from "
            f"[cyan]{self.edges_source}[/cyan]"
        )
        return False

    def cmd_search(self, args: list) -> bool:
        if not args:
            self.console.print(
                "[red]Error:[/red] /search requires a pattern: "
                "[cyan]/search <pattern>[/cyan]"
            )
            return False
        if not self.edges:
            self.console.print("[yellow]No edges loaded.[/yellow]")
            self.console.print(
                "[dim]Use[/dim] [cyan]/load <path>[/cyan] [dim]first.[/dim]"
            )
            return False

        pattern_text = " ".join(args)
        try:
            pattern = hedge(pattern_text)
        except Exception as e:
            self.console.print(f"[red]Error:[/red] failed to parse pattern: {e}")
            return False
        if pattern is None:
            self.console.print(
                f"[red]Error:[/red] could not parse pattern: "
                f"[cyan]{pattern_text}[/cyan]"
            )
            return False

        recursive = bool(self.settings.get("search_recursive", True))
        page_size = int(self.settings.get("search_page_size", 10))
        if page_size < 1:
            page_size = 10

        hits: list[tuple[int, Hyperedge, Hyperedge, list[dict]]] = []
        for top_idx, top_edge in enumerate(self.edges):
            candidates: Iterable[Hyperedge] = (
                self._iter_subedges_ordered(top_edge) if recursive else [top_edge]
            )
            for sub in candidates:
                bindings = sub.match(pattern)
                if bindings:
                    hits.append((top_idx, top_edge, sub, bindings))

        if not hits:
            self.console.print(
                f"[yellow]No matches[/yellow] for [cyan]{pattern_text}[/cyan]"
            )
            return False

        self.console.print(
            f"[green]{len(hits)}[/green] match(es) "
            f"({'recursive' if recursive else 'top-level only'})"
        )
        self._paginate(
            hits,
            lambda n, hit: self._render_search_hit(n, *hit),
            page_size,
        )
        return False

    def _render_search_hit(
        self,
        n: int,
        top_idx: int,
        top_edge: Hyperedge,
        sub: Hyperedge,
        bindings: list[dict],
    ) -> None:
        self.console.print(f"[bold]#{n}[/bold] [dim](edge {top_idx})[/dim]")
        self.console.print(self.formatter.format(top_edge, highlight=sub))

        nonempty = [b for b in bindings if b]
        for bi, b in enumerate(nonempty):
            prefix = f"  bindings[{bi}]: " if len(nonempty) > 1 else "  bindings: "
            for var, val in b.items():
                line = Text()
                line.append(prefix, style="dim")
                line.append(f"{var} = ", style="dim")
                line.append(self.formatter.format(val))
                self.console.print(line)
        self.console.print()

    def _paginate(
        self,
        items: list[Any],
        render_fn: Callable[[int, Any], None],
        page_size: int,
    ) -> None:
        total = len(items)
        pages = (total + page_size - 1) // page_size
        page = 0
        while True:
            start = page * page_size
            end = min(start + page_size, total)
            self.console.print()
            self.console.print(
                f"[dim]-- page {page + 1}/{pages} "
                f"(results {start + 1}-{end} of {total}) --[/dim]"
            )
            for i in range(start, end):
                render_fn(i + 1, items[i])

            if pages == 1:
                return
            if page == pages - 1:
                self.console.print("[dim]-- end of results --[/dim]")
                return

            try:
                choice = (
                    self.session.prompt("[Enter] next  [p] prev  [q] quit > ")
                    .strip()
                    .lower()
                )
            except (KeyboardInterrupt, EOFError):
                self.console.print("[dim](aborted)[/dim]")
                return

            if choice in ("q", "quit", "exit"):
                return
            if choice == "p":
                if page > 0:
                    page -= 1
                continue
            page += 1

    def cmd_count(self, args: list) -> bool:
        if not args:
            self.console.print(
                "[red]Error:[/red] /count requires a pattern: "
                "[cyan]/count <pattern>[/cyan]"
            )
            return False
        if not self.edges:
            self.console.print("[yellow]No edges loaded.[/yellow]")
            self.console.print(
                "[dim]Use[/dim] [cyan]/load <path>[/cyan] [dim]first.[/dim]"
            )
            return False

        pattern_text = " ".join(args)
        try:
            pattern = hedge(pattern_text)
        except Exception as e:
            self.console.print(f"[red]Error:[/red] failed to parse pattern: {e}")
            return False
        if pattern is None:
            self.console.print(
                f"[red]Error:[/red] could not parse pattern: "
                f"[cyan]{pattern_text}[/cyan]"
            )
            return False

        recursive = bool(self.settings.get("search_recursive", True))
        page_size = int(self.settings.get("search_page_size", 10))
        if page_size < 1:
            page_size = 10

        # Counter key:
        #   - if the pattern has variables, key is sorted tuple of (var, value)
        #   - otherwise the matched (sub)edge itself
        counter: Counter[Any] = Counter()
        for top_edge in self.edges:
            candidates: Iterable[Hyperedge] = (
                self._iter_subedges_ordered(top_edge) if recursive else [top_edge]
            )
            for sub in candidates:
                bindings_list = sub.match(pattern)
                for b in bindings_list:
                    key: Any = tuple(sorted(b.items())) if b else sub
                    counter[key] += 1

        if not counter:
            self.console.print(
                f"[yellow]No matches[/yellow] for [cyan]{pattern_text}[/cyan]"
            )
            return False

        items = counter.most_common()
        self.console.print(
            f"[green]{sum(counter.values())}[/green] match(es), "
            f"[cyan]{len(counter)}[/cyan] distinct "
            f"({'recursive' if recursive else 'top-level only'})"
        )
        self._paginate(
            items,
            lambda n, item: self._render_count_row(n, item[0], item[1]),
            page_size,
        )
        return False

    def cmd_types(self, args: list) -> bool:
        if not self.edges:
            self.console.print("[yellow]No edges loaded.[/yellow]")
            self.console.print(
                "[dim]Use[/dim] [cyan]/load <path>[/cyan] [dim]first.[/dim]"
            )
            return False

        filter_main_type: str | None = None
        if args:
            filter_main_type = args[0]
            try:
                EdgeType(filter_main_type)
            except ValueError:
                valid = ", ".join(sorted(t.value for t in EdgeType))
                self.console.print(
                    f"[red]Error:[/red] unknown main type "
                    f"[cyan]{filter_main_type}[/cyan]. [dim]Valid:[/dim] {valid}"
                )
                return False

        page_size = int(self.settings.get("search_page_size", 10))
        if page_size < 1:
            page_size = 10

        counter: Counter[str] = Counter()
        for top_edge in self.edges:
            for atom in top_edge.all_atoms():
                if filter_main_type is not None and atom.mtype() != filter_main_type:
                    continue
                counter[atom.type()] += 1

        if not counter:
            if filter_main_type is not None:
                self.console.print(
                    f"[yellow]No atoms[/yellow] with main type "
                    f"[cyan]{filter_main_type}[/cyan]"
                )
            else:
                self.console.print("[yellow]No atoms found[/yellow]")
            return False

        items = counter.most_common()
        suffix = (
            f" filtered to main type [cyan]{filter_main_type}[/cyan]"
            if filter_main_type
            else ""
        )
        self.console.print(
            f"[green]{sum(counter.values())}[/green] atom(s), "
            f"[cyan]{len(counter)}[/cyan] distinct type(s)" + suffix
        )
        self._paginate(
            items,
            lambda n, item: self._render_types_row(n, item[0], item[1]),
            page_size,
        )
        return False

    def _render_types_row(self, n: int, type_str: str, count: int) -> None:
        color = "white"
        if type_str:
            with contextlib.suppress(ValueError):
                color = TYPE_COLORS.get(EdgeType(type_str[0]), "white")
        line = Text()
        line.append(f"#{n}  ", style="bold")
        line.append(f"{count}x  ", style="green")
        line.append(type_str, style=color)
        self.console.print(line)

    def _render_count_row(self, n: int, key: object, count: int) -> None:
        header = Text()
        header.append(f"#{n}  ", style="bold")
        header.append(f"{count}x", style="green")
        self.console.print(header)

        if isinstance(key, tuple):
            for var, val in key:
                line = Text()
                line.append("  ", style="dim")
                line.append(f"{var} = ", style="dim")
                line.append(self.formatter.format(val))
                self.console.print(line)
        elif isinstance(key, Hyperedge):
            self.console.print(Text("  ") + self.formatter.format(key))
        self.console.print()

    def _load_edges_from_jsonl(self, path: Path) -> tuple[list[Hyperedge], int]:
        edges: list[Hyperedge] = []
        skipped = 0
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                    edge_str = d.get("edge")
                    if not isinstance(edge_str, str):
                        skipped += 1
                        continue
                    edge = hedge(edge_str)
                    if edge is None:
                        skipped += 1
                        continue
                    edges.append(edge)
                except (json.JSONDecodeError, ValueError, TypeError):
                    skipped += 1
        return edges, skipped

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

    # CLI-only flags that should not be persisted in saved settings.
    load_path: str | None = getattr(args, "load", None)

    # Build initial settings: saved -> CLI args (CLI overrides saved).
    settings: dict[str, Any] = {}
    settings.update(saved)
    for key, value in vars(args).items():
        if value is None or key == "load":
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

    if load_path:
        session.cmd_load([load_path])

    session.run()
