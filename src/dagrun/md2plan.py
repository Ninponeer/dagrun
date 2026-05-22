from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Literal, Optional, Sequence, Tuple

import yaml

from .models import PlanMetadata, PlanModel, TaskModel


@dataclass(frozen=True)
class ExtractedItem:
    section: str  # nearest heading text
    heading_path: Tuple[str, ...]  # full heading ancestry (##, ###, ...)
    text: str
    checked: Optional[bool] = None  # for [ ] / [x] items when present
    kind: Literal["checkbox", "numbered", "bullet"] = "bullet"
    file_paths: Tuple[str, ...] = ()
    indent: int = 0  # Indentation level for hierarchy


def _strip_md_inline(text: str) -> str:
    # Minimal inline cleanup: drop backticks and collapse whitespace.
    text = text.replace("`", "")
    return " ".join(text.strip().split())


def _parse_checkbox(line: str) -> Optional[Tuple[bool, str]]:
    s = line.lstrip()
    if not (s.startswith("- [") or s.startswith("* [")):
        return None
    # Examples: "- [ ] Deliverable", "- [x] Done"
    if len(s) < 6 or s[4] != "]":
        return None
    marker = s[3].lower()
    checked = marker == "x"
    rest = s[5:].strip()
    if not rest:
        return None
    return checked, rest


def _parse_numbered_item(line: str) -> Optional[str]:
    s = line.lstrip()
    # "1. foo" / "2) foo"
    i = 0
    while i < len(s) and s[i].isdigit():
        i += 1
    if i == 0:
        return None
    if i >= len(s):
        return None
    if s[i : i + 2] == ". ":
        return s[i + 2 :].strip() or None
    if s[i : i + 2] == ") ":
        return s[i + 2 :].strip() or None
    return None


def _parse_bullet_item(line: str) -> Optional[str]:
    s = line.lstrip()
    if s.startswith("- "):
        return s[2:].strip() or None
    if s.startswith("* "):
        return s[2:].strip() or None
    return None


_BACKTICK_RE = re.compile(r"`([^`]+)`")
_FILELIKE_RE = re.compile(r"(?i)\b[\w./-]+\.(py|ts|tsx|js|json|yaml|yml|md|txt|toml|ini|cfg|cs|cpp|c|h|hpp|gd|tres|tscn)\b")
_DEPENDENCY_RE = re.compile(r"(?:depends\s*on|depends:)\s*([A-Z]\d+)", re.IGNORECASE)
_MACRO_LANE_RE = re.compile(r"(?i)Macro-Lane:\s*(.*)")
_MICRO_LANE_RE = re.compile(r"(?i)Micro-Lane:\s*(.*)")


def _extract_file_paths(text: str) -> Tuple[str, ...]:
    candidates: List[str] = []
    for m in _BACKTICK_RE.finditer(text):
        candidates.append(m.group(1))
    candidates.extend(_FILELIKE_RE.findall(text))  # note: findall returns extensions if grouped
    # Fix grouped findall behavior: use finditer instead.
    candidates = [m.group(0) for m in _FILELIKE_RE.finditer(text)] + [c for c in candidates if "/" in c or "." in c]
    # Normalize / dedupe deterministically.
    normed: List[str] = []
    seen = set()
    for c in candidates:
        c2 = c.strip()
        if not c2:
            continue
        if c2 in seen:
            continue
        seen.add(c2)
        normed.append(c2)
    return tuple(normed)


def _extract_swim_lanes(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extracts Macro-Lane and Micro-Lane from document metadata.
    """
    macro, micro = None, None
    for line in text.splitlines():
        m_macro = _MACRO_LANE_RE.search(line)
        if m_macro:
            macro = m_macro.group(1).strip()
        m_micro = _MICRO_LANE_RE.search(line)
        if m_micro:
            micro = m_micro.group(1).strip()
    return macro, micro


def extract_action_items(md_text: str) -> List[ExtractedItem]:
    """
    Extracts actionable items from Markdown.

    Deterministic rules:
    - Track heading path (## / ### / ####...). Items are attributed to the nearest heading.
    - Extract:
      - checkbox list items: "- [ ] ..." / "- [x] ..."
      - numbered list items: "1. ..." / "1) ..."
      - bullet list items (best-effort; agents/rulesets can filter downstream)
    """
    items: List[ExtractedItem] = []
    heading_stack: List[Tuple[int, str]] = []  # (level, text)
    current_section: str = "Uncategorized"

    def heading_path() -> Tuple[str, ...]:
        return tuple(h[1] for h in heading_stack) if heading_stack else ("Uncategorized",)

    for raw in md_text.splitlines():
        line = raw.rstrip("\n")
        if not line.strip():
            continue
            
        # Calculate indentation level (number of leading spaces / 2)
        indent = len(line) - len(line.lstrip())
        indent_level = indent // 2

        if line.startswith("#"):
            # Markdown headings: count leading # until a space.
            m = re.match(r"^(#{1,6})\s+(.*)$", line)
            if m:
                level = len(m.group(1))
                text = _strip_md_inline(m.group(2))
                # Pop to parent level then push.
                while heading_stack and heading_stack[-1][0] >= level:
                    heading_stack.pop()
                heading_stack.append((level, text))
                current_section = text or current_section
            continue

        cb = _parse_checkbox(line)
        if cb:
            checked, text = cb
            cleaned = _strip_md_inline(text)
            items.append(
                ExtractedItem(
                    section=current_section,
                    heading_path=heading_path(),
                    text=cleaned,
                    checked=checked,
                    kind="checkbox",
                    file_paths=_extract_file_paths(cleaned),
                    indent=indent_level,
                )
            )
            continue

        num = _parse_numbered_item(line)
        if num:
            cleaned = _strip_md_inline(num)
            items.append(
                ExtractedItem(
                    section=current_section,
                    heading_path=heading_path(),
                    text=cleaned,
                    checked=None,
                    kind="numbered",
                    file_paths=_extract_file_paths(cleaned),
                    indent=indent_level,
                )
            )
            continue

        bullet = _parse_bullet_item(line)
        if bullet:
            cleaned = _strip_md_inline(bullet)
            items.append(
                ExtractedItem(
                    section=current_section,
                    heading_path=heading_path(),
                    text=cleaned,
                    checked=None,
                    kind="bullet",
                    file_paths=_extract_file_paths(cleaned),
                    indent=indent_level,
                )
            )

    return items


IdStrategy = Literal["index", "hash"]


def _task_id(prefix: str, index_1: int, *, strategy: IdStrategy, text: str) -> str:
    if strategy == "index":
        return f"{prefix}{index_1}"
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]
    return f"{prefix}{digest}"


@dataclass(frozen=True)
class Rule:
    """
    A minimal ruleset for mapping extracted items into task groups.

    - match_section_contains: if provided, section must contain any of these (case-insensitive)
    - match_heading_path_contains: if provided, any heading in the path must contain any of these (case-insensitive)
    - match_kind: optional filter on item kind
    """

    name: str
    prefix: str
    mode: Literal["pull", "push", "either"] = "either"
    action: str = "execute"
    agent: Optional[str] = None
    match_section_contains: Tuple[str, ...] = ()
    match_heading_path_contains: Tuple[str, ...] = ()
    match_kind: Tuple[Literal["checkbox", "numbered", "bullet"], ...] = ()
    exclude_section_contains: Tuple[str, ...] = ()
    exclude_heading_path_contains: Tuple[str, ...] = ()
    exclude_kind: Tuple[Literal["checkbox", "numbered", "bullet"], ...] = ()

    def matches(self, item: ExtractedItem) -> bool:
        sec = item.section.lower()
        hp = tuple(h.lower() for h in item.heading_path)

        if self.exclude_kind and item.kind in self.exclude_kind:
            return False
        if self.exclude_section_contains and any(k.lower() in sec for k in self.exclude_section_contains):
            return False
        if self.exclude_heading_path_contains:
            for h in hp:
                if any(k.lower() in h for k in self.exclude_heading_path_contains):
                    return False

        if self.match_kind and item.kind not in self.match_kind:
            return False
        if self.match_section_contains and not any(k.lower() in sec for k in self.match_section_contains):
            return False
        if self.match_heading_path_contains:
            ok = False
            for h in hp:
                if any(k.lower() in h for k in self.match_heading_path_contains):
                    ok = True
                    break
            if not ok:
                return False
        return True


def default_rules() -> List[Rule]:
    # Works reasonably for many “action plan” docs; template-specific rules can override.
    return [
        Rule(name="deliverables", prefix="D", match_section_contains=("deliverable",), match_kind=("checkbox",)),
        Rule(name="immediate", prefix="I", mode="pull", match_section_contains=("immediate",)),
        Rule(name="short_term", prefix="S", match_section_contains=("short-term", "short term")),
        Rule(name="deferred", prefix="F", match_section_contains=("deferred",)),
        Rule(name="migration", prefix="M", match_section_contains=("migration",), match_kind=("checkbox",)),
        Rule(
            name="fallback", 
            prefix="T", 
            exclude_section_contains=(
                "metadata", "overview", "objectives", "current state", "risks", "accomplishments", "decisions", 
                "rationale", "insights", "observations", "documentation", "notes"
            )
        ),
    ]


def md_to_plan(
    md_path: Path,
    *,
    plan_id: Optional[str] = None,
    goal: Optional[str] = None,
    default_agent: str = "dev-agent",
    rules: Optional[Sequence[Rule]] = None,
    id_strategy: IdStrategy = "index",
    chain_dependencies: bool = True,
) -> PlanModel:
    text = md_path.read_text(encoding="utf-8")
    extracted = extract_action_items(text)
    macro_lane, micro_lane = _extract_swim_lanes(text)

    derived_plan_id = plan_id or md_path.stem
    derived_goal = goal or f"Execute action items from {md_path.name}"
    
    tasks: List[TaskModel] = []
    
    rule_list = list(rules) if rules is not None else default_rules()
    buckets: Dict[str, Tuple[Rule, List[ExtractedItem]]] = {}
    for r in rule_list:
        buckets[r.name] = (r, [])
    
    # Stable assignment: first matching rule wins.
    for item in extracted:
        for r in rule_list:
            if r.matches(item):
                buckets[r.name][1].append(item)
                break
    
    # Task generation with hierarchy and explicit deps
    prev_tasks: Dict[int, str] = {} # indent_level -> last_task_id
    
    for r in rule_list:
        group = buckets[r.name][1]
        if not group:
            continue
        for i, item in enumerate(group, 1):
            tid = _task_id(r.prefix, i, strategy=id_strategy, text=item.text)
            
            # 1. Hierarchical Dependency: depend on the item at the level above
            deps = []
            if item.indent > 0 and (item.indent - 1) in prev_tasks:
                deps.append(prev_tasks[item.indent - 1])
            elif item.indent in prev_tasks:
                # If same level, we still chain (sequential flow within a group)
                deps.append(prev_tasks[item.indent])
                
            # 2. Explicit Dependencies: (depends: T1)
            explicit_deps = _DEPENDENCY_RE.findall(item.text)
            deps.extend(explicit_deps)
            
            tasks.append(
                TaskModel(
                    id=tid,
                    title=item.text,
                    action=r.action,
                    agent=r.agent or default_agent,
                    depends_on=list(set(deps)),
                    files=list(item.file_paths),
                    mode=r.mode,
                    macro_lane=macro_lane,
                    micro_lane=micro_lane,
                )
            )
            prev_tasks[item.indent] = tid
    
    return PlanModel(plan=PlanMetadata(id=derived_plan_id, goal=derived_goal), tasks=tasks)



def plan_to_yaml(plan: PlanModel) -> str:
    # Ensure stable key ordering in output.
    data = plan.model_dump(mode="json")
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)


def plan_to_yaml_with_header(
    plan: PlanModel,
    *,
    source_path: Optional[Path] = None,
    ruleset_path: Optional[Path] = None,
    generator: str = "dagrun",
    generator_version: Optional[str] = None,
) -> str:
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    header_lines: List[str] = [
        "# Generated by DAGrun",
        f"# generated_at_utc: {ts}",
    ]
    if generator_version:
        header_lines.append(f"# generator_version: {generator_version}")
    header_lines.append(f"# generator: {generator}")
    if source_path:
        header_lines.append(f"# source: {source_path.as_posix()}")
    if ruleset_path:
        header_lines.append(f"# ruleset: {ruleset_path.as_posix()}")
    header_lines.append("# ---")

    return "\n".join(header_lines) + "\n" + plan_to_yaml(plan)


def extracted_to_json(items: Sequence[ExtractedItem]) -> str:
    payload = [
        {
            "section": x.section,
            "heading_path": list(x.heading_path),
            "text": x.text,
            "checked": x.checked,
            "kind": x.kind,
            "file_paths": list(x.file_paths),
        }
        for x in items
    ]
    return json.dumps(payload, indent=2, ensure_ascii=False)

