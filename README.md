# DAGrun  
### A Directed Acyclic Graph Orchestrator for AI‑Augmented Development

**DAGrun** is a local‑first, agent‑aware orchestration engine that converts structured plan files into an executable dependency graph. It enables AI agents to collaborate on development tasks through deterministic, dependency‑driven execution.

DAGrun is:

- DAG‑driven — deterministic, dependency‑aware, cycle‑free  
- agent‑centric — built for multi‑agent workflows  
- text‑first — `.plan` files define the execution lattice  
- local‑first — no cloud dependency  
- extensible — any agent can integrate via a simple protocol  
- IDE‑native — designed for direct editor integration  

---

## Purpose

DAGrun provides a machine‑readable execution graph for AI agents.  
It replaces ad‑hoc planning with a structured, dependency‑aware system that agents can:

- pull from (“What tasks are ready for me”)  
- receive pushes from (“A dependency cleared; begin execution”)  
- collaborate through (“Task complete; update state and unblock others”)  

DAGrun is the orchestration substrate for AI‑augmented engineering.

---

## Core Concepts

### Plan Files (`.plan`)
A structured DSL defining:

- tasks  
- dependencies  
- agents  
- actions  
- file targets  
- scheduling mode (pull, push, either)

Example:

```yaml
plan:
  id: PIPELINE-14
  goal: "Stabilize ingestion pipeline"

tasks:
  - id: T1
    title: "Integrate new data source"
    action: implement_ingestion
    agent: pipeline-agent
    depends_on: []
    files: ["src/pipeline/ingest.py"]
    mode: either

  - id: T2
    title: "Fix memory leak"
    action: debug_memory
    agent: pipeline-agent
    depends_on: [T1]
    files: ["src/pipeline/memory.cpp"]
    mode: push
```

---

## Architecture Overview

### 1. Parser  
Validates and converts `.plan` files into an AST.

### 2. DAG Builder  
Constructs the directed acyclic graph representing task flow.

### 3. Hybrid Scheduler  
Supports:

- pull mode — agents request runnable tasks  
- push mode — orchestrator emits events when tasks become unblocked  
- hybrid mode — tasks declare their own scheduling behavior  

### 4. Agent Interface Layer  
A local command and event API enabling agents to:

- query task readiness  
- retrieve context  
- mark tasks complete  
- update plan state  

### 5. Editor Integration (Optional)  
Provides:

- syntax highlighting  
- plan validation  
- dependency graph visualization  
- task panels  
- agent activity feed  

---

## Why DAGrun Exists

Traditional planning frameworks are optimized for human coordination.  
DAGrun is optimized for AI‑assisted execution.

It focuses on:

- dependency resolution  
- deterministic execution  
- structured plans  
- agent autonomy  
- hybrid scheduling  

DAGrun is a post‑ceremony orchestration substrate for modern development workflows.

---

## Usage

### Installation
```bash
pip install .
```

### Commands

#### 1. Initialize Workspace
Creates a `.dagrun` folder in your project root to store plans and state.
```bash
dagrun init /path/to/project
```

#### 2. Validate Plan
Checks for schema correctness and DAG logical errors (cycles, missing dependencies).
```bash
dagrun validate my_plan.plan
```

#### 3. Visualize DAG
Generates a Mermaid.js graph definition for visualization in Mermaid-compatible viewers.
```bash
dagrun visualize my_plan.plan
```

#### 4. Status
Show current progress (human or JSON).
```bash
dagrun status my_plan.plan
dagrun status my_plan.plan --json
```

#### 5. Agent workflow (primary integration path)

Claim the next ready task for a specific agent:
```bash
dagrun next my_plan.plan --agent dev-agent
dagrun next my_plan.plan --agent dev-agent --json
```

Mark a task complete (optionally with a result note):
```bash
dagrun complete my_plan.plan T1 --result "Implemented and smoke-tested"
```

Mark a task failed:
```bash
dagrun fail my_plan.plan T2 --error "Missing dependency X"
```

State is persisted under `.dagrun/<plan_id>.state.json` so progress survives across process restarts. This is the intended interface for Hermes profiles and other agents.

#### 6. Run (experimental)
Lists currently ready tasks. Full automatic execution is not yet implemented; prefer the agent commands above.
```bash
dagrun run my_plan.plan
```

---

## Hermes / multi-agent notes

- Map each Hermes profile to a stable `agent` name that matches the `agent:` field in `.plan` files.
- Agents should only act on tasks returned by `dagrun next --agent <id>`.
- After finishing work, call `dagrun complete` (or `fail`) so dependents become ready.
- Use `dagrun status --json` for machine-readable situational awareness.

---

## Roadmap

- [x] DSL schema  
- [x] Parser + validator  
- [x] DAG builder  
- [x] Agent CLI surface (`next` / `complete` / `fail` / `status`)  
- [ ] Hybrid scheduler events (push notifications)  
- [ ] Markdown action-plan → `.plan` converter polish  
- [ ] Editor extension  
- [ ] Multi‑agent concurrency guards  
- [ ] Conflict detection  
- [ ] Plan auto‑generation helpers  

---

## License

Apache 2.0 — see `LICENSE`.

---

## Status

Early but usable for agent-driven workflows.  
Core concepts stable.  
Agent CLI surface in place.

---

## Contributing

DAGrun is designed to be:

- modular  
- deterministic  
- low‑maintenance  
- agent‑agnostic  

Contributions should preserve these principles.
