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

from enum import Enum
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

class SchedulingMode(str, Enum):
    PULL = "pull"
    PUSH = "push"
    EITHER = "either"

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskModel(BaseModel):
    id: str = Field(..., description="Unique task identifier")
    title: str = Field(..., description="Short description of the task")
    action: str = Field(..., description="Verb or action token understood by the agent")
    agent: str = Field(..., description="Agent responsible for the task")
    depends_on: List[str] = Field(default_factory=list, description="IDs of tasks that must complete first")
    files: List[str] = Field(default_factory=list, description="Relevant file paths")
    mode: Literal["pull", "push", "either"] = Field(default="either", description="Scheduling mode")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Current status of the task")
    verification_cmd: Optional[str] = Field(default=None, description="Shell command to verify task completion")
    result: Optional[str] = Field(default=None, description="Stored result or output of the task execution")
    macro_lane: Optional[str] = Field(default=None, description="Macro swim lane for architectural organization")
    micro_lane: Optional[str] = Field(default=None, description="Micro swim lane for specialized tracking")

class PlanMetadata(BaseModel):
    id: str = Field(..., description="Unique plan identifier")
    goal: str = Field(..., description="High-level purpose of the plan")

class PlanModel(BaseModel):
    plan: PlanMetadata
    tasks: List[TaskModel]
