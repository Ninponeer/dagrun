from __future__ import annotations

from pathlib import Path
from typing import List, Literal, Optional, Sequence, Tuple

import yaml
from pydantic import BaseModel, Field

from .md2plan import Rule


class RuleConfig(BaseModel):
    name: str
    prefix: str
    mode: Literal["pull", "push", "either"] = "either"
    action: str = "execute"
    agent: Optional[str] = None
    match_section_contains: List[str] = Field(default_factory=list)
    match_heading_path_contains: List[str] = Field(default_factory=list)
    match_kind: List[Literal["checkbox", "numbered", "bullet"]] = Field(default_factory=list)
    exclude_section_contains: List[str] = Field(default_factory=list)
    exclude_heading_path_contains: List[str] = Field(default_factory=list)
    exclude_kind: List[Literal["checkbox", "numbered", "bullet"]] = Field(default_factory=list)

    def to_rule(self) -> Rule:
        return Rule(
            name=self.name,
            prefix=self.prefix,
            mode=self.mode,
            action=self.action,
            agent=self.agent,
            match_section_contains=tuple(self.match_section_contains),
            match_heading_path_contains=tuple(self.match_heading_path_contains),
            match_kind=tuple(self.match_kind),
            exclude_section_contains=tuple(self.exclude_section_contains),
            exclude_heading_path_contains=tuple(self.exclude_heading_path_contains),
            exclude_kind=tuple(self.exclude_kind),
        )


class RulesetConfig(BaseModel):
    version: int = 1
    rules: List[RuleConfig]

    def to_rules(self) -> List[Rule]:
        return [r.to_rule() for r in self.rules]


def load_ruleset(path: Path) -> Sequence[Rule]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    cfg = RulesetConfig.model_validate(data)
    return cfg.to_rules()

