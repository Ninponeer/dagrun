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

import json
from pathlib import Path
from typing import Union, Optional
from .models import PlanModel

class StateManager:
    def __init__(self, project_root: Union[str, Path]):
        self.root = Path(project_root)
        self.state_dir = self.root / ".dagrun"
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def get_state_path(self, plan_id: str) -> Path:
        return self.state_dir / f"{plan_id}.state.json"

    def save_state(self, plan: PlanModel):
        path = self.get_state_path(plan.plan.id)
        with open(path, "w", encoding="utf-8") as f:
            f.write(plan.model_dump_json(indent=2))

    def load_state(self, plan_id: str) -> Optional[PlanModel]:
        path = self.get_state_path(plan_id)
        if not path.exists():
            return None
        try:
            return PlanModel.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception:
            return None
