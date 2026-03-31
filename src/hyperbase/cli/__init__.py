import argparse
import sys


def main():
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
        help="Parser plugin name (e.g. generative, alphabeta)",
    )
    repl_parser.add_argument(
        "--model_path",
        type=str,
        default=None,
        help="Path to trained model (generative parser)",
    )
    repl_parser.add_argument(
        "--language",
        type=str,
        default=None,
        help="Language for alphabeta parser (de, en, es, fr, pt, etc.)",
    )
    repl_parser.add_argument(
        "--max_length",
        type=int,
        default=None,
        help="Maximum sequence length (generative parser)",
    )
    repl_parser.add_argument(
        "--num_beams",
        type=int,
        default=None,
        help="Number of beams for beam search (generative parser)",
    )
    repl_parser.add_argument(
        "--num_candidates",
        type=int,
        default=None,
        help="Number of candidates for beam search (generative parser)",
    )
    repl_parser.add_argument(
        "--use_constraints",
        action="store_true",
        default=None,
        help="Enable post-generation SH constraint validation (generative parser)",
    )
    repl_parser.add_argument(
        "--check_badness",
        action="store_true",
        default=None,
        help="Enable badness check after parsing",
    )
    repl_parser.add_argument(
        "--statistics",
        action="store_true",
        default=None,
        help="Show parse statistics",
    )
    repl_parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="Device to use (cuda/cpu/mps)",
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "parsers":
        from hyperbase.cli.parsers import run_parsers
        run_parsers()
        sys.exit(0)

    if args.command == "repl":
        from hyperbase.cli.repl import run_repl
        run_repl(args)
