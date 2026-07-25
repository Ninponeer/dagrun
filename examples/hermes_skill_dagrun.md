# Hermes Skill Skeleton — DAGrun

Drop this (or adapt it) into a Hermes skill so a profile can only work inside an approved plan.

## Intent

- Never invent free-form work when a `.plan` is active.
- Only claim tasks assigned to this profile’s agent ID.
- Always complete or fail tasks so the DAG can progress.

## Required config (per Hermes profile)

```yaml
# Example profile knobs
agent_id: hk-47          # must match `agent:` field in .plan files
plan_file: ./my_feature.plan
project_root: .
```

## Tools the skill should expose / call

These map 1:1 to the DAGrun CLI:

| Skill action        | CLI equivalent                                      |
|---------------------|-----------------------------------------------------|
| `dagrun_status`     | `dagrun status <plan> --json`                       |
| `dagrun_next`       | `dagrun next <plan> --agent <agent_id> --json`      |
| `dagrun_complete`   | `dagrun complete <plan> <task_id> --result "..."`   |
| `dagrun_fail`       | `dagrun fail <plan> <task_id> --error "..."`        |
| `dagrun_validate`   | `dagrun validate <plan>`                            |
| `dagrun_visualize`  | `dagrun visualize <plan>`                           |

## Suggested agent loop

1. `dagrun_status` — understand current state.
2. `dagrun_next` — claim one ready task (or stop if none).
3. Do the work described by `title` / `action` / `files`.
4. `dagrun_complete` (or `dagrun_fail`) with a short result note.
5. Repeat until no ready tasks remain for this agent.

## Guardrails to put in the skill prompt

- You may only execute tasks returned by `dagrun_next` for your `agent_id`.
- Do not modify the `.plan` file unless the user explicitly asks for a plan edit.
- If `dagrun_next` returns no task, stop and report status instead of inventing work.
- Prefer small, verifiable steps; write results back via `--result`.

## Minimal shell wrappers (if Hermes calls CLI directly)

```bash
# status
dagrun status "$PLAN_FILE" --json

# claim
dagrun next "$PLAN_FILE" --agent "$AGENT_ID" --json

# complete
dagrun complete "$PLAN_FILE" "$TASK_ID" --result "$RESULT"

# fail
dagrun fail "$PLAN_FILE" "$TASK_ID" --error "$ERROR"
```

## Notes

- State lives in `.dagrun/<plan_id>.state.json` — safe across restarts.
- Multiple Hermes profiles can share one plan as long as their `agent_id`s differ.
- Pair this skill with your existing `scaffold_hermes_profiles.py` so each profile has a stable agent name.
