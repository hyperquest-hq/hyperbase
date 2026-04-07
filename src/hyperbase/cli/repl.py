import argparse
import json
import re
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
from rich.tree import Tree

from hyperbase.builders import hedge
from hyperbase.constants import EdgeType
from hyperbase.hyperedge import Atom, Hyperedge
from hyperbase.parsers import Parser, get_parser, list_parsers
from hyperbase.parsers.correctness import badness_check

SETTINGS_FILE = Path.home() / ".hyperbase_repl_settings.json"

DEFAULTS = {
    "parser": "generative",
    "model_path": "",
    "language": None,
    "max_length": 256,
    "num_beams": 1,
    "num_candidates": 1,
    "use_constraints": False,
    "check_badness": False,
    "statistics": False,
    "raw_output": False,
    "device": None,
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


def print_dependency_tree(
    token: Any,  # noqa: ANN401
    console: Console,
    visited: set | None = None,
) -> Tree | None:
    """Print dependency parse tree with dep_ and tag_ labels as a rich tree."""
    if visited is None:
        visited = set()

    if token in visited:
        return None
    visited.add(token)

    label = Text()
    label.append(token.text, style="bold white")
    label.append(" [", style="dim")
    label.append(f"dep_={token.dep_}", style="cyan")
    label.append(", ", style="dim")
    label.append(f"tag_={token.pos_}", style="yellow")
    label.append("]", style="dim")

    tree = Tree(label)

    for child in token.children:
        child_tree = print_dependency_tree(child, console, visited)
        if child_tree:
            tree.add(child_tree)

    return tree


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


def _parser_kwargs(settings: dict) -> dict:
    """Build keyword arguments for get_parser() from current settings."""
    parser_name = settings["parser"]
    kwargs: dict[str, Any] = {}

    if parser_name == "generative":
        if settings.get("model_path"):
            kwargs["model_path"] = settings["model_path"]
        if settings.get("device"):
            kwargs["device"] = settings["device"]
        if settings.get("max_length"):
            kwargs["max_length"] = settings["max_length"]
        if settings.get("num_beams"):
            kwargs["num_beams"] = settings["num_beams"]
        if settings.get("num_candidates"):
            kwargs["num_candidates"] = settings["num_candidates"]
        if settings.get("use_constraints"):
            kwargs["use_constraints"] = settings["use_constraints"]
    elif parser_name == "alphabeta":
        if settings.get("language"):
            kwargs["lang"] = settings["language"]

    return kwargs


class ReplSession:
    """Enhanced REPL session with modern TUI features."""

    def __init__(
        self, parser: Parser, parser_name: str, args: argparse.Namespace
    ) -> None:
        self.parser = parser
        self.parser_name = parser_name
        self.console = Console(force_terminal=True, color_system="auto")
        self.args = args
        self.formatter = HyperedgeFormatter(self.console)

        self.settings = {
            "parser": parser_name,
            "language": args.language,
            "max_length": args.max_length,
            "num_beams": args.num_beams,
            "num_candidates": args.num_candidates,
            "use_constraints": args.use_constraints,
            "model_path": args.model_path,
            "check_badness": args.check_badness,
            "statistics": args.statistics,
            "raw_output": False,
            "device": args.device,
        }

        self.parser_cache: dict[tuple, Any] = {}
        cache_key = self._get_cache_key()
        self.parser_cache[cache_key] = parser

        history_file = Path.home() / ".hyperbase_repl_history"
        self.history = FilteredFileHistory(str(history_file))

        self.commands = {
            "quit": {"help": "Exit the REPL", "handler": self.cmd_quit},
            "exit": {"help": "Exit the REPL", "handler": self.cmd_quit},
            "help": {"help": "Show available commands", "handler": self.cmd_help},
            "settings": {"help": "Show current settings", "handler": self.cmd_settings},
            "set": {
                "help": "Change a setting (e.g., /set parser generative)",
                "handler": self.cmd_set,
            },
            "clear": {"help": "Clear the screen", "handler": self.cmd_clear},
            "parsers": {"help": "List all cached parsers", "handler": self.cmd_parsers},
            "clear-parsers": {
                "help": "Clear all parsers from cache except the current one",
                "handler": self.cmd_clear_parsers,
            },
        }

        self.session = PromptSession(
            history=self.history,
            completer=CommandCompleter(self.commands),
            complete_while_typing=False,
        )

    def show_banner(self) -> None:
        available = sorted(list_parsers().keys())
        banner = Panel(
            Text.from_markup(
                "[bold cyan]Hyperbase REPL[/bold cyan]\n"
                "[dim]Interactive Semantic Hypergraph Parser[/dim]\n\n"
                f"[yellow]Parser:[/yellow] [green]{self.parser_name}[/green]\n"
                "[yellow]Language:[/yellow] "
                f"[green]{self.settings['language'] or 'N/A'}[/green]\n"
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

        for cmd_name, cmd_info in self.commands.items():
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

    def cmd_set(self, args: list) -> bool:
        if len(args) < 2:
            self.console.print(
                "[red]Error:[/red] /set requires two arguments: "
                "[cyan]/set <setting> <value>[/cyan]"
            )
            self.console.print("[dim]Example:[/dim] /set language en")
            return False

        setting_name = args[0]
        setting_value: Any = args[1]

        if setting_name not in self.settings:
            self.console.print(
                f"[red]Error:[/red] Unknown setting '[cyan]{setting_name}[/cyan]'"
            )
            self.console.print(
                f"[dim]Available settings:[/dim] {', '.join(self.settings.keys())}"
            )
            return False

        try:
            if setting_name in ["max_length", "num_beams", "num_candidates"]:
                setting_value = int(setting_value)
            elif setting_name == "use_constraints" or setting_name in (
                "check_badness",
                "statistics",
                "raw_output",
            ):
                setting_value = setting_value.lower() in ["true", "1", "yes"]
            elif setting_name == "parser":
                available = list_parsers()
                if setting_value not in available:
                    avail_str = ", ".join(sorted(available)) or "(none)"
                    self.console.print(
                        f"[red]Error:[/red] parser must be one of: {avail_str}"
                    )
                    return False

            self.settings[setting_name] = setting_value
            save_settings(self.settings)
            self.console.print(
                f"[green]✓[/green] Set [cyan]{setting_name}[/cyan] = "
                f"[green]{setting_value}[/green]"
            )

            if setting_name not in ("check_badness", "statistics", "raw_output"):
                new_parser = self._get_or_create_parser()
                if new_parser:
                    self.parser = new_parser
                    self.parser_name = self.settings["parser"]
                else:
                    self.console.print(
                        "[red]Failed to reload parser. Keeping previous parser.[/red]"
                    )

        except ValueError as e:
            self.console.print(
                f"[red]Error:[/red] Invalid value for {setting_name}: {e}"
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

        current_key = self._get_cache_key()

        for cache_key in self.parser_cache:
            parser_name = cache_key[0]
            settings_str = self._format_cache_key_settings(cache_key)
            is_current = "✓" if cache_key == current_key else ""
            table.add_row(parser_name, settings_str, is_current)

        self.console.print()
        self.console.print(
            Panel(table, title="[bold]Cached Parsers[/bold]", border_style="blue")
        )
        self.console.print(
            f"[dim]Total: {len(self.parser_cache)} parser(s) in cache[/dim]\n"
        )
        return False

    def cmd_clear_parsers(self, args: list) -> bool:
        current_key = self._get_cache_key()
        old_count = len(self.parser_cache)
        self.parser_cache = {current_key: self.parser}
        cleared_count = old_count - 1
        self.console.print(
            f"[green]✓[/green] Cleared [cyan]{cleared_count}[/cyan] "
            "parser(s) from cache"
        )
        self.console.print(
            "[dim]Kept current parser: "
            f"{self._format_cache_key_settings(current_key)}[/dim]\n"
        )
        return False

    def _get_cache_key(self) -> tuple:
        parser_name = self.settings["parser"]

        if parser_name == "generative":
            return (
                parser_name,
                self.settings["model_path"],
                self.settings["max_length"],
                self.settings["num_beams"],
                self.settings["num_candidates"],
                self.settings["use_constraints"],
                self.settings["device"],
            )
        elif parser_name == "alphabeta":
            return (parser_name, self.settings["language"])
        else:
            # Generic key for unknown parser plugins
            return (parser_name,)

    def _format_cache_key_settings(self, cache_key: tuple) -> str:
        parser_name = cache_key[0]

        if parser_name == "generative" and len(cache_key) == 7:
            model_path = cache_key[1] or "default"
            max_length = cache_key[2]
            num_beams = cache_key[3]
            num_candidates = cache_key[4]
            use_constraints = cache_key[5]
            device = cache_key[6]
            return (
                f"model={model_path}, max_len={max_length}, beams={num_beams}, "
                f"candidates={num_candidates}, use_constraints={use_constraints}, "
                f"device={device}"
            )
        elif parser_name == "alphabeta" and len(cache_key) == 2:
            language = cache_key[1]
            return f"language={language}"
        else:
            return str(cache_key[1:])

    def _get_or_create_parser(self) -> Parser | None:
        cache_key = self._get_cache_key()

        if cache_key in self.parser_cache:
            self.console.print("[dim]Using cached parser[/dim]")
            return self.parser_cache[cache_key]

        self.console.print("[yellow]Initializing new parser...[/yellow]")
        try:
            kwargs = _parser_kwargs(self.settings)
            new_parser = get_parser(self.settings["parser"], **kwargs)
            self.parser_cache[cache_key] = new_parser
            self.console.print("[green]✓[/green] Parser initialized and cached")
            return new_parser
        except Exception as e:
            self.console.print(f"[red]Error:[/red] Failed to create parser: {e}")
            return None

    def handle_command(self, text: str) -> bool:
        if not text.startswith("/"):
            return False

        parts = text[1:].split()
        if not parts:
            return False

        cmd_name = parts[0]
        cmd_args = parts[1:]

        if cmd_name not in self.commands:
            self.console.print(
                f"[red]Error:[/red] Unknown command '[cyan]/{cmd_name}[/cyan]'"
            )
            self.console.print(
                "[dim]Type[/dim] [bold]/help[/bold] "
                "[dim]to see available commands[/dim]"
            )
            return False

        return self.commands[cmd_name]["handler"](cmd_args)

    def parse_text(self, text: str) -> None:
        try:
            start_time = time.perf_counter()

            parse_result = list(self.parser.parse(text))
            if parse_result and len(parse_result) > 0:
                edge = parse_result[0].edge
                tokens = parse_result[0].tokens
            else:
                edge = None
                tokens = None

            # Print dependency tree for alphabeta parser
            if (
                self.parser_name == "alphabeta"
                and hasattr(self.parser, "doc")
                and self.parser.doc
            ):
                for sent in self.parser.doc.sents:
                    dep_tree = print_dependency_tree(sent.root, self.console)
                    if dep_tree:
                        self.console.print()
                        tree_panel = Panel(
                            dep_tree,
                            title="[bold cyan]Dependency Parse Tree[/bold cyan]",
                            border_style="cyan",
                            box=box.ROUNDED,
                        )
                        self.console.print(tree_panel)

            elapsed_time = time.perf_counter() - start_time

            self.console.print()

            if edge is None:
                result_panel = Panel(
                    Text("FAILED", style="bold red"),
                    title="[yellow]Parse Result[/yellow]",
                    border_style="red",
                    box=box.ROUNDED,
                )
            else:
                formatted_edge = self.formatter.format(edge)
                result_panel = Panel(
                    formatted_edge,
                    title="[yellow]Parse Result[/yellow]",
                    border_style="green",
                    box=box.ROUNDED,
                )

            self.console.print(result_panel)

            # Show raw model output if enabled
            raw_parse = parse_result[0].extra.get("raw_parse") if parse_result else None
            if raw_parse and self.settings.get("raw_output", False):
                self.console.print()
                self.console.print(
                    Panel(
                        Text(raw_parse, style="dim"),
                        title="[bold yellow]Raw Model Output[/bold yellow]",
                        border_style="yellow",
                        box=box.ROUNDED,
                    )
                )

            # Show all candidates when constraints are enabled
            candidates = (
                parse_result[0].extra.get("candidates") if parse_result else None
            )
            if candidates and len(candidates) > 1:
                self.console.print()
                for candidate in candidates:
                    idx = candidate["index"]
                    score = candidate["badness_score"]
                    c_edge = hedge(candidate["edge"])
                    is_selected = edge is not None and str(c_edge) == str(edge)

                    formatted = self.formatter.format(c_edge)
                    score_style = "green" if score == 0 else "red"

                    title = f"Candidate {idx + 1}"
                    if is_selected:
                        title += " [selected]"
                    title += f" (badness: {score})"

                    self.console.print(
                        Panel(
                            formatted,
                            title=f"[bold {score_style}]{title}[/bold {score_style}]",
                            border_style="dim" if not is_selected else score_style,
                            box=box.ROUNDED,
                        )
                    )

                    if score > 0:
                        for error in candidate.get("badness", []):
                            if isinstance(error, (list, tuple)) and len(error) >= 2:
                                self.console.print(
                                    f"  [dim]{error[0]}:[/dim] {error[1]}"
                                )

            # Show statistics if enabled and we have a valid edge
            if (
                edge is not None
                and tokens is not None
                and self.settings.get("statistics", False)
            ):
                self.console.print()
                stats_table = Table(
                    show_header=False,
                    box=box.SIMPLE,
                    padding=(0, 1),
                )
                stats_table.add_column("Stat", style="cyan")
                stats_table.add_column("Value", style="green", justify="right")

                stats_table.add_row("External tokens", str(len(tokens)))

                # Model input width and output length -- generative parser only
                if self.parser_name == "generative":
                    _sentence = re.sub(r"\s+", " ", text.strip())
                    if hasattr(self.parser, "external_tokenizer") and hasattr(
                        self.parser, "tokenizer"
                    ):
                        external_tokens = self.parser.external_tokenizer.tokenize(
                            _sentence
                        )
                        input_text = f"parse to SH: {' '.join(external_tokens)}"
                        source_tokens = self.parser.tokenizer.convert_ids_to_tokens(
                            self.parser.tokenizer.encode(input_text)
                        )
                        stats_table.add_row(
                            "Model input width", str(len(source_tokens))
                        )

                    output_length = parse_result[0].get("output_length")
                    if output_length:
                        stats_table.add_row(
                            "Output sequence length", str(output_length)
                        )

                _edge = hedge(edge)
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

            # Perform badness check if enabled and we have a valid edge
            if (
                edge is not None
                and tokens is not None
                and self.settings.get("check_badness", False)
            ):
                self.console.print()
                _edge = hedge(edge)
                badness_errors = badness_check(_edge, tokens) if _edge else None

                if _edge and not badness_errors:
                    self.console.print(
                        Panel(
                            Text("No errors found", style="green"),
                            title="[bold green]Badness Check[/bold green]",
                            border_style="green",
                            box=box.ROUNDED,
                        )
                    )
                elif _edge:
                    error_table = Table(
                        show_header=True,
                        header_style="bold red",
                        box=box.SIMPLE,
                        padding=(0, 1),
                    )
                    error_table.add_column("Type", style="cyan")
                    error_table.add_column("Message", style="white")

                    if badness_errors:
                        for key, errors in badness_errors.items():
                            context = key
                            if isinstance(errors, list):
                                for error in errors:
                                    if isinstance(error, tuple) and len(error) >= 2:
                                        code, msg = error[0], error[1]
                                        sev = error[2] if len(error) > 2 else "?"
                                        error_table.add_row(
                                            f"{code} [dim](sev:{sev})[/dim]\n[dim]"
                                            f"({context})[/dim]",
                                            msg,
                                        )
                                    else:
                                        error_table.add_row(
                                            f"[dim]({context})[/dim]", str(error)
                                        )

                    self.console.print(
                        Panel(
                            error_table,
                            title="[bold red]Badness Check Failed[/bold red]",
                            border_style="red",
                            box=box.ROUNDED,
                        )
                    )

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
    # Merge: CLI args > saved settings > hardcoded defaults
    saved = load_saved_settings()
    for key in DEFAULTS:
        cli_val = getattr(args, key, None)
        if cli_val is not None:
            continue
        elif key in saved:
            setattr(args, key, saved[key])
        else:
            setattr(args, key, DEFAULTS[key])

    # Initialize parser
    kwargs = _parser_kwargs(
        {
            "parser": args.parser,
            "model_path": args.model_path,
            "language": args.language,
            "device": args.device,
            "max_length": args.max_length,
            "num_beams": args.num_beams,
            "num_candidates": args.num_candidates,
            "use_constraints": args.use_constraints,
        }
    )
    sh_parser = get_parser(args.parser, **kwargs)

    session = ReplSession(sh_parser, args.parser, args)
    session.run()
