import json
import traceback
from abc import ABC
from collections import Counter

import hyperbase.constants as const
from .parser import Parser
from hyperbase.hyperedge import build_atom, hedge, non_unique, unique, UniqueAtom
from hyperbase.utils.concepts import has_common_or_proper_concept


def _resolved_to(edge, resolved_edge):
    if edge == resolved_edge:
        return resolved_edge
    else:
        return hedge((const.resolved_to_connector, edge, resolved_edge))


def _resolution_only(edge):
    if edge is None or edge.atom:
        return edge
    if str(edge[0]) == const.resolved_to_connector:
        return _resolution_only(edge[2])
    else:
        return hedge([_resolution_only(_edge) for _edge in edge])


class Rule:
    def __init__(self, first_type, arg_types, size, connector=None):
        self.first_type = first_type
        self.arg_types = arg_types
        self.size = size
        self.connector = connector
        self._branches = 0


strict_rules = [
    Rule('C', {'C'}, 2, '+/B/.'),
    Rule('M', {'C', 'R', 'M', 'S', 'T', 'P', 'B', 'J'}, 2),
    Rule('B', {'C'}, 3),
    Rule('T', {'C', 'R'}, 2),
    Rule('P', {'C', 'R', 'S'}, 6),
    Rule('P', {'C', 'R', 'S'}, 5),
    Rule('P', {'C', 'R', 'S'}, 4),
    Rule('P', {'C', 'R', 'S'}, 3),
    Rule('P', {'C', 'R', 'S'}, 2),
    Rule('J', {'C', 'R', 'M', 'S', 'T', 'P', 'B', 'J'}, 3)]


repair_rules = [
    Rule('C', {'C'}, 2, '+/B/.'),
    Rule('M', {'C', 'R', 'M', 'S', 'T', 'P', 'B', 'J'}, 2),
    Rule('B', {'C', 'R'}, 3),
    Rule('T', {'C', 'R'}, 2),
    Rule('P', {'C', 'R', 'S'}, 6),
    Rule('P', {'C', 'R', 'S'}, 5),
    Rule('P', {'C', 'R', 'S'}, 4),
    Rule('P', {'C', 'R', 'S'}, 3),
    Rule('P', {'C', 'R', 'S'}, 2),
    Rule('J', {'C', 'R', 'M', 'S', 'T', 'P', 'B', 'J'}, 3),
    Rule('J', {'C', 'R', 'M', 'S', 'T', 'P', 'B', 'J'}, 2)]


def _apply_rule(rule, sentence, pos):
    for pivot_pos in range(rule.size):
        args = []
        pivot = None
        valid = True
        for i in range(rule.size):
            edge = sentence[pos - rule.size + i + 1]
            if i == pivot_pos:
                if edge.mtype() == rule.first_type:
                    if rule.connector:
                        args.append(edge)
                    else:
                        pivot = edge
                else:
                    valid = False
                    break
            else:
                if edge.mtype() in rule.arg_types:
                    args.append(edge)
                else:
                    valid = False
                    break
        if valid:
            if rule.connector:
                return hedge([rule.connector] + args)
            else:
                return hedge([pivot] + args)
    return None


def _is_proper_noun(edge):
    return any(atom.t == 'Cp' for atom in edge.atoms())

def _generate_tok_pos(parse, edge):
    if edge.atom:
        atom = unique(edge)
        if atom in parse['atom2word']:
            return str(parse['atom2word'][atom][1])
        else:
            return '-1'
    else:
        return '({})'.format(' '.join([_generate_tok_pos(parse, subedge) for subedge in edge]))


class AlphaBeta(Parser, ABC):
    def __init__(self, nlp, lemmas=False, corefs=False, beta='repair', normalize=True, post_process=True):
        super().__init__(lemmas=lemmas, corefs=corefs)
        self.nlp = nlp
        self.post_process = post_process
        if beta == 'strict':
            self.rules = strict_rules
        elif beta == 'repair':
            self.rules = repair_rules
        else:
            raise RuntimeError('unkown beta stage: {}'.format(beta))
        self.normalize = normalize

        self.atom2token = None
        self.temp_atoms = None
        self.orig_atom = None
        self.token2atom = None
        self.depths = None
        self.connections = None
        self.edge2text = None
        self.edge2toks = None
        self.toks2edge = None
        self.edge2coref = None
        self.resolved_corefs = None
        self.cur_text = None
        self.extra_edges = set()
        self.doc = None
        self.alpha = None
        self.beta = beta

    # ========================================================================
    # Language-specific abstract methods, to be implemented in derived classes
    # ========================================================================

    def _concept_type_and_subtype(self, token):
        raise NotImplementedError()

    def _modifier_type_and_subtype(self, token):
        raise NotImplementedError()

    def _builder_type_and_subtype(self, token):
        raise NotImplementedError()

    def _predicate_type_and_subtype(self, token):
        raise NotImplementedError()

    def _predicate_post_type_and_subtype(self, edge, subparts, args_string):
        raise NotImplementedError()

    def _relation_arg_role(self, token):
        raise NotImplementedError()

    def _builder_arg_roles(self, edge):
        raise NotImplementedError()

    def _is_noun(self, token):
        raise NotImplementedError()

    def _is_verb(self, token):
        raise NotImplementedError()

    def _verb_features(self, token):
        raise NotImplementedError()

    def _adjust_score(self, edges):
        raise NotImplementedError()

    def _post_process(self, edge):
        return edge

    # =========================
    # Language-agnostic methods
    # =========================

    def parse_spacy_sentence(self, sent, atom_sequence=None, offset=0):
        try:
            self.extra_edges = set()

            if atom_sequence is None:
                atom_sequence = self._build_atom_sequence(sent)

            self._compute_depths_and_connections(sent.root)

            main_edge = None
            result, failed = self._parse_atom_sequence(atom_sequence)
            if result and len(result) == 1:
                main_edge = non_unique(result[0])
                # break

            if main_edge:
                main_edge = self._apply_arg_roles(main_edge)
                if self.beta == 'repair':
                    main_edge = self._repair(main_edge)
                if self.normalize:
                    main_edge = self._normalize(main_edge)
                main_edge = self._apply_temporal_triggers(main_edge)
                if self.post_process:
                    main_edge = self._post_process(main_edge)
                atom2word = self._generate_atom2word(main_edge, offset=offset)
            else:
                atom2word = {}

            # atom2token = {}
            # for atom in self.atom2token:
            #     if atom not in self.temp_atoms:
            #         atom2token[atom] = self.atom2token[atom]
            atom2token = self.atom2token

            return {'main_edge': main_edge,
                    'extra_edges': self.extra_edges,
                    'failed': failed,
                    'text': str(sent).strip(),
                    'atom2word': atom2word,
                    # TODO: HACK TEMPORARY
                    'atom2token': atom2token,
                    'spacy_sentence': sent}
        except Exception as e:
            if hasattr(e, 'message'):
                msg = e.message
            else:
                msg = str(e)
            print('Caught exception: {} while parsing: "{}"'.format(msg, str(sent)))
            traceback.print_exc()
            return {'main_edge': None,
                    'extra_edges': [],
                    'failed': True,
                    'text': str(sent).strip(),
                    'atom2word': {},
                    'spacy_sentence': sent}

    def manual_atom_sequence(self, sentence, token2atom):
        self.token2atom = {}

        atomseq = []
        for token in sentence:
            if token in token2atom:
                atom = token2atom[token]
            else:
                atom = None
            if atom:
                uatom = UniqueAtom(atom)
                self.dep_[uatom] = token
                self.token2atom[token] = uatom
                self.orig_atom[uatom] = uatom
                atomseq.append(uatom)
        return atomseq

    def reset(self, text):
        self.dep_ = {}
        self.temp_atoms = set()
        self.orig_atom = {}
        self.edge2toks = {}
        self.toks2edge = {}
        self.edge2coref = {}
        self.resolved_corefs = set()
        self.cur_text = text

    def _head_token(self, edge):
        atoms = [unique(atom) for atom in edge.all_atoms() if unique(atom) in self.atom2token]
        min_depth = 9999999
        main_atom = None
        for atom in atoms:
            if atom in self.orig_atom:
                oatom = self.orig_atom[atom]
                if oatom in self.depths:
                    depth = self.depths[oatom]
                    if depth < min_depth:
                        min_depth = depth
                        main_atom = atom
        if main_atom:
            return self.atom2token[main_atom]
        else:
            return None

    def _build_atom(self, token, ent_type, last_token):
        text = token.text.lower()
        et = ent_type

        if ent_type[0] == 'P':
            atom = self._build_atom_predicate(token, ent_type, last_token)
        elif ent_type[0] == 'T':
            atom = self._build_atom_trigger(token, ent_type)
        elif ent_type[0] == 'M':
            atom = self._build_atom_modifier(token, ent_type)
        else:
            atom = build_atom(text, et, self.lang)
        return atom

    def _build_atom_predicate(self, token, ent_type, last_token):
        text = token.text.lower()
        et = ent_type

        # create verb features string
        verb_features = self._verb_features(token)

        # first naive assignment of predicate subtype
        # (can be revised at post-processing stage)
        if ent_type == 'Pd':
            # interrogative cases
            if (last_token and
                    last_token.tag_ == '.' and
                    last_token.dep_ == 'punct' and
                    last_token.lemma_.strip() == '?'):
                ent_type = 'P?'
            # declarative (by default)
            else:
                ent_type = 'Pd'

        et = '{}..{}'.format(ent_type, verb_features)

        return build_atom(text, et, self.lang)

    def _build_atom_trigger(self, token, ent_type):
        text = token.text.lower()
        et = ent_type

        if self._is_verb(token):
            # create verb features string
            verb_features = self._verb_features(token)
            et = 'Tv.{}'.format(verb_features)

        return build_atom(text, et, self.lang)

    def _build_atom_modifier(self, token, ent_type):
        text = token.text.lower()

        if self._is_verb(token):
            # create verb features string
            verb_features = self._verb_features(token)
            et = 'Mv.{}'.format(verb_features)  # verbal subtype
        else:
            et = self._modifier_type_and_subtype(token)

        return build_atom(text, et, self.lang)

    def _repair(self, edge):
        if edge.not_atom:
            edge = hedge([self._repair(subedge) for subedge in edge])

            if edge.connector_mtype() == 'B':
                if 'R' in set(subedge.mtype() for subedge in edge[1:]):
                    builder_atom = edge.connector_atom()
                    builder_parts = builder_atom.parts()
                    newparts = (builder_parts[0], 'J' + builder_parts[1][1:])
                    if len(builder_parts) > 2:
                        newparts += tuple(builder_parts[2:])
                    new_builder = hedge('/'.join(newparts))
                    utrigger_atom = UniqueAtom(builder_atom)
                    unew_trigger = UniqueAtom(new_builder)
                    if utrigger_atom in self.atom2token:
                        self.atom2token[unew_trigger] = self.atom2token[utrigger_atom]
                    self.orig_atom[unew_trigger] = utrigger_atom
                    edge = edge.replace_atom(builder_atom, new_builder, unique=True)
            elif edge.connector_mtype() == 'J':
                if len(edge) == 2:
                    builder_atom = edge.connector_atom()
                    builder_parts = builder_atom.parts()
                    newparts = (builder_parts[0], 'Mj')
                    if len(builder_parts) > 2:
                        newparts += tuple(builder_parts[2:])
                    new_builder = hedge('/'.join(newparts))
                    ubuilder_atom = UniqueAtom(builder_atom)
                    unew_builder = UniqueAtom(new_builder)
                    if ubuilder_atom in self.atom2token:
                        self.atom2token[unew_builder] = self.atom2token[ubuilder_atom]
                    self.orig_atom[unew_builder] = ubuilder_atom
                    edge = edge.replace_atom(builder_atom, new_builder, unique=True)

        return edge

    def _normalize(self, edge):
        if edge.not_atom:
            edge = hedge([self._normalize(subedge) for subedge in edge])

            # Move modifier to internal connector if it is applied to
            # relations, specifiers or conjunctions
            if edge.connector_mtype() == 'M' and not edge[1].atom:
                innner_conn = edge[1].connector_mtype()
                if innner_conn in {'P', 'T', 'J'}:
                    return hedge(((edge[0], edge[1][0]),) + edge[1][1:])

        return edge

    def _is_temporal(self, edge):
        if edge.atom:
            token = self.atom2token.get(UniqueAtom(edge))
            if token:
                ent_type = self.atom2token[UniqueAtom(edge)].ent_type_
                if ent_type in {'DATE', 'TIME'}:
                    return True
            return False
        else:
            for subedge in edge:
                if self._is_temporal(subedge):
                    return True
            return False


    def _update_atom(self, old, new):
        uold = UniqueAtom(old)
        unew = UniqueAtom(new)
        if uold in self.atom2token:
            self.atom2token[unew] = self.atom2token[uold]
            self.temp_atoms.add(uold)
        self.orig_atom[unew] = uold

    def _replace_atom(self, edge, old, new):
        self._update_atom(old, new)
        return edge.replace_atom(old, new)

    def _insert_edge_with_argrole(self, edge, arg, argrole, pos):
        new_edge = edge.insert_edge_with_argrole(arg, argrole, pos)
        old_pred = edge[0].inner_atom()
        new_pred = new_edge[0].inner_atom()
        self._update_atom(old_pred, new_pred)
        return new_edge

    def _replace_argroles(self, edge, argroles):
        new_edge = edge.replace_argroles(argroles)
        old_pred = edge[0].inner_atom()
        new_pred = new_edge[0].inner_atom()
        self._update_atom(old_pred, new_pred)
        return new_edge

    def _apply_temporal_triggers(self, edge):
        if edge.not_atom:
            edge = hedge([self._apply_temporal_triggers(subedge) for subedge in edge])

            if edge.connector_mtype() == 'T':
                # Make triggers temporal, if appropriate.
                # e.g.: (in/T 1976) -> (in/Tt 1976)
                if self._is_temporal(edge):
                    trigger_atom = edge[0].atom_with_type('T')
                    triparts = trigger_atom.parts()
                    newparts = (triparts[0], 'Tt')
                    if len(triparts) > 2:
                        newparts += tuple(triparts[2:])
                    new_trigger = hedge('/'.join(newparts))
                    edge = self._replace_atom(edge, trigger_atom, new_trigger)

        return edge

    def _add_lemmas(self, token, entity, ent_type):
        text = token.lemma_.lower()
        lemma = build_atom(text, ent_type[0], self.lang)
        lemma_edge = hedge((const.lemma_connector, entity.simplify(), lemma))
        self.extra_edges.add(lemma_edge)

    def _apply_arg_roles(self, edge):
        if edge.atom:
            return edge

        new_entity = edge

        # Extend predicate connectors with argument types
        if edge.connector_mtype() == 'P':
            pred = edge.atom_with_type('P')
            subparts = pred.parts()[1].split('.')
            args = [self._relation_arg_role(param) for param in edge[1:]]
            args_string = ''.join(args)
            # TODO: this is done to detect imperative, to refactor
            pt = self._predicate_post_type_and_subtype(edge, subparts, args_string)
            if len(subparts) > 2:
                new_part = '{}.{}.{}'.format(pt, args_string, subparts[2])
            else:
                new_part = '{}.{}'.format(pt, args_string)
            new_pred = pred.replace_atom_part(1, new_part)
            unew_pred = UniqueAtom(new_pred)
            upred = UniqueAtom(pred)
            self.atom2token[unew_pred] = self.atom2token[upred]
            self.temp_atoms.add(upred)
            self.orig_atom[unew_pred] = upred
            new_entity = edge.replace_atom(pred, new_pred, unique=True)

        # Extend builder connectors with argument types
        elif edge.connector_mtype() == 'B':
            builder = edge.atom_with_type('B')
            subparts = builder.parts()[1].split('.')
            arg_roles = self._builder_arg_roles(edge)
            if len(arg_roles) > 0:
                if len(subparts) > 1:
                    subparts[1] = arg_roles
                else:
                    subparts.append(arg_roles)
                new_part = '.'.join(subparts)
                new_builder = builder.replace_atom_part(1, new_part)
                ubuilder = UniqueAtom(builder)
                unew_builder = UniqueAtom(new_builder)
                if ubuilder in self.atom2token:
                    self.atom2token[unew_builder] = self.atom2token[ubuilder]
                    self.temp_atoms.add(ubuilder)
                self.orig_atom[unew_builder] = ubuilder
                new_entity = edge.replace_atom(builder, new_builder, unique=True)

        new_args = [self._apply_arg_roles(subentity) for subentity in new_entity[1:]]
        new_entity = hedge([new_entity[0]] + new_args)

        return new_entity

    def _generate_atom2word(self, edge, offset=0):
        atom2word = {}
        atoms = edge.all_atoms()
        for atom in atoms:
            uatom = UniqueAtom(atom)
            if uatom in self.atom2token:
                token = self.atom2token[uatom]
                word = (token.text, token.i - offset)
                atom2word[uatom] = word
        return atom2word

    def _parse_token(self, token, atom_type):
        if atom_type == 'X':
            return None
        elif atom_type == 'C':
            atom_type = self._concept_type_and_subtype(token)
        elif atom_type == 'M':
            atom_type = self._modifier_type_and_subtype(token)
        elif atom_type == 'B':
            atom_type = self._builder_type_and_subtype(token)
        elif atom_type == 'P':
            atom_type = self._predicate_type_and_subtype(token)

        # last token is useful to determine predicate subtype
        tokens = list(token.lefts) + list(token.rights)
        last_token = tokens[-1] if len(tokens) > 0 else None

        atom = self._build_atom(token, atom_type, last_token)
        self.debug_msg('ATOM: {}'.format(atom))

        # lemmas
        if self.lemmas:
            self._add_lemmas(token, atom, atom_type)

        return atom

    def _build_atom_sequence(self, sentence):
        features = []
        for pos, token in enumerate(sentence):
            head = token.head
            tag = token.tag_
            dep = token.dep_
            hpos = head.pos_ if head else ''
            hdep = head.dep_ if head else ''
            if pos + 1 < len(sentence):
                pos_after = sentence[pos + 1].pos_
            else:
                pos_after = ''
            features.append((tag, dep, hpos, hdep, pos_after))
        atom_types = self.alpha.predict(features)

        self.token2atom = {}

        atomseq = []
        for token, atom_type in zip(sentence, atom_types):
            atom = self._parse_token(token, atom_type)
            if atom:
                uatom = UniqueAtom(atom)
                self.atom2token[uatom] = token
                self.token2atom[token] = uatom
                self.orig_atom[uatom] = uatom
                atomseq.append(uatom)
        return atomseq

    def _compute_depths_and_connections(self, root, depth=0):
        if depth == 0:
            self.depths = {}
            self.connections = set()

        if root in self.token2atom:
            parent_atom = self.token2atom[root]
            self.depths[parent_atom] = depth
        else:
            parent_atom = None

        for child in root.children:
            if parent_atom and child in self.token2atom:
                child_atom = self.token2atom[child]
                self.connections.add((parent_atom, child_atom))
                self.connections.add((child_atom, parent_atom))
            self._compute_depths_and_connections(child, depth + 1)

    def _is_pair_connected(self, atoms1, atoms2):
        for atom1 in atoms1:
            for atom2 in atoms2:
                if atom1 in self.orig_atom and atom2 in self.orig_atom:
                    pair = (self.orig_atom[atom1], self.orig_atom[atom2])
                    if pair in self.connections:
                        return True
        return False

    def _are_connected(self, atom_sets, connector_pos):
        conn = True
        for pos, arg in enumerate(atom_sets):
            if pos != connector_pos:
                if not self._is_pair_connected(atom_sets[connector_pos], arg):
                    conn = False
                    break
        return conn

    def _score(self, edges):
        atom_sets = [edge.all_atoms() for edge in edges]

        conn = False
        for pos in range(len(edges)):
            if self._are_connected(atom_sets, pos):
                conn = True
                break

        mdepth = 99999999
        for atom_set in atom_sets:
            for atom in atom_set:
                if atom in self.orig_atom:
                    oatom = self.orig_atom[atom]
                    if oatom in self.depths:
                        depth = self.depths[oatom]
                        if depth < mdepth:
                            mdepth = depth

        return (10000000 if conn else 0) + (mdepth * 100) + self._adjust_score(edges)

    def _parse_atom_sequence(self, atom_sequence):
        sequence = atom_sequence
        while True:
            action = None
            best_score = -999999999
            for rule_number, rule in enumerate(self.rules):
                window_start = rule.size - 1
                for pos in range(window_start, len(sequence)):
                    new_edge = _apply_rule(rule, sequence, pos)
                    if new_edge:
                        score = self._score(sequence[pos - window_start:pos + 1])
                        score -= rule_number
                        if score > best_score:
                            action = (rule, score, new_edge, window_start, pos)
                            best_score = score

            # parse failed, make best effort to return something
            if action is None:
                # if all else fails...
                if len(sequence) > 0:
                    new_sequence = [hedge([':/J/.'] + sequence[:2])]
                    new_sequence += sequence[2:]
                else:
                    return None, True
            else:
                rule, s, new_edge, window_start, pos = action
                new_sequence = (sequence[:pos - window_start] + [new_edge] + sequence[pos + 1:])

                self.debug_msg('rule: {}'.format(rule))
                self.debug_msg('score: {}'.format(score))
                self.debug_msg('new_edge: {}'.format(new_edge))
                self.debug_msg('new_sequence: {}'.format(new_sequence))

            sequence = new_sequence
            if len(sequence) < 2:
                return sequence, False

    def _parse(self, text):
        """Transforms the given text into hyperedges + aditional information.
        Returns a sequence of dictionaries, with one dictionary for each
        sentence found in the text.

        Each dictionary contains the following fields:

        -> main_edge: the hyperedge corresponding to the sentence.

        -> extra_edges: aditional edges, e.g. connecting atoms that appear
        in the main_edge to their lemmas.

        -> text: the string of natural language text corresponding to the
        main_edge, i.e.: the sentence itself.

        -> atom2word: TODO

        -> spacy_sentence: the spaCy structure representing the sentence
        enriched with NLP annotations.
        """
        self.reset(text)
        parses = []
        try:
            self.doc = self.nlp(text.strip())
            offset = 0
            for sent in self.doc.sents:
                parses.append(self.parse_spacy_sentence(sent, offset=offset))
                offset += len(sent)
        except RuntimeError as error:
            print(error)
        return {'parses': parses, 'inferred_edges': []}

    def sentences(self, text):
        doc = self.nlp(text.strip())
        return [str(sent).strip() for sent in doc.sents]

    def _coref_inferences(self, main_edge, edges):
        results = set()

        gender_cnt = Counter()
        number_cnt = Counter()
        animacy_cnt = Counter()
        for edge in edges:
            if edge.atom:
                gender = self.atom_gender(edge)
                if gender is not None:
                    gender_cnt[gender] += 1
                number = self.atom_number(edge)
                if number is not None:
                    number_cnt[number] += 1
                animacy = self.atom_animacy(edge)
                if animacy is not None:
                    animacy_cnt[animacy] += 1
            if edge != main_edge and has_common_or_proper_concept(edge):
                is_edge = hedge((const.is_connector, main_edge, edge))
                results.add(is_edge)

        gender_top = gender_cnt.most_common(2)
        if len(gender_top) == 1 or (len(gender_top) == 2 and gender_top[0][1] > gender_top[1][1]):
            gender = gender_top[0][0]
            gender_edge = hedge((const.gender_connector, main_edge, gender))
            results.add(gender_edge)
        number_top = number_cnt.most_common(2)
        if len(number_top) == 1 or (len(number_top) == 2 and number_top[0][1] > number_top[1][1]):
            number = number_top[0][0]
            number_edge = hedge((const.number_connector, main_edge, number))
            results.add(number_edge)
        animacy_top = animacy_cnt.most_common(2)
        if len(animacy_top) == 1 or (len(animacy_top) == 2 and animacy_top[0][1] > animacy_top[1][1]):
            animacy = animacy_top[0][0]
            animacy_edge = hedge((const.animacy_connector, main_edge, animacy))
            results.add(animacy_edge)

        # proper noun corefs
        if _is_proper_noun(main_edge):
            for edge in edges:
                if edge != main_edge and  _is_proper_noun(edge):
                    coref_edge = hedge((const.parser_coref_connector, main_edge, edge))
                    results.add(coref_edge)

        return results

    def _resolve_corefs_edge(self, edge):
        if edge is None:
            return None
        if edge.atom:
            return edge
        else:
            if str(edge[0]) == const.resolved_to_connector:
                _edge = self._resolve_corefs_edge(edge[2])
                if str(_edge[0]) == const.resolved_to_connector:
                    _edge = edge[2]
                return hedge((edge[0], edge[1], _edge))
            # e.g. "ihr Hund", "son chien", "her dog", ...
            # (her/Mp dog/Cc) -> (poss/Bp.am/. mary/Cp dog/Cc)
            elif (edge.ct == 'Mp' and
                  len(edge) == 2 and
                  edge[0] in self.edge2coref and
                  self.edge2coref[edge[0]].mt == 'C' and
                  self.edge2coref[edge[0]].t != 'Ci' and
                  (self.edge2coref[edge[0]].atom or self.edge2coref[edge[0]][0].t != 'Mp')):
                return _resolved_to(edge, hedge((const.possessive_builder, self.edge2coref[edge[0]], edge[1])))
            elif edge in self.resolved_corefs:
                return edge
            elif edge in self.edge2coref and edge.mt == self.edge2coref[edge].mt:
                return _resolved_to(edge, self.edge2coref[edge])
            else:
                return hedge([self._resolve_corefs_edge(subedge) for subedge in edge])

    def _edge2toks(self, edge):
        uatoms = [unique(atom) for atom in edge.all_atoms()]
        toks = tuple(sorted([self.atom2token[uatom] for uatom in uatoms if uatom in self.atom2token]))
        self.edge2toks[edge] = toks
        self.toks2edge[toks] = edge
        if edge.not_atom:
            for subedge in edge:
                self._edge2toks(subedge)

    def _set_edge_tokens(self, edge, hg, parse):
        hg.set_attribute(edge, 'tokens', json.dumps([str(token) for token in parse['spacy_sentence']]))
        hg.set_attribute(edge, 'tok_pos', _generate_tok_pos(parse, edge))

    def _resolve_corefs(self, parse_results):
        for parse in parse_results['parses']:
            if parse['main_edge'] is not None:
                self._edge2toks(parse['main_edge'])

        coref_clusters = []
        i = 1
        while True:
            key = 'coref_clusters_{}'.format(i)
            if key in self.doc.spans:
                coref_clusters.append(self.doc.spans[key])
                i += 1
            else:
                break

        toks2resolved = {}
        clusters = {}
        for cluster in coref_clusters:
            mtoks = tuple(sorted(list(cluster[0])))
            if mtoks in self.toks2edge:
                redge = self.toks2edge[mtoks]
                clusters[redge] = []
                for span in cluster:
                    stoks = tuple(sorted(list(span)))
                    toks2resolved[stoks] = redge
                    if stoks in self.toks2edge:
                        clusters[redge].append(self.toks2edge[stoks])

        for edge, toks in self.edge2toks.items():
            if toks in toks2resolved:
                redge = toks2resolved[toks]
                if edge != redge:
                    self.edge2coref[edge] = redge
                    self.resolved_corefs.add(redge)

        for parse in parse_results['parses']:
            resolved_edge = parse['main_edge']
            while True:
                new_edge = self._resolve_corefs_edge(resolved_edge)
                if new_edge == resolved_edge:
                    break
                else:
                    resolved_edge = new_edge
            parse['resolved_to'] = resolved_edge
            parse['resolved_corefs'] = _resolution_only(resolved_edge)

        inferred_edges = set()
        for main_edge, edges in clusters.items():
            inferred_edges |= self._coref_inferences(main_edge, edges)
        parse_results['inferred_edges'] = list(inferred_edges)
