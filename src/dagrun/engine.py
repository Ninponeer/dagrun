from typing import List, Dict, Set
from .models import PlanModel, TaskModel

class DagError(Exception):
    """Specific error for DAG-related issues (cycles, missing dependencies)."""
    pass

class DagEngine:
    def __init__(self, plan: PlanModel):
        self.plan = plan
        self._validate_unique_task_ids()
        self.tasks = {t.id: t for t in plan.tasks}
        self.graph = {t.id: t.depends_on for t in plan.tasks}
        self._validate_existence()
        self._validate_cycles()

    def _validate_unique_task_ids(self):
        """Ensures all task IDs are unique (no silent overwrites)."""
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
        """Ensures all referenced dependencies actually exist in the plan."""
        for task_id, deps in self.graph.items():
            for dep in deps:
                if dep not in self.tasks:
                    raise DagError(f"Task '{task_id}' depends on non-existent task '{dep}'")

    def _validate_cycles(self):
        """Detects if there are any circular dependencies in the graph."""
        visited: Set[str] = set()
        path: Set[str] = set()

        def visit(u: str):
            if u in path:
                # Trace the cycle for better error reporting
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
        """
        Returns a valid execution order for the tasks based on their dependencies.
        Uses Kahn's algorithm for topological sorting.
        """
        in_degree = {t_id: len(deps) for t_id, deps in self.graph.items()}
        queue = [t_id for t_id, deg in in_degree.items() if deg == 0]
        order = []

        # Build reverse graph for efficient dependent lookup
        reverse_graph: Dict[str, List[str]] = {t_id: [] for t_id in self.tasks}
        for t_id, deps in self.graph.items():
            for dep in deps:
                reverse_graph[dep].append(t_id)

        while queue:
            # Sort to ensure deterministic output for equal priority tasks
            queue.sort()
            u = queue.pop(0)
            order.append(u)
            for v in reverse_graph[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)
        
        return order

    def validate(self) -> bool:
        """Utility to confirm the plan is valid and executable."""
        try:
            self._validate_existence()
            self._validate_cycles()
            return True
        except DagError:
            return False
