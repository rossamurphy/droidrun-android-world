"""
Task management utilities for AndroidWorld benchmarks.
"""

import asyncio
import logging
import random
from typing import Dict, Any, List, Tuple, Optional, Callable

# Import from AndroidWorld
from android_world import registry
from android_world.task_evals import task_eval
from android_world.env import env_launcher

logger = logging.getLogger("android_world_bench")


class TaskRegistry:
    """Manages the registry of AndroidWorld tasks."""

    def __init__(self, task_family: str = registry.TaskRegistry.ANDROID_WORLD_FAMILY):
        """Initialize the task registry.

        Args:
            task_family: The task family to use
        """
        self.task_family = task_family
        self.registry = registry.TaskRegistry()
        self.task_dict = self.registry.get_registry(family=task_family)
        self.task_id_to_name = {}
        self.task_name_to_id = {}

        # Build task ID to name mapping
        for i, task_name in enumerate(sorted(self.task_dict.keys()), 1):
            self.task_id_to_name[i] = task_name
            self.task_name_to_id[task_name] = i

        logger.info(f"Found {len(self.task_id_to_name)} tasks in registry")

    def get_task_ids(self) -> Dict[int, str]:
        """Get the mapping of task IDs to task names.

        Returns:
            Dict mapping task IDs to task names
        """
        return self.task_id_to_name

    def get_task_class(self, task_name: str) -> Optional[type]:
        """Get the task class for a task name.

        Args:
            task_name: Name of the task

        Returns:
            Task class or None if not found
        """
        return self.task_dict.get(task_name)

    def get_task_by_id(self, task_id: int) -> Optional[str]:
        """Get the task name for a task ID.

        Args:
            task_id: ID of the task

        Returns:
            Task name or None if not found
        """
        return self.task_id_to_name.get(task_id)

    def create_task_instance(
        self, task_name: str, random_seed: int = 42
    ) -> Optional[task_eval.TaskEval]:
        """Create an instance of a task.

        Args:
            task_name: Name of the task
            random_seed: Random seed for parameter generation

        Returns:
            Task instance or None if task could not be created
        """
        task_class = self.get_task_class(task_name)
        if not task_class:
            logger.warning(f"Task {task_name} not found in registry")
            return None

        try:
            # Generate random parameters
            random.seed(random_seed)
            params = task_class.generate_random_params()
            params["seed"] = random_seed

            # Create and return task instance
            task_instance = task_class(params)
            logger.info(f"Created task instance for {task_name}")
            return task_instance
        except NotImplementedError:
            logger.warning(
                f"Task {task_name} does not implement generate_random_params()"
            )
            return None
        except Exception as e:
            logger.exception(f"Error creating instance for task {task_name}: {e}")
            return None

    def filter_tasks(
        self,
        task_ids: Optional[List[int]] = None,
        task_names: Optional[List[str]] = None,
    ) -> Dict[Tuple[int, str], type]:
        """Filter tasks based on task IDs or names.

        Args:
            task_ids: List of task IDs to filter
            task_names: List of task names to filter

        Returns:
            Dictionary of filtered tasks
        """
        filtered_tasks = {}

        # Filter by task IDs
        if task_ids:
            for task_id in task_ids:
                if task_id in self.task_id_to_name:
                    task_name = self.task_id_to_name[task_id]
                    if task_name in self.task_dict:
                        filtered_tasks[(task_id, task_name)] = self.task_dict[task_name]
                    else:
                        logger.warning(
                            f"Task {task_name} (ID: {task_id}) not found in registry"
                        )
                else:
                    logger.warning(f"Task ID {task_id} not found in registry")

        # Filter by task names
        if task_names:
            for task_name in task_names:
                if task_name in self.task_dict:
                    task_id = self.task_name_to_id[task_name]
                    filtered_tasks[(task_id, task_name)] = self.task_dict[task_name]
                else:
                    logger.warning(f"Task {task_name} not found in registry")

        # If no filters applied, use all tasks
        if not filtered_tasks and not task_ids and not task_names:
            filtered_tasks = self.task_dict

        return filtered_tasks

    def create_task_suite(
        self,
        task_ids: Optional[List[int]] = None,
        task_names: Optional[List[str]] = None,
        n_combinations: int = 1,
        random_seed: int = 42,
    ) -> List[Tuple[int, str, task_eval.TaskEval]]:
        """Create a suite of tasks to benchmark.

        Args:
            task_ids: List of task IDs to include
            task_names: List of task names to include
            n_combinations: Number of parameter combinations per task
            random_seed: Random seed for reproducibility

        Returns:
            List of (task_name, task_instance) tuples
        """
        # Filter tasks based on IDs or names
        filtered_tasks = self.filter_tasks(task_ids, task_names)

        # Create task instances
        task_suite = []
        random.seed(random_seed)

        logger.info(f"Creating task suite with {len(filtered_tasks)} tasks...")

        for (task_id, task_name), task_class in filtered_tasks.items():
            for i in range(n_combinations):
                try:
                    # Generate random parameters for the task
                    params = task_class.generate_random_params()
                    # Add a seed for reproducibility
                    params["seed"] = random_seed + i
                    # Create task instance
                    task_instance = task_class(params)
                    task_suite.append((task_id, task_name, task_instance))

                    logger.info(
                        f"Created task: {task_id} {task_name} (instance {i+1}/{n_combinations})"
                    )
                except Exception as e:
                    logger.error(f"Error creating task {task_id} {task_name}: {e}")
                    continue

        logger.info(f"Created task suite with {len(task_suite)} task instances")
        return task_suite
