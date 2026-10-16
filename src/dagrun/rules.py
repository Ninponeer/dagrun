# Copyright (C) 2026  Rick Metz
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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

