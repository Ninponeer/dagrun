from typing import List, Dict, Set
from .models import PlanModel, TaskModel, TaskStatus

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

    def get_ready_tasks(self) -> List[TaskModel]:
        """
        Returns a list of tasks that are PENDING and whose dependencies are all COMPLETED.
        """
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

    def run_scheduler(self):
        """
        A simple scheduler loop that runs tasks as they become ready.
        """
        import time
        while True:
            ready_tasks = self.get_ready_tasks()
            if not ready_tasks:
                # Check if all tasks are completed
                all_completed = all(t.status == TaskStatus.COMPLETED for t in self.tasks.values())
                if all_completed:
                    break
                else:
                    # Check if any tasks failed
                    if any(t.status == TaskStatus.FAILED for t in self.tasks.values()):
                        break
                    
                    print("Waiting for tasks to become ready...")
                    time.sleep(1)
                    continue

            for task in ready_tasks:
                task.status = TaskStatus.RUNNING
                print(f"Running task: {task.id} - {task.title} (Agent: {task.agent})")
                # Simulate work
                time.sleep(0.5)
                task.status = TaskStatus.COMPLETED
                print(f"Finished task: {task.id}")

    def run(self):
        """
        Executes the tasks in the plan using the scheduler.
        """
        self.run_scheduler()

    def to_mermaid(self) -> str:
        """
        Generates a Mermaid.js graph definition of the DAG.
        """
        lines = ["graph TD"]
        for task_id, task in self.tasks.items():
            # Define the node with a label
            lines.append(f'    {task_id}["{task.id}: {task.title}"]')
            # Define dependencies as edges
            for dep in task.depends_on:
                lines.append(f"    {dep} --> {task_id}")
        return "\n".join(lines)

    def validate(self) -> bool:
        """Utility to confirm the plan is valid and executable."""
        try:
            self._validate_existence()
            self._validate_cycles()
            return True
        except DagError:
            return False
