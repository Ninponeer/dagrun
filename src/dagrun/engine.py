from typing import List, Dict, Set, Optional
from .models import PlanModel, TaskModel, TaskStatus

class DagError(Exception):
    """Specific error for DAG-related issues (cycles, missing dependencies)."""
    pass

class DagEngine:
    def __init__(self, plan: PlanModel, state_manager=None):
        self.plan = plan
        self.state_manager = state_manager
        self._validate_unique_task_ids()
        self.tasks = {t.id: t for t in plan.tasks}
        self.graph = {t.id: t.depends_on for t in plan.tasks}
        self._validate_existence()
        self._validate_cycles()
        
        if self.state_manager:
            self.state_manager.save_state(self.plan)

    def _validate_unique_task_ids(self):
        seen: Set[str] = set()
        duplicates: Set[str] = set()
        for t in self.plan.tasks:
            if t.id in seen:
                duplicates.add(t.id)
            seen.add(t.id)
        if duplicates:
            dup_list = ", ".join(sorted(duplicates))
            raise DagError(f"Duplicate task id(s) found: {dup_list}")

    def _validate_existence(self):
        for task_id, deps in self.graph.items():
            for dep in deps:
                if dep not in self.tasks:
                    raise DagError(f"Task '{task_id}' depends on non-existent task '{dep}'")

    def _validate_cycles(self):
        visited: Set[str] = set()
        path: Set[str] = set()

        def visit(u: str):
            if u in path:
                raise DagError(f"Cycle detected involving task '{u}'")
            if u in visited:
                return
            path.add(u)
            for v in self.graph.get(u, []):
                visit(v)
            path.remove(u)
            visited.add(u)

        for task_id in self.tasks:
            if task_id not in visited:
                visit(task_id)

    def get_execution_order(self) -> List[str]:
        in_degree = {t_id: len(deps) for t_id, deps in self.graph.items()}
        queue = [t_id for t_id, deg in in_degree.items() if deg == 0]
        order = []

        reverse_graph: Dict[str, List[str]] = {t_id: [] for t_id in self.tasks}
        for t_id, deps in self.graph.items():
            for dep in deps:
                reverse_graph[dep].append(t_id)

        while queue:
            queue.sort()
            u = queue.pop(0)
            order.append(u)
            for v in reverse_graph[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)
        
        return order

    def get_ready_tasks(self) -> List[TaskModel]:
        ready_tasks = []
        for task in self.tasks.values():
            if task.status == TaskStatus.PENDING:
                deps_completed = all(
                    self.tasks[dep_id].status == TaskStatus.COMPLETED
                    for dep_id in task.depends_on
                )
                if deps_completed:
                    ready_tasks.append(task)
        return ready_tasks

    def invalidate_task(self, task_id: str):
        if task_id not in self.tasks:
            raise DagError(f"Task '{task_id}' not found in plan.")

        reverse_graph: Dict[str, List[str]] = {t_id: [] for t_id in self.tasks}
        for t_id, deps in self.graph.items():
            for dep in deps:
                reverse_graph[dep].append(t_id)

        visited = set()
        stack = [task_id]
        while stack:
            u = stack.pop()
            if u not in visited:
                visited.add(u)
                self.tasks[u].status = TaskStatus.PENDING
                stack.extend(reverse_graph.get(u, []))
        
        return visited

    def invalidate_lane(self, macro_lane: str, micro_lane: Optional[str] = None) -> Set[str]:
        impacted_tasks = set()
        for task in self.tasks.values():
            if task.macro_lane == macro_lane:
                if micro_lane is None or task.micro_lane == micro_lane:
                    impacted_tasks.update(self.invalidate_task(task.id))
        
        return impacted_tasks

    def get_impacted_tasks(self, task_id: str) -> Set[str]:
        import copy
        temp_engine = copy.deepcopy(self)
        return temp_engine.invalidate_task(task_id)

    def get_impacted_lanes(self, task_id: str) -> Set[str]:
        impacted = self.get_impacted_tasks(task_id)
        lanes = set()
        for tid in impacted:
            lane = self.tasks[tid].macro_lane
            if lane:
                lanes.add(lane)
        return lanes

    def to_mermaid(self) -> str:
        lines = ["graph TD"]
        lanes: Dict[str, List[TaskModel]] = {}
        for task in self.tasks.values():
            lane = task.macro_lane or "Uncategorized"
            lanes.setdefault(lane, []).append(task)
        
        for lane_name, tasks in lanes.items():
            safe_lane_id = lane_name.replace(" ", "_").replace("🌌", "").replace("🌉", "").replace("🎨", "").replace("⚔️", "").replace("📜", "").strip()
            lines.append(f'    subgraph {safe_lane_id} ["{lane_name}"]')
            for task in tasks:
                status_prefix = "✅ " if task.status == TaskStatus.COMPLETED else "⏳ " if task.status == TaskStatus.PENDING else "⚙️ "
                lines.append(f'        {task.id}["{status_prefix}{task.id}: {task.title}"]')
            lines.append("    end")
        
        for task_id, task in self.tasks.items():
            for dep in task.depends_on:
                lines.append(f"    {dep} --> {task_id}")
        
        return "\n".join(lines)

    def validate(self) -> bool:
        try:
            self._validate_existence()
            self._validate_cycles()
            return True
        except DagError:
            return False
