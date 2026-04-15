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
    
    with open(path, 'r') as f:
        try:
            data = yaml.safe_load(f)
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
