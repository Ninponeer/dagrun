import json
from pathlib import Path

import pytest

from dagrun.engine import DagEngine
from dagrun.interface import AgentInterface
from dagrun.models import PlanMetadata, PlanModel, TaskModel, TaskStatus
from dagrun.state_manager import StateManager


@pytest.fixture
def sample_plan(tmp_path: Path):
    plan = PlanModel(
        plan=PlanMetadata(id="AGENT-TEST", goal="Agent interface smoke test"),
        tasks=[
            TaskModel(
                id="T1",
                title="First task",
                action="do_first",
                agent="dev-agent",
                depends_on=[],
                files=["src/a.py"],
                mode="pull",
            ),
            TaskModel(
                id="T2",
                title="Second task",
                action="do_second",
                agent="dev-agent",
                depends_on=["T1"],
                files=["src/b.py"],
                mode="either",
            ),
            TaskModel(
                id="T3",
                title="Other agent task",
                action="do_other",
                agent="other-agent",
                depends_on=[],
                files=[],
                mode="push",
            ),
        ],
    )
    # Persist initial plan state under a temp project root
    sm = StateManager(tmp_path)
    sm.save_state(plan)
    return plan, sm


def test_get_next_task_claims_and_marks_running(sample_plan):
    plan, sm = sample_plan
    engine = DagEngine(plan, state_manager=sm)
    iface = AgentInterface(engine, state_manager=sm)

    task = iface.get_next_task("dev-agent")
    assert task is not None
    assert task.id == "T1"
    assert task.status == TaskStatus.RUNNING

    # Other agent can still claim its own ready task
    other = iface.get_next_task("other-agent")
    assert other is not None
    assert other.id == "T3"


def test_complete_unblocks_dependent(sample_plan):
    plan, sm = sample_plan
    engine = DagEngine(plan, state_manager=sm)
    iface = AgentInterface(engine, state_manager=sm)

    t1 = iface.get_next_task("dev-agent")
    assert t1.id == "T1"

    ok = iface.complete_task("T1", result="done")
    assert ok is True
    assert engine.tasks["T1"].status == TaskStatus.COMPLETED
    assert engine.tasks["T1"].result == "done"

    # T2 should now be ready
    t2 = iface.get_next_task("dev-agent")
    assert t2 is not None
    assert t2.id == "T2"


def test_fail_task(sample_plan):
    plan, sm = sample_plan
    engine = DagEngine(plan, state_manager=sm)
    iface = AgentInterface(engine, state_manager=sm)

    t1 = iface.get_next_task("dev-agent")
    assert t1.id == "T1"

    ok = iface.fail_task("T1", error="boom")
    assert ok is True
    assert engine.tasks["T1"].status == TaskStatus.FAILED
    assert "boom" in (engine.tasks["T1"].result or "")


def test_no_task_for_unknown_agent(sample_plan):
    plan, sm = sample_plan
    engine = DagEngine(plan, state_manager=sm)
    iface = AgentInterface(engine, state_manager=sm)

    task = iface.get_next_task("nobody")
    assert task is None


def test_state_roundtrip(tmp_path: Path):
    plan = PlanModel(
        plan=PlanMetadata(id="ROUNDTRIP", goal="Persist and reload"),
        tasks=[
            TaskModel(
                id="T1",
                title="Only",
                action="act",
                agent="dev-agent",
                depends_on=[],
            )
        ],
    )
    sm = StateManager(tmp_path)
    engine = DagEngine(plan, state_manager=sm)
    iface = AgentInterface(engine, state_manager=sm)

    t = iface.get_next_task("dev-agent")
    assert t is not None
    iface.complete_task("T1", result="persisted")

    # Reload from disk
    reloaded = sm.load_state("ROUNDTRIP")
    assert reloaded is not None
    assert reloaded.tasks[0].status == TaskStatus.COMPLETED
    assert reloaded.tasks[0].result == "persisted"
