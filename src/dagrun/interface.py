# Copyright (C) 2026  Rick Metz
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from typing import List, Optional, Dict, Any
from .engine import DagEngine, DagError
from .models import TaskModel, TaskStatus


class AgentInterface:
    def __init__(self, engine: DagEngine, state_manager=None):
        self.engine = engine
        self.state_manager = state_manager

    def get_next_task(self, agent_id: str) -> Optional[TaskModel]:
        ready_tasks = self.engine.get_ready_tasks()
        for task in ready_tasks:
            if task.agent == agent_id:
                task.status = TaskStatus.RUNNING
                if self.state_manager:
                    self.state_manager.save_state(self.engine.plan)
                return task
        return None

    def complete_task(self, task_id: str, result: str = "") -> bool:
        if task_id not in self.engine.tasks:
            return False
        task = self.engine.tasks[task_id]
        task.status = TaskStatus.COMPLETED
        task.result = result
        if self.state_manager:
            self.state_manager.save_state(self.engine.plan)
        return True

    def fail_task(self, task_id: str, error: str = "") -> bool:
        if task_id not in self.engine.tasks:
            return False
        task = self.engine.tasks[task_id]
        task.status = TaskStatus.FAILED
        task.result = f"Error: {error}" if error else "Error"
        if self.state_manager:
            self.state_manager.save_state(self.engine.plan)
        return True
