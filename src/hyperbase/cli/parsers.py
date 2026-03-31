from hyperbase.parsers import list_parsers


def run_parsers():
    parsers = list_parsers()
    if parsers:
        for name in sorted(parsers):
            ep = parsers[name]
            print(f"  {name:20s} {ep.value}")
    else:
        print("No parser plugins installed.")
