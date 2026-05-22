import argparse
import sys
from pathlib import Path
from .parser import load_plan
from .engine import DagEngine, DagError
from .md2plan import extract_action_items, extracted_to_json, md_to_plan, plan_to_yaml_with_header, plan_to_yaml
from .rules import load_ruleset
from .workspace import ensure_dagrun_dir, find_project_root

def _get_version() -> str | None:
    try:
        from importlib.metadata import version

        return version("dagrun")
    except Exception:
        return None

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

    # Run command
    run_parser = subparsers.add_parser("run", help="Execute a .plan file")
    run_parser.add_argument("plan", type=Path, help="Path to the .plan file")
    run_parser.add_argument("--dry-run", action="store_true", help="Print execution order without running tasks")

    # Visualize command
    viz_parser = subparsers.add_parser("visualize", help="Generate a Mermaid chart for a .plan file")
    viz_parser.add_argument("plan", type=Path, help="Path to the .plan file")

    # Invalidate command
    inv_parser = subparsers.add_parser("invalidate", help="Invalidate tasks and their dependencies")
    inv_parser.add_argument("plan", type=Path, help="Path to the .plan file")
    inv_parser.add_argument("--macro", type=str, help="Macro lane to invalidate")
    inv_parser.add_argument("--micro", type=str, help="Micro lane to invalidate")
    inv_parser.add_argument("--task", type=str, help="Specific task ID to invalidate")

    # Embed Visualization command
    embed_parser = subparsers.add_parser("embed-viz", help="Embed the Mermaid chart into the source Markdown file")
    embed_parser.add_argument("plan", type=Path, help="Path to the .plan file")
    embed_parser.add_argument("markdown", type=Path, help="Path to the source .md file")

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize DAGrun workspace (.dagrun folder)")
    init_parser.add_argument(
        "path",
        type=Path,
        nargs="?",
        default=Path.cwd(),
        help="Project path (default: current directory)",
    )

    # md command group
    md_parser = subparsers.add_parser("md", help="Markdown utilities (extract, convert)")
    md_sub = md_parser.add_subparsers(dest="md_command", required=True)

    md_extract = md_sub.add_parser("extract", help="Extract actionable items from Markdown (JSON)")
    md_extract.add_argument("markdown", type=Path, help="Path to the source .md file")

    # md2plan command
    md2plan_parser = md_sub.add_parser("to-plan", help="Convert Markdown action items into a .plan file")
    md2plan_parser.add_argument("markdown", type=Path, help="Path to the source .md file")
    md2plan_parser.add_argument("-o", "--out", type=Path, help="Output .plan path (default: <project>/.dagrun/<stem>.plan)")
    md2plan_parser.add_argument("--id", dest="plan_id", help="Override plan.id (default: markdown filename stem)")
    md2plan_parser.add_argument("--goal", dest="goal", help="Override plan.goal")
    md2plan_parser.add_argument("--agent", dest="agent", default="dev-agent", help="Default agent name for tasks")
    md2plan_parser.add_argument("--rules", type=Path, help="Path to a ruleset YAML file")
    md2plan_parser.add_argument("--id-strategy", choices=["index", "hash"], default="index")
    md2plan_parser.add_argument("--no-chain", action="store_true", help="Do not chain dependencies between generated tasks")

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
            
        return

    elif args.command == "visualize":
        try:
            plan = load_plan(args.plan)
            engine = DagEngine(plan)
            print(engine.to_mermaid())
        except Exception as e:
            print(f"❌ Visualization failed: {e}", file=sys.stderr)
            sys.exit(1)
        return

    elif args.command == "invalidate":
        try:
            plan = load_plan(args.plan)
            engine = DagEngine(plan)
            
            impacted = set()
            if args.task:
                impacted = engine.invalidate_task(args.task)
                print(f"Invalidating task '{args.task}' and its downstream dependencies...")
            elif args.macro:
                impacted = engine.invalidate_lane(args.macro, args.micro)
                print(f"Invalidating Macro-Lane '{args.macro}'" + (f" (Micro: {args.micro})" if args.micro else "") + " and dependencies...")
            else:
                print("❌ Error: You must specify either --task or --macro to invalidate.", file=sys.stderr)
                sys.exit(1)

            if not impacted:
                print("No tasks were impacted by this invalidation.")
                return

            print(f"✅ {len(impacted)} task(s) reset to PENDING.")
            
            # Save the updated plan
            out_yaml = plan_to_yaml_with_header(
                plan,
                source_path=args.plan,
                generator_version=_get_version(),
            )
            args.plan.write_text(out_yaml, encoding="utf-8")
            print(f"✅ Updated plan saved to: {args.plan}")

        except Exception as e:
            print(f"❌ Invalidation failed: {e}", file=sys.stderr)
            sys.exit(1)
        return

    elif args.command == "embed-viz":
        try:
            plan = load_plan(args.plan)
            engine = DagEngine(plan)
            mermaid_graph = engine.to_mermaid()
            
            md_path = args.markdown
            content = md_path.read_text(encoding="utf-8")
            
            # Avoid duplicate embeddings
            if "## Execution Graph" in content:
                import re
                content = re.sub(r"## Execution Graph.*?\n```mermaid.*?```", "", content, flags=re.DOTALL)
            
            viz_block = f"\n\n## Execution Graph\n\n```mermaid\n{mermaid_graph}\n```\n"
            md_path.write_text(content.strip() + viz_block, encoding="utf-8")
            print(f"✅ Embedded graph into: {md_path}")
        except Exception as e:
            print(f"❌ Embedding failed: {e}", file=sys.stderr)
            sys.exit(1)
        return

    elif args.command == "run":

        try:
            plan = load_plan(args.plan)
            engine = DagEngine(plan)
            
            if args.dry_run:
                print(f"🚀 Dry run for plan '{plan.plan.id}'")
                order = engine.get_execution_order()
                for i, task_id in enumerate(order, 1):
                    task = engine.tasks[task_id]
                    print(f"  {i}. {task_id}: {task.title}")
                return

            print(f"🚀 Executing plan '{plan.plan.id}'...")
            engine.run()
            print("✅ Execution completed successfully.")
        except Exception as e:
            print(f"❌ Execution failed: {e}", file=sys.stderr)
            sys.exit(1)
            
        return

    elif args.command == "init":
        try:
            root = find_project_root(args.path)
            dagrun_dir = ensure_dagrun_dir(root)
            print(f"✅ Initialized DAGrun workspace at: {dagrun_dir}")
        except Exception as e:
            print(f"❌ init failed: {e}", file=sys.stderr)
            sys.exit(1)
        return

    elif args.command == "md":
        try:
            if args.md_command == "extract":
                text = args.markdown.read_text(encoding="utf-8")
                items = extract_action_items(text)
                print(extracted_to_json(items))
                return

            if args.md_command == "to-plan":
                rules = load_ruleset(args.rules) if args.rules else None
                plan = md_to_plan(
                    args.markdown,
                    plan_id=args.plan_id,
                    goal=args.goal,
                    default_agent=args.agent,
                    rules=rules,
                    id_strategy=args.id_strategy,
                    chain_dependencies=not args.no_chain,
                )
                out_yaml = plan_to_yaml_with_header(
                    plan,
                    source_path=args.markdown.resolve(),
                    ruleset_path=args.rules.resolve() if args.rules else None,
                    generator_version=_get_version(),
                )
                out_path = args.out
                if out_path is None:
                    root = find_project_root(args.markdown)
                    dagrun_dir = ensure_dagrun_dir(root)
                    out_path = dagrun_dir / f"{args.markdown.stem}.plan"
                out_path.write_text(out_yaml, encoding="utf-8")
                print(f"✅ Wrote plan: {out_path}")
                return
        except Exception as e:
            print(f"❌ Markdown tool failed: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
