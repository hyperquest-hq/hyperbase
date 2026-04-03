import argparse
import os
import sys

from hyperbase.parsers import get_parser
from hyperbase.readers import get_reader


def run_read(args: argparse.Namespace):
    ext = os.path.splitext(args.output)[1].lower()

    if ext == '.txt':
        try:
            reader = get_reader(args.source, reader=args.reader)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        print(f"Reader: {type(reader).__name__}", file=sys.stderr)
        reader.read_to_text(args.source, args.output, progress=True)
        print(f"\nOutput: {args.output}", file=sys.stderr)
        return

    if ext != '.jsonl':
        print(f"Error: unsupported output extension {ext!r}"
              " (use .jsonl or .txt)", file=sys.stderr)
        sys.exit(1)

    # Build parser kwargs
    kwargs = {}
    if args.parser == 'generative':
        if args.model_path:
            kwargs['model_path'] = args.model_path
        if args.device:
            kwargs['device'] = args.device
    elif args.parser == 'alphabeta':
        if args.language:
            kwargs['lang'] = args.language

    try:
        parser = get_parser(args.parser, **kwargs)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Parser: {args.parser}", file=sys.stderr)

    sentences = 0
    edges = 0
    errors = 0

    with open(args.output, 'w') as f:
        for results in parser.read_source(
            args.source, reader=args.reader,
            batch_size=args.batch_size, progress=True,
        ):
            for result in results:
                sentences += 1
                if result.failed:
                    errors += 1
                else:
                    edges += 1
                f.write(result.to_json() + '\n')

    print(f"\nSentences: {sentences}", file=sys.stderr)
    print(f"Edges:     {edges}", file=sys.stderr)
    print(f"Errors:    {errors}", file=sys.stderr)
    print(f"Output:    {args.output}", file=sys.stderr)
