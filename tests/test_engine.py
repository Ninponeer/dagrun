import pytest
from dagrun.models import PlanModel, TaskModel, PlanMetadata
from dagrun.engine import DagEngine, DagError

def test_valid_dag_order():
    plan = PlanModel(
        plan=PlanMetadata(id="TEST", goal="Test"),
        tasks=[
            TaskModel(id="T1", title="T1", action="A1", agent="Ag1", depends_on=[]),
            TaskModel(id="T2", title="T2", action="A2", agent="Ag2", depends_on=["T1"]),
            TaskModel(id="T3", title="T3", action="A3", agent="Ag3", depends_on=["T2"]),
        ]
    )
    engine = DagEngine(plan)
    assert engine.get_execution_order() == ["T1", "T2", "T3"]

def test_cycle_detection():
    plan = PlanModel(
        plan=PlanMetadata(id="CYCLE", goal="Test Cycle"),
        tasks=[
            TaskModel(id="T1", title="T1", action="A1", agent="Ag1", depends_on=["T2"]),
            TaskModel(id="T2", title="T2", action="A2", agent="Ag2", depends_on=["T1"]),
        ]
    )
    with pytest.raises(DagError, match="Cycle detected"):
        DagEngine(plan)

def test_missing_dependency():
    plan = PlanModel(
        plan=PlanMetadata(id="MISSING", goal="Test Missing"),
        tasks=[
            TaskModel(id="T1", title="T1", action="A1", agent="Ag1", depends_on=["NON_EXISTENT"]),
        ]
    )
    with pytest.raises(DagError, match="depends on non-existent task"):
        DagEngine(plan)

def test_multiple_ready_tasks_determinism():
    # T1 and T2 are both ready. T3 depends on both.
    # Order should be ['T1', 'T2', 'T3'] because we sort alphabetically
    plan = PlanModel(
        plan=PlanMetadata(id="MULTI", goal="Test Determinism"),
        tasks=[
            TaskModel(id="T2", title="T2", action="A2", agent="Ag2", depends_on=[]),
            TaskModel(id="T1", title="T1", action="A1", agent="Ag1", depends_on=[]),
            TaskModel(id="T3", title="T3", action="A3", agent="Ag3", depends_on=["T1", "T2"]),
        ]
    )
    engine = DagEngine(plan)
    assert engine.get_execution_order() == ["T1", "T2", "T3"]
