from hyperbase.parsers import create_parser, print_tree


if __name__ == '__main__':
    text = """
    Satellites from NASA and other agencies have been tracking sea ice changes
    since 1979.
    """

    parser = create_parser(lang='en', lemmas=True)
    parse_results = parser.parse(text)

    for parse in parse_results['parses']:
        print_tree(parse['spacy_sentence'].root)
        print(parse['main_edge'])
        print('>> Extra edges:')
        for edge in parse['extra_edges']:
            print(edge)
