# DAGrun Plan File Schema (`.plan`)

A `.plan` file defines a structured, machine‑readable task graph for DAGrun.  
It consists of two top‑level sections:

- `plan` — metadata and high‑level intent
- `tasks` — the task list forming the DAG

All fields are explicit. No implicit behavior.

---

## Top‑Level Structure

plan:
id: <string>
goal: <string>

tasks:

id: <string>
title: <string>
action: <string>
agent: <string>
depends_on: <list[string]>
files: <list[string]>
mode: <pull|push|either>

Code

---

## Field Definitions

### `plan.id`
A unique identifier for the plan.

### `plan.goal`
A human‑readable description of the plan’s purpose.

---

## Task Fields

### `tasks[].id`
A unique task identifier.

### `tasks[].title`
A short human‑readable description of the task.

### `tasks[].action`
A verb or action token that the assigned agent understands.

### `tasks[].agent`
The agent responsible for executing the task.

### `tasks[].depends_on`
A list of task IDs that must complete before this task becomes runnable.

### `tasks[].files`
A list of file paths relevant to the task.

### `tasks[].mode`
Defines how the task is scheduled:

- `pull` — agent must request the task
- `push` — DAGrun notifies the agent when the task becomes runnable
- `either` — agent or orchestrator may initiate execution

---

## Example (escaped for Markdown safety)

\`\`\`yaml
plan:
  id: DEMO-01
  goal: "Example plan demonstrating schema"

tasks:
  - id: T1
    title: "Initialize module"
    action: init_module
    agent: dev-agent
    depends_on: []
    files: ["src/module/init.py"]
    mode: pull

  - id: T2
    title: "Refactor core logic"
    action: refactor_core
    agent: dev-agent
    depends_on: [T1]
    files: ["src/module/core.py"]
    mode: either

  - id: T3
    title: "Generate tests"
    action: generate_tests
    agent: test-agent
    depends_on: [T2]
    files: ["tests/test_core.py"]
    mode: push
\`\`\`

---

## Validation Rules

- All task IDs must be unique.
- All dependencies must reference valid task IDs.
- No cycles are allowed.
- `mode` must be one of: `pull`, `push`, `either`.
- `agent` must match a configured agent.
- `files` must be a list (may be empty).
- The plan must contain at least one task.

---

## Notes

- The schema is intentionally minimal.
- No implicit ordering.
- No hidden semantics.
- All behavior is explicit and deterministic.

This schema is stable and safe for early implementation.
It can be used to author `.plan` files that DAGrun can consume without risk of breaking changes while the orchestrator and agents are wired up against this structure.