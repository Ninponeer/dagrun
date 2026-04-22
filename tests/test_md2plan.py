from pathlib import Path

from dagrun.engine import DagEngine
from dagrun.md2plan import extract_action_items, md_to_plan


def test_md2plan_generates_valid_plan(tmp_path: Path):
    md = tmp_path / "oracle.md"
    md.write_text(
        "\n".join(
            [
                "# Title",
                "## 🎯 Session Overview",
                "### Key Deliverables",
                "- [ ] Deliverable 1",
                "- [ ] Deliverable 2",
                "## 🔮 Next Session Priorities",
                "### Immediate (Next session)",
                "1. Do thing A",
                "2. Do thing B",
                "### Short-Term (Within 1-2 sessions)",
                "- Task C",
                "### Deferred (Future consideration)",
                "- Task D",
                "## 📚 Related Documentation",
                "**Should Be Updated**:",
                "- [ ] `docs/a.md` — update",
                "## 🔄 Migration Checklist",
                "- [ ] Content refined",
            ]
        ),
        encoding="utf-8",
    )

    plan = md_to_plan(md, plan_id="TEST-PLAN", goal="Test", default_agent="test-agent")
    engine = DagEngine(plan)
    order = engine.get_execution_order()

    assert plan.plan.id == "TEST-PLAN"
    assert plan.plan.goal == "Test"
    assert len(plan.tasks) >= 2
    assert order[0] == "D1"


def test_md2plan_ids_are_deterministic(tmp_path: Path):
    md = tmp_path / "oracle.md"
    md.write_text(
        "\n".join(
            [
                "## 🎯 Session Overview",
                "### Key Deliverables",
                "- [ ] Deliverable 1",
                "- [ ] Deliverable 2",
                "## 🔮 Next Session Priorities",
                "### Immediate (Next session)",
                "1. Do thing A",
            ]
        ),
        encoding="utf-8",
    )

    plan1 = md_to_plan(md, plan_id="X", goal="Y", default_agent="a")
    plan2 = md_to_plan(md, plan_id="X", goal="Y", default_agent="a")
    assert [t.id for t in plan1.tasks] == [t.id for t in plan2.tasks]


def test_extract_action_items_includes_heading_path(tmp_path: Path):
    text = "\n".join(
        [
            "# Top",
            "## Section A",
            "### Sub A1",
            "- [ ] Do a thing",
        ]
    )
    items = extract_action_items(text)
    assert items[0].heading_path == ("Top", "Section A", "Sub A1")

