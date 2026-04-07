from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, cast

from hyperbase.hyperedge import Hyperedge, hedge


@dataclass
class ParseResult:
    edge: Hyperedge
    text: str
    tokens: list[str]
    tok_pos: Hyperedge
    failed: bool = False
    errors: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)
    source: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "edge": str(self.edge),
            "text": self.text,
            "tokens": self.tokens,
            "tok_pos": str(self.tok_pos),
            "failed": self.failed,
            "errors": self.errors,
            "extra": self.extra,
            "source": self.source,
        }
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ParseResult:
        edge = d["edge"]
        if isinstance(edge, str):
            edge = hedge(edge)
        elif not isinstance(edge, Hyperedge):
            raise TypeError(
                f"'edge' must be a str or Hyperedge, got {type(edge).__name__}"
            )
        edge = cast(Hyperedge, edge)
        tok_pos = d.get("tok_pos")
        if isinstance(tok_pos, str):
            tok_pos = hedge(tok_pos)
        elif tok_pos is not None and not isinstance(tok_pos, Hyperedge):
            raise TypeError(
                f"'tok_pos' must be a str or Hyperedge, got {type(tok_pos).__name__}"
            )
        tok_pos = cast(Hyperedge, tok_pos)
        return cls(
            edge=edge,
            text=d["text"],
            tokens=d["tokens"],
            tok_pos=tok_pos,
            failed=d.get("failed", False),
            errors=d.get("errors", []),
            extra=d.get("extra", {}),
            source=d.get("source", {}),
        )

    @classmethod
    def from_json(cls, json_str: str) -> ParseResult:
        return cls.from_dict(json.loads(json_str))
