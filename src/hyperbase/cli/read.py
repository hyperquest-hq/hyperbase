import argparse
import os
import sys

from hyperbase.parsers import get_parser, list_parsers
from hyperbase.readers import get_reader

DEFAULT_PARSER = "generative"


def run_read(args: argparse.Namespace) -> None:
    ext = os.path.splitext(args.output)[1].lower()

    if ext == ".txt":
        try:
            reader = get_reader(args.source, reader=args.reader)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        print(f"Reader: {type(reader).__name__}", file=sys.stderr)
        reader.read_to_text(args.source, args.output, progress=True)
        print(f"\nOutput: {args.output}", file=sys.stderr)
        return

    if ext != ".jsonl":
        print(
            f"Error: unsupported output extension {ext!r} (use .jsonl or .txt)",
            file=sys.stderr,
        )
        sys.exit(1)

    parser_name: str = getattr(args, "parser", None) or DEFAULT_PARSER

    parsers = list_parsers()
    if parser_name not in parsers:
        avail = ", ".join(sorted(parsers)) or "(none)"
        print(
            f"Error: parser {parser_name!r} is not installed. Available: {avail}",
            file=sys.stderr,
        )
        sys.exit(1)
    parser_cls = parsers[parser_name].load()

    # Build kwargs from the parser's own ``accepted_params``: every
    # parser-specific CLI flag was injected by ``hyperbase.cli`` based on
    # the same dict, so this is just the inverse mapping.
    kwargs: dict[str, object] = {}
    for name in parser_cls.accepted_params():
        value = getattr(args, name, None)
        if value is not None:
            kwargs[name] = value

    try:
        parser = get_parser(parser_name, **kwargs)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Parser: {parser_name}", file=sys.stderr)

    sentences = 0
    edges = 0
    errors = 0

    with open(args.output, "w") as f:
        for results in parser.parse_source(
            args.source,
            reader=args.reader,
            batch_size=args.batch_size,
            progress=True,
        ):
            for result in results:
                sentences += 1
                if result.failed:
                    errors += 1
                else:
                    edges += 1
                f.write(result.to_json() + "\n")

    print(f"\nSentences: {sentences}", file=sys.stderr)
    print(f"Edges:     {edges}", file=sys.stderr)
    print(f"Errors:    {errors}", file=sys.stderr)
    print(f"Output:    {args.output}", file=sys.stderr)
