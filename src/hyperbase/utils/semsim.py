# import logging
# from typing import Any
# from urllib.parse import unquote
#
# from hyperbase import hedge
# from hyperbase.hyperedge import Hyperedge
#
#
# logger: logging.Logger = logging.getLogger(__name__)
#
# # ----- SemSim CTX ----- #
#
# SEMSIM_CTX_TOK_POS_VAR_CODE = "semsim-ctx_tok_pos"
# SEMSIM_CTX_THRESHOLD_VAR_CODE = "semsim-ctx_threshold"
#
#
# def get_semsim_ctx_tok_poses(results: list[dict[str, Any]]) -> dict[int, Hyperedge]:
#     return get_semsim_ctx_var_vals(SEMSIM_CTX_TOK_POS_VAR_CODE, results)
#
#
# def get_semsim_ctx_thresholds(results: list[dict[str, Any]]) -> dict[int, float]:
#     return get_semsim_ctx_var_vals(SEMSIM_CTX_THRESHOLD_VAR_CODE, results)
#
#
# def get_semsim_ctx_var_vals(var_code: str, results: list[dict[str, Any]]) -> dict[int, Any]:
#     var_vals: dict[int, Any] = {}
#     prefix: str = f"__{var_code}_"
#     for results_ in results:
#         for key, value in results_.items():
#             if key.startswith(prefix):
#                 semsim_ctx_idx: int = int(key[len(prefix):])
#                 if var_vals.get(semsim_ctx_idx) is None:
#                     var_vals[semsim_ctx_idx] = value
#                 else:
#                     try:
#                         assert var_vals[semsim_ctx_idx] == value
#                     except AssertionError:
#                         raise ValueError(f"Duplicate semsim-ctx index: {semsim_ctx_idx}")
#     return var_vals
#
#
# # ----- SemSim FIX ----- #
#
# # replace first edge part with pattern word part
# def replace_edge_word_part(edge: Hyperedge, pattern_word_part: str):
#     assert edge.is_atom(), f"Cannot replace edge word part of non-atom: {edge}"
#     return hedge('/'.join([pattern_word_part] + edge.parts()[1:]))  # type: ignore
#
#
# def get_edge_word_part(edge: Hyperedge):  # -> str | None:
#     if edge.not_atom:
#         return None
#
#     edge_word_part: str = edge.parts()[0]  # type: ignore
#
#     # special atoms ('_lemma')
#     if edge_word_part.startswith('_'):
#         return None
#
#     # decode specially encoded characters
#     edge_word_part = unquote(edge_word_part)
#
#     return edge_word_part
#
#
# def extract_pattern_words(pattern_word_part: str):
#     if pattern_word_part.startswith('[') and pattern_word_part.endswith(']'):
#         return [w.strip() for w in pattern_word_part[1:-1].split(',')]
#     return [pattern_word_part]
#
#
# # ----- SemSim general ----- #
#
# # extract similarity threshold if given
# def extract_similarity_threshold(pattern: Hyperedge):  # -> float | None:
#     if not len(pattern) > 1:
#         return None
#
#     try:
#         similarity_threshold = float(pattern[1][0])
#     except ValueError:
#         logger.error(f"Invalid value for similarity threshold: {pattern[1]}")
#         return None
#
#     return similarity_threshold
