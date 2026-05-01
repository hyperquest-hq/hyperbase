import argparse
import sys

from hyperbase.parsers import Parser, list_parsers


def _add_parser_args(
    subparser: argparse.ArgumentParser, parser_cls: type[Parser]
) -> None:
    """Inject *parser_cls*-specific CLI arguments into *subparser*.

    The arguments are derived from ``parser_cls.accepted_params()``: each
    accepted parameter becomes ``--<name>``. Boolean parameters become
    ``store_true`` flags. ``max_depth`` (declared on the base
    :class:`Parser`) is added once globally, not per plugin.
    """
    for name, info in parser_cls.accepted_params().items():
        flag = f"--{name}"
        # Avoid clobbering an arg that's already been added (e.g. when
        # the same name appears on multiple subparsers, or when both base
        # and subclass declare it).
        if any(
            flag in (action.option_strings or [])
            for action in subparser._actions  # type: ignore[attr-defined]
        ):
            continue
        type_: type = info.get("type", str)
        help_str: str = info.get("description", "") or ""
        if type_ is bool:
            subparser.add_argument(
                flag,
                action="store_true",
                default=None,
                help=help_str,
            )
        else:
            subparser.add_argument(
                flag,
                type=type_,
                default=None,
                help=help_str,
            )


def _resolve_parser_name(
    argv: list[str], subcommand: str, default: str | None
) -> str | None:
    """Look ahead in *argv* for ``--parser <name>`` under *subcommand*.

    Returns the parser name to use for dynamically injecting parser-specific
    args, or *default* if not specified. Falls back to the saved REPL
    settings if no value is on the command line and *default* is ``None``.
    """
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--parser", default=None)

    # Strip everything before the subcommand so the pre-parser only
    # sees flags for the right subcommand. ``parse_known_args`` ignores
    # the rest.
    try:
        idx = argv.index(subcommand)
        rest = argv[idx + 1 :]
    except ValueError:
        rest = argv

    pre_args, _ = pre.parse_known_args(rest)
    if pre_args.parser:
        return pre_args.parser
    if default is not None:
        return default

    # Fall back to whatever the REPL last saved.
    try:
        from hyperbase.cli.repl import load_saved_settings

        saved = load_saved_settings()
        if saved.get("parser"):
            return str(saved["parser"])
    except Exception:
        pass
    return None


def _maybe_load_parser_class(name: str | None) -> type[Parser] | None:
    if not name:
        return None
    parsers = list_parsers()
    if name not in parsers:
        return None
    try:
        return parsers[name].load()  # type: ignore[no-any-return]
    except Exception as e:
        print(
            f"Warning: failed to load parser {name!r}: {e}",
            file=sys.stderr,
        )
        return None


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="hyperbase",
        description="Hyperbase CLI",
    )
    subparsers = parser.add_subparsers(dest="command")

    # --- parsers subcommand ------------------------------------------------
    subparsers.add_parser(
        "parsers",
        help="List installed parser plugins",
    )

    # --- read subcommand ---------------------------------------------------
    read_parser = subparsers.add_parser(
        "read",
        help="Read a source, parse it, and write JSONL output",
    )
    read_parser.add_argument(
        "source",
        type=str,
        help="Source to read (file path or URL)",
    )
    read_parser.add_argument(
        "-o",
        "--output",
        type=str,
        required=True,
        help="Output file path (.jsonl for parsed output, .txt for raw text)",
    )
    read_parser.add_argument(
        "--parser",
        type=str,
        default=None,
        help="Parser plugin name (default: generative)",
    )
    read_parser.add_argument(
        "--reader",
        type=str,
        default="auto",
        help="Reader name or 'auto' (default: auto)",
    )
    read_parser.add_argument(
        "--batch_size",
        type=int,
        default=8,
        help="Batch size for parsing (default: 8)",
    )

    # --- repl subcommand ---------------------------------------------------
    repl_parser = subparsers.add_parser(
        "repl",
        help="Interactive REPL for SH parsers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    repl_parser.add_argument(
        "--parser",
        type=str,
        default=None,
        help="Parser plugin name",
    )
    repl_parser.add_argument(
        "--statistics",
        action="store_true",
        default=None,
        help="Show parse statistics after each parse",
    )
    repl_parser.add_argument(
        "--load",
        type=str,
        default=None,
        help="Path to a .jsonl parse-results file to pre-load into memory",
    )

    # Dynamically inject parser-specific args, derived from the active
    # parser's ``accepted_params()``. We do this in two passes so that
    # plugin packages stay the source of truth for their CLI surface.
    argv = sys.argv[1:]
    for sub_name, sub_parser, default_parser in (
        ("read", read_parser, "generative"),
        ("repl", repl_parser, None),
    ):
        active = _resolve_parser_name(argv, sub_name, default_parser)
        cls = _maybe_load_parser_class(active)
        if cls is not None:
            _add_parser_args(sub_parser, cls)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "parsers":
        from hyperbase.cli.parsers import run_parsers

        run_parsers()
        sys.exit(0)

    if args.command == "read":
        from hyperbase.cli.read import run_read

        run_read(args)
        sys.exit(0)

    if args.command == "repl":
        from hyperbase.cli.repl import run_repl

        run_repl(args)
