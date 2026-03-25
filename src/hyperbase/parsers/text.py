import re

from hyperbase.hyperedge import UniqueAtom


def edge_text(atom2word, edge):
    atoms = edge.all_atoms()
    words = list(atom2word[UniqueAtom(atom)]
                 for atom in atoms
                 if UniqueAtom(atom) in atom2word)
    words.sort(key=lambda word: word[1])
    text = ' '.join([word[0] for word in words])
    # remove spaces arounf non alpha-numeric characters
    # e.g.: "passive-aggressive" instead of "passive - aggressive"
    text = re.sub(' ([^a-zA-Z\\d\\s]) ', '\\g<1>', text)
    return text
