import argparse
import sys
from pathlib import Path
from .parser import load_plan
from .engine import DagEngine, DagError

def main():
    # Ensure UTF-8 output on Windows consoles
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(prog="dagrun", description="DAGrun Orchestrator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a .plan file")
    validate_parser.add_argument("plan", type=Path, help="Path to the .plan file")

    args = parser.parse_args()

    if args.command == "validate":
        try:
            # 1. Load and parse (schema validation)
            plan = load_plan(args.plan)
            
            # 2. Build DAG and check for logical errors (cycles/missing deps)
            engine = DagEngine(plan)
            order = engine.get_execution_order()
            
            # 3. Report Success
            print(f"✅ Plan '{plan.plan.id}' is valid.")
            print(f"Goal: {plan.plan.goal}")
            print("\nProposed Execution Order:")
            for i, task_id in enumerate(order, 1):
                task = engine.tasks[task_id]
                print(f"  {i}. {task_id}: {task.title} (Agent: {task.agent})")
            
        except Exception as e:
            print(f"❌ Validation failed: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
