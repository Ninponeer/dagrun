import sys
import argparse
from pathlib import Path
from .engine import DagEngine, DagError
from .models import PlanModel
from .state_manager import StateManager
from .parser import load_plan

def main():
    parser = argparse.ArgumentParser(
        description="DAGrun - A Directed Acyclic Graph Orchestrator for AI-Augmented Development"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init command
    init_parser = subparsers.add_parser("init", help="Initialize a DAGrun workspace")
    init_parser.add_argument("path", help="Path to the project root")

    # validate command
    val_parser = subparsers.add_parser("validate", help="Validate a .plan file")
    val_parser.add_argument("plan_file", help="Path to the .plan file")

    # visualize command
    vis_parser = subparsers.add_parser("visualize", help="Generate Mermaid.js visualization")
    vis_parser.add_argument("plan_file", help="Path to the .plan file")

    # run command
    run_parser = subparsers.add_parser("run", help="Execute a .plan file")
    run_parser.add_argument("plan_file", help="Path to the .plan file")

    args = parser.parse_args()

    if args.command == "init":
        handle_init(args.path)
    elif args.command == "validate":
        handle_validate(args.plan_file)
    elif args.command == "visualize":
        handle_visualize(args.plan_file)
    elif args.command == "run":
        handle_run(args.plan_file)
    else:
        parser.print_help()

def handle_init(path):
    project_root = Path(path)
    state_dir = project_root / ".dagrun"
    state_dir.mkdir(parents=True, exist_ok=True)
    print(f"✅ Initialized DAGrun workspace at {state_dir}")

def handle_validate(plan_file):
    try:
        plan = load_plan(plan_file)
        engine = DagEngine(plan)
        if engine.validate():
            print(f"✅ Plan {plan_file} is valid and executable.")
        else:
            print(f"❌ Plan {plan_file} failed validation.")
    except Exception as e:
        print(f"❌ Validation error: {e}")

def handle_visualize(plan_file):
    try:
        plan = load_plan(plan_file)
        engine = DagEngine(plan)
        print(engine.to_mermaid())
    except Exception as e:
        print(f"❌ Visualization error: {e}")

def handle_run(plan_file):
    try:
        plan = load_plan(plan_file)
        # Use local project root as state manager root
        project_root = Path(plan_file).parent
        state_manager = StateManager(project_root)
        engine = DagEngine(plan, state_manager=state_manager)
        
        print(f"🚀 Executing plan: {plan.plan.id} - {plan.plan.goal}")
        engine.run()
        print("✅ Plan execution complete.")
    except Exception as e:
        print(f"❌ Execution error: {e}")

if __name__ == "__main__":
    main()
