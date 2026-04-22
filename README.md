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

Example (escaped for Markdown safety):

\`\`\`yaml
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
\`\`\`

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
- subscribe to events  
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

## Roadmap

- [ ] DSL schema  
- [ ] Parser + validator  
- [ ] DAG builder  
- [ ] Hybrid scheduler  
- [ ] Agent interface (RPC)  
- [ ] Markdown action-plan → `.plan` converter  
- [ ] Editor extension  
- [ ] Graph visualization  
- [ ] Multi‑agent concurrency  
- [ ] Conflict detection  
- [ ] Plan auto‑generation helpers  

---

## License

Apache 2.0 — see `LICENSE`.

---

## Status

Early scaffolding.  
Core concepts stable.  
Implementation underway.

---

## Contributing

DAGrun is designed to be:

- modular  
- deterministic  
- low‑maintenance  
- agent‑agnostic  

Contributions should preserve these principles.
