from __future__ import annotations

from typing import Any

from hyperbase.constants import EdgeType
from hyperbase.hyperedge import Hyperedge
from hyperbase.parsers.utils import filter_alphanumeric_strings


def check_structural_quality(
    edge: Hyperedge,
) -> dict[Hyperedge, list[tuple[str, str, int]]]:
    errors: dict[Hyperedge, list[tuple[str, str, int]]] = {}

    def _visit(current_edge: Hyperedge) -> None:
        if not current_edge or current_edge.atom:
            return

        current_errors: list[tuple[str, str, int]] = []

        # Argrole checks
        try:
            ars = current_edge.argroles()
            for ar in ars:
                if ar not in "mspaoixtjrc":
                    current_errors.append(
                        (
                            "bad-argrole",
                            f"Bad argument role '{ar}'. "
                            "Should be one of 'mspaoixtjrc'.",
                            2,
                        )
                    )

        except Exception:
            pass

        # Junction checks
        try:
            if current_edge[0].mt == EdgeType.CONJUNCTION:
                types = {child.mt for child in current_edge[1:]}
                if (
                    types != {EdgeType.RELATION}
                    and types != {EdgeType.CONCEPT}
                    and types != {EdgeType.RELATION, EdgeType.SPECIFIER}
                ):
                    current_errors.append(
                        (
                            "bad-junction-types",
                            "Junction arguments should ideally be all of type"
                            " 'R[S]' or all of type 'C'.",
                            3,
                        )
                    )
        except Exception:
            pass

        if current_errors:
            errors[current_edge] = current_errors

        for child in current_edge:
            _visit(child)

    if edge:
        _visit(edge)
    return errors


def badness_check(
    edge: Hyperedge, tokens: list[str]
) -> dict[Any, list[tuple[str, str, int]]]:
    raw_errors = edge.check_correctness()
    errors: dict[Any, list[tuple[str, str, int]]] = {}
    for k, v in raw_errors.items():
        errors[k] = [(err_type, err_msg, 0) for err_type, err_msg in v]

    structural_errors = check_structural_quality(edge)
    for k, v2 in structural_errors.items():
        if k in errors:
            errors[k].extend(v2)
        else:
            errors[k] = v2

    # Only check token matching if we have a valid edge
    if edge:
        try:
            tokens = filter_alphanumeric_strings(tokens)
            roots = filter_alphanumeric_strings(
                [atom.label() for atom in edge.all_atoms()]
            )

            # Track which tokens and roots have been matched
            matched_tokens: set[int] = set()
            matched_roots: set[int] = set()

            # Count remaining unmatched instances of each root
            def count_unmatched_roots(root_value: str) -> int:
                count = 0
                for root_idx, root in enumerate(roots):
                    if root == root_value and root_idx not in matched_roots:
                        count += 1
                return count

            # Go through each token and try to find matching roots
            for token_idx, token in enumerate(tokens):
                if token_idx in matched_tokens:
                    continue  # Already matched this token

                # Try exact match first
                unmatched_root_count = count_unmatched_roots(token)
                if unmatched_root_count > 0:
                    matched_tokens.add(token_idx)
                    # Find an unmatched instance of this root
                    for root_idx, root in enumerate(roots):
                        if root == token and root_idx not in matched_roots:
                            matched_roots.add(root_idx)
                            break

                else:
                    # Try to find a root that matches this token exactly
                    for root_idx, root in enumerate(roots):
                        if root_idx in matched_roots:
                            continue  # Already matched this root

                        if root == token:
                            matched_tokens.add(token_idx)
                            matched_roots.add(root_idx)
                            break

                    # If no exact match, try to find combination of roots that
                    # form this token
                    if token_idx not in matched_tokens:
                        # Look for sequence of consecutive roots that concatenate to
                        # form the token
                        for root_start_idx in range(len(roots)):
                            if root_start_idx in matched_roots:
                                continue  # This root is already matched

                            concatenated = ""
                            root_sequence: list[int] = []

                            for root_idx in range(root_start_idx, len(roots)):
                                if root_idx in matched_roots:
                                    # Can't use matched roots in sequence
                                    break

                                root = roots[root_idx]
                                concatenated += root
                                root_sequence.append(root_idx)

                                if concatenated == token:
                                    # Found a matching sequence
                                    matched_tokens.add(token_idx)
                                    for idx in root_sequence:
                                        matched_roots.add(idx)
                                    break

                                if len(concatenated) >= len(token):
                                    # Gone too far or exact match found
                                    break

                            if token_idx in matched_tokens:
                                break  # Found a match

                    # If still no match, try:
                    # root that matches this token and subsequent tokens
                    if token_idx not in matched_tokens:
                        # Look for a root that can match this token
                        # plus some following tokens
                        for root_idx, root in enumerate(roots):
                            if root_idx in matched_roots:
                                continue  # Already matched

                            concatenated = ""
                            token_sequence: list[int] = []

                            for next_token_idx in range(token_idx, len(tokens)):
                                if next_token_idx in matched_tokens:
                                    continue  # Already matched

                                concatenated += tokens[next_token_idx]
                                token_sequence.append(next_token_idx)

                                if concatenated == root:
                                    # Found a root that matches multiple tokens
                                    matched_roots.add(root_idx)
                                    for idx in token_sequence:
                                        matched_tokens.add(idx)
                                    break

                                if len(concatenated) >= len(root):
                                    break

                    # If still no match, try case:
                    # multi-token to multi-root concatenation matching
                    if token_idx not in matched_tokens:
                        # First, try positional matching (existing logic)
                        for root_start_idx in range(len(roots)):
                            if root_start_idx in matched_roots:
                                continue  # This root is already matched

                            tokens_concatenated = ""
                            roots_concatenated = ""
                            token_sequence = []
                            root_sequence = []

                            max_tokens = min(
                                len(tokens) - token_idx, len(roots) - root_start_idx
                            )

                            for i in range(max_tokens):
                                current_token_idx = token_idx + i
                                current_root_idx = root_start_idx + i

                                if (
                                    current_token_idx in matched_tokens
                                    or current_root_idx in matched_roots
                                ):
                                    break  # Can't use already matched items

                                tokens_concatenated += tokens[current_token_idx]
                                roots_concatenated += roots[current_root_idx]
                                token_sequence.append(current_token_idx)
                                root_sequence.append(current_root_idx)

                                # Check if concatenations match
                                if (
                                    tokens_concatenated == roots_concatenated
                                    and tokens_concatenated
                                ):
                                    # Found a match - mark all as matched
                                    for idx in token_sequence:
                                        matched_tokens.add(idx)
                                    for idx in root_sequence:
                                        matched_roots.add(idx)
                                    break

                                # Stop if we've gone too far
                                # (tokens longer than reasonable)
                                if (
                                    len(tokens_concatenated) > 10
                                    or len(roots_concatenated) > 10
                                ):
                                    break

                            if token_idx in matched_tokens:
                                break  # Found a match

                        # If still no match, try non-positional contraction matching
                        # Look for contractions by trying to combine this token
                        # with the next one and matching against any two available
                        # roots in the roots list (not necessarily consecutive)
                        if (
                            token_idx not in matched_tokens
                            and token_idx + 1 < len(tokens)
                            and token_idx + 1 not in matched_tokens
                        ):
                            token_concat = tokens[token_idx] + tokens[token_idx + 1]

                            # Try to find any two available roots (not necessarily
                            # consecutive) that concatenate to the same value
                            for root_idx1 in range(len(roots)):
                                if root_idx1 in matched_roots:
                                    continue  # Can't use already matched roots

                                for root_idx2 in range(len(roots)):
                                    if (
                                        root_idx2 in matched_roots
                                        or root_idx2 == root_idx1
                                    ):
                                        continue  # Can't use already matched roots
                                        # or same root

                                    root_concat = roots[root_idx1] + roots[root_idx2]

                                    if token_concat == root_concat:
                                        # Found a contraction match
                                        matched_tokens.add(token_idx)
                                        matched_tokens.add(token_idx + 1)
                                        matched_roots.add(root_idx1)
                                        matched_roots.add(root_idx2)
                                        break

                                if token_idx in matched_tokens:
                                    break  # Found a match

            token_matching_errors: list[tuple[str, str, int]] = []
            # Report unmatched roots
            for root_idx, root in enumerate(roots):
                if root_idx not in matched_roots:
                    token_matching_errors.append(
                        (
                            "root-without-token",
                            f"Atom root '{root}' is used more times "
                            "than it appears in the original text.",
                            1,
                        )
                    )

            # Report unmatched tokens
            for token_idx, token in enumerate(tokens):
                if token_idx not in matched_tokens:
                    token_matching_errors.append(
                        (
                            "token-unused",
                            f"Atom root '{token}' is not used, "
                            "but it appears in the original text.",
                            1,
                        )
                    )

            if len(token_matching_errors) > 0:
                errors["token-matching"] = token_matching_errors

        except (AttributeError, Exception):
            # If token counting fails (e.g., edge is invalid), skip it
            pass

    return errors
