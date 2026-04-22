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
