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

import yaml
from pathlib import Path
from typing import Union
from .models import PlanModel

def load_plan(plan_path: Union[str, Path]) -> PlanModel:
    """
    Loads and validates a .plan file from a YAML source accurately.
    """
    path = Path(plan_path)
    if not path.exists():
        raise FileNotFoundError(f"Plan file not found: {plan_path}")
    
    # Always prefer UTF-8 to support Unicode in plan files across platforms.
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Fallback for legacy files; still deterministic.
        raw = path.read_text(encoding="utf-8-sig")

    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML in {plan_path}: {e}")
    
    # Pydantic validation
    return PlanModel(**data)

def validate_plan_schema(plan_path: Union[str, Path]) -> bool:
    """
    Check if a plan is valid without returning the model.
    """
    try:
        load_plan(plan_path)
        return True
    except (FileNotFoundError, ValueError, Exception):
        return False
