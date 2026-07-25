import argparse
import json
import sys
from pathlib import Path

from .engine import DagEngine, DagError
from .interface import AgentInterface
from .models import PlanModel, TaskStatus
from .parser import load_plan
from .state_manager import StateManager
from .workspace import find_project_root


def load_plan_with_state(plan_file: str) -> tuple[PlanModel, StateManager, DagEngine]:
    """Load a .plan file and overlay any persisted state from .dagrun/."""
    plan_path = Path(plan_file)
    if not plan_path.exists():
        raise FileNotFoundError(f"Plan file not found: {plan_file}")

    base_plan = load_plan(plan_path)
    project_root = find_project_root(plan_path)
    state_manager = StateManager(project_root)

    # Prefer persisted state if it exists (carries status / results)
    saved = state_manager.load_state(base_plan.plan.id)
    plan = saved if saved is not None else base_plan

    engine = DagEngine(plan, state_manager=state_manager)
    return plan, state_manager, engine


def main():
    parser = argparse.ArgumentParser(
        description="DAGrun - A Directed Acyclic Graph Orchestrator for AI-Augmented Development"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init
    init_parser = subparsers.add_parser("init", help="Initialize a DAGrun workspace")
    init_parser.add_argument("path", help="Path to the project root")

    # validate
    val_parser = subparsers.add_parser("validate", help="Validate a .plan file")
    val_parser.add_argument("plan_file", help="Path to the .plan file")

    # visualize
    vis_parser = subparsers.add_parser("visualize", help="Generate Mermaid.js visualization")
    vis_parser.add_argument("plan_file", help="Path to the .plan file")

    # run (placeholder / future full executor)
    run_parser = subparsers.add_parser("run", help="Execute a .plan file (experimental)")
    run_parser.add_argument("plan_file", help="Path to the .plan file")

    # --- Agent-facing commands ---

    # next
    next_parser = subparsers.add_parser(
        "next", help="Claim the next ready task for an agent"
    )
    next_parser.add_argument("plan_file", help="Path to the .plan file")
    next_parser.add_argument(
        "--agent", required=True, help="Agent ID that is requesting work"
    )
    next_parser.add_argument(
        "--json", action="store_true", help="Emit machine-readable JSON"
    )

    # complete
    complete_parser = subparsers.add_parser(
        "complete", help="Mark a task as completed"
    )
    complete_parser.add_argument("plan_file", help="Path to the .plan file")
    complete_parser.add_argument("task_id", help="Task ID to complete")
    complete_parser.add_argument(
        "--result", default="", help="Optional result / notes to store"
    )

    # fail
    fail_parser = subparsers.add_parser("fail", help="Mark a task as failed")
    fail_parser.add_argument("plan_file", help="Path to the .plan file")
    fail_parser.add_argument("task_id", help="Task ID to fail")
    fail_parser.add_argument(
        "--error", default="", help="Optional error message to store"
    )

    # status
    status_parser = subparsers.add_parser(
        "status", help="Show current status of a plan"
    )
    status_parser.add_argument("plan_file", help="Path to the .plan file")
    status_parser.add_argument(
        "--json", action="store_true", help="Emit machine-readable JSON"
    )

    args = parser.parse_args()

    if args.command == "init":
        handle_init(args.path)
    elif args.command == "validate":
        handle_validate(args.plan_file)
    elif args.command == "visualize":
        handle_visualize(args.plan_file)
    elif args.command == "run":
        handle_run(args.plan_file)
    elif args.command == "next":
        handle_next(args.plan_file, args.agent, args.json)
    elif args.command == "complete":
        handle_complete(args.plan_file, args.task_id, args.result)
    elif args.command == "fail":
        handle_fail(args.plan_file, args.task_id, args.error)
    elif args.command == "status":
        handle_status(args.plan_file, args.json)
    else:
        parser.print_help()


def handle_init(path: str):
    project_root = Path(path)
    state_dir = project_root / ".dagrun"
    state_dir.mkdir(parents=True, exist_ok=True)
    print(f"✅ Initialized DAGrun workspace at {state_dir}")


def handle_validate(plan_file: str):
    try:
        plan = load_plan(plan_file)
        engine = DagEngine(plan)
        if engine.validate():
            print(f"✅ Plan {plan_file} is valid and executable.")
        else:
            print(f"❌ Plan {plan_file} failed validation.")
    except Exception as e:
        print(f"❌ Validation error: {e}")
        sys.exit(1)


def handle_visualize(plan_file: str):
    try:
        plan, _, engine = load_plan_with_state(plan_file)
        print(engine.to_mermaid())
    except Exception as e:
        print(f"❌ Visualization error: {e}")
        sys.exit(1)


def handle_run(plan_file: str):
    try:
        plan, state_manager, engine = load_plan_with_state(plan_file)
        print(f"🚀 Plan: {plan.plan.id} — {plan.plan.goal}")
        print("Note: full automatic execution is not yet implemented.")
        print("Use `dagrun next`, `dagrun complete`, and `dagrun status` for agent-driven runs.")
        ready = engine.get_ready_tasks()
        if not ready:
            print("No tasks currently ready.")
        else:
            print(f"{len(ready)} task(s) ready:")
            for t in ready:
                print(f"  - {t.id}: {t.title} (agent={t.agent}, mode={t.mode})")
    except Exception as e:
        print(f"❌ Execution error: {e}")
        sys.exit(1)


def handle_next(plan_file: str, agent_id: str, as_json: bool):
    try:
        plan, state_manager, engine = load_plan_with_state(plan_file)
        iface = AgentInterface(engine, state_manager=state_manager)
        task = iface.get_next_task(agent_id)

        if task is None:
            if as_json:
                print(json.dumps({"task": None, "message": "No ready tasks for this agent"}))
            else:
                print(f"No ready tasks for agent '{agent_id}'.")
            return

        payload = {
            "id": task.id,
            "title": task.title,
            "action": task.action,
            "agent": task.agent,
            "files": task.files,
            "mode": task.mode,
            "depends_on": task.depends_on,
            "status": task.status.value if hasattr(task.status, "value") else str(task.status),
        }

        if as_json:
            print(json.dumps({"task": payload}, indent=2))
        else:
            print(f"✅ Claimed task {task.id}: {task.title}")
            print(f"   action : {task.action}")
            print(f"   files  : {', '.join(task.files) if task.files else '(none)'}")
            print(f"   mode   : {task.mode}")
    except Exception as e:
        print(f"❌ next error: {e}")
        sys.exit(1)


def handle_complete(plan_file: str, task_id: str, result: str):
    try:
        plan, state_manager, engine = load_plan_with_state(plan_file)
        iface = AgentInterface(engine, state_manager=state_manager)
        ok = iface.complete_task(task_id, result=result)
        if not ok:
            print(f"❌ Task '{task_id}' not found.")
            sys.exit(1)
        print(f"✅ Task {task_id} marked completed.")
        if result:
            print(f"   result: {result}")
    except Exception as e:
        print(f"❌ complete error: {e}")
        sys.exit(1)


def handle_fail(plan_file: str, task_id: str, error: str):
    try:
        plan, state_manager, engine = load_plan_with_state(plan_file)
        iface = AgentInterface(engine, state_manager=state_manager)
        iface.fail_task(task_id, error=error)
        print(f"❌ Task {task_id} marked failed.")
        if error:
            print(f"   error: {error}")
    except Exception as e:
        print(f"❌ fail error: {e}")
        sys.exit(1)


def handle_status(plan_file: str, as_json: bool):
    try:
        plan, _, engine = load_plan_with_state(plan_file)

        counts = {s.value: 0 for s in TaskStatus}
        tasks_out = []
        for t in plan.tasks:
            status_val = t.status.value if hasattr(t.status, "value") else str(t.status)
            counts[status_val] = counts.get(status_val, 0) + 1
            tasks_out.append(
                {
                    "id": t.id,
                    "title": t.title,
                    "agent": t.agent,
                    "status": status_val,
                    "depends_on": t.depends_on,
                    "mode": t.mode,
                }
            )

        ready = [
            {"id": t.id, "title": t.title, "agent": t.agent}
            for t in engine.get_ready_tasks()
        ]

        if as_json:
            print(
                json.dumps(
                    {
                        "plan_id": plan.plan.id,
                        "goal": plan.plan.goal,
                        "counts": counts,
                        "ready": ready,
                        "tasks": tasks_out,
                    },
                    indent=2,
                )
            )
        else:
            print(f"Plan: {plan.plan.id} — {plan.plan.goal}")
            print(
                f"Status: {counts.get('completed', 0)} completed · "
                f"{counts.get('running', 0)} running · "
                f"{counts.get('pending', 0)} pending · "
                f"{counts.get('failed', 0)} failed"
            )
            if ready:
                print("Ready tasks:")
                for r in ready:
                    print(f"  - {r['id']}: {r['title']} (agent={r['agent']})")
            else:
                print("No tasks currently ready.")
    except Exception as e:
        print(f"❌ status error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
