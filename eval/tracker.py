import json
import os
from typing import Dict, Any, List
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from droidrun import DroidAgent
from pathlib import Path

logger = logging.getLogger("tracker")

"""
@dataclass
class TaskSummary:
    task_name: str
    task_idx: int
    task_id: int
    score: float
    success: bool
    steps_taken: int
    execution_time: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    trajectory_summary:


@dataclass
class Summary:
    total_tasks: int = 0
    successful_tasks: int = 0
    success_rate: float = 0.0
    tasks: List[TaskSummary] = field(default_factory=list)
    avg_steps: float = 0.0
    avg_time: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


def update_progress():
    logger.debug("Updating progress")


def update_summary():
    logger.debug("Updating summary")
"""


@dataclass
class TrajectoryItem:
    pass


@dataclass
class TrajectoryStats:
    total_steps: int = field(default=0)
    planning_steps: int = field(default=0)
    execution_steps: int = field(default=0)


# legacy result format used in web repr
@dataclass
class TaskResult:
    task_id: int
    task_name: str
    task_idx: int
    task_description: str
    max_steps: int
    success: float = field(default=0.0)
    agent_success: bool = field(default=False)
    steps_taken: int = field(default=0)
    execution_time: float = field(default=0.0)
    reasoning: bool = field(default=False)
    final_thought: str = field(default="")
    logs: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    error: str | None = field(default=None)
    trajectory: List[TrajectoryItem] = field(default_factory=list)
    trajectory_stats: TrajectoryStats = field(default_factory=TrajectoryStats)


OUTPUT_DIR = "eval_results"


def get_task_result_path(task_name: str) -> Path:
    dname = f"{task_name.replace(' ', '_')}"
    opath = Path(OUTPUT_DIR, dname)
    opath.mkdir(parents=True, exist_ok=True)
    return opath


def track_task(task_name: str, task_idx: int, goal: str, max_steps: int) -> TaskResult:
    return TaskResult(
        task_id=0,
        task_name=task_name,
        task_idx=task_idx,
        task_description=goal,
        max_steps=max_steps,
    )


def write_task_result(
    task_result: TaskResult,
    agent: DroidAgent,
    score: float = 0.0,
    agent_result: Dict[str, Any] | None = None,
    error: str | None = None,
):
    logger.debug(
        f"Writing task result for {task_result.task_name} {task_result.task_idx} with score {score}. Agent result: {json.dumps(agent_result)}"
    )

    task_result.success = score
    
    if agent_result is not None:
        task_result.agent_success = agent_result["success"]
        task_result.steps_taken = agent_result["steps"]
        task_result.final_thought = agent_result["reason"]

    if error is not None:
        task_result.error = error

    started_at = datetime.fromisoformat(task_result.timestamp)
    task_result.execution_time = (datetime.now() - started_at).total_seconds()

    task_result.logs = []
    task_result.trajectory = []
    task_result.trajectory_stats = TrajectoryStats(
        total_steps=0, execution_steps=0, planning_steps=0
    )
    task_result.reasoning = agent.reasoning

    dpath = get_task_result_path(task_result.task_name)
    fpath = dpath / "result.json"
    try:
        with open(fpath, "w") as f:
            json.dump(asdict(task_result), f, indent=2)
        logger.debug(f"Wrote task {task_result.task_name} result to {fpath}")
    except Exception as e:
        logger.error(f"Error writing task result to {fpath}: {e}")


def write_task_trajectory(task_name: str, task_idx: int, agent: DroidAgent):
    logger.debug(f"Writing task trajectory for {task_name} {task_idx}.")

    dpath = get_task_result_path(task_name)
    trk_path = agent.trajectory.save_trajectory(dpath)
    logger.debug(f"Wrote task {task_name} trajectory to {trk_path}")
