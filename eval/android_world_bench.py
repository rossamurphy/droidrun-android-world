import argparse
import asyncio
import logging
import time
import textwrap

from eval.tools import AndroidWorldTools
from eval.android_env_client import AndroidEnvClient
from droidrun import DroidAgent, load_llm

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("android_world_bench")
logger.level = logging.DEBUG
logging.getLogger("droidrun").level = logging.DEBUG


class AndroidWorldBenchmark:
    def __init__(
        self,
        base_url: str = "http://localhost:5000",
    ) -> None:
        logger.info(f"Initializing AndroidWorldBenchmark with env base_url: {base_url}")
        self.env = AndroidEnvClient(base_url)
        self.tools = AndroidWorldTools(self.env)

    def wait_for_env(self):
        while True:
            if not self.env.health():
                print("Environment is not healthy, waiting for 1 second...")
                time.sleep(1)
            else:
                break

    def list_tasks(self):
        logger.info("Listing tasks...")
        tasks = self.env.get_suite_task_list(-1)
        for i, task in enumerate(tasks):
            logger.info(f"{i}: {task}")

    async def run(
        self,
        # droidrun params
        llm_provider: str,
        llm_model: str,
        reasoning: bool = True,
        temperature: float = 0.5,
        tracing: bool = False,
        debug: bool = False,
        # suite params
        n_task_combinations: int = 1,
        seed: int = 42,
        task_family: str = "android_world",
        max_steps_multiplier: int = 15,
    ):
        self.env.reset(go_home=True)
        logger.info(
            f"Reinitializing suite {task_family} with {n_task_combinations} combinations and seed {seed}"
        )
        self.env.reinitialize_suite(
            n_task_combinations=n_task_combinations, seed=seed, task_family=task_family
        )
        logger.debug("Suite reinitialized successfully")

        logger.debug("Fetching task list...")
        task_list = self.env.get_suite_task_list(-1)
        logger.info(f"Found {len(task_list)} tasks")
        logger.debug("Loading LLM...")
        llm = load_llm(llm_provider, model=llm_model)
        logger.debug("LLM loaded successfully")

        for task_name in task_list:
            num_tasks = self.env.get_suite_task_length(task_name)

            for task_idx in range(num_tasks):
                task_goal = self.env.get_task_goal(task_name, task_idx)
                task_complexity = self.env.get_task_complexity(task_name, task_idx)

                max_steps = task_complexity * max_steps_multiplier
                max_retries = max_steps / 10
                timeout = task_complexity * 300

                logger.info(
                    f"Initializing Task {task_name} {task_idx} | {task_complexity} -> {max_steps} | {task_goal} within {timeout} seconds"
                )

                try:
                    self.env.initialize_task(task_name, task_idx)
                    logger.debug("Task initialized successfully")
                except Exception as e:
                    logger.error(f"Error initializing task {task_name} {task_idx}: {e}")
                    logger.info("Continuing to next task...")
                    continue

                logger.info(
                    f"Initializing DroidAgent with {max_steps} steps, {max_retries} retries, and {timeout} timeout"
                )

                agent = DroidAgent(
                    task_goal,
                    llm,
                    self.tools,
                    reasoning=reasoning,
                    enable_tracing=tracing,
                    debug=debug,
                    max_steps=max_steps,
                    max_retries=max_retries,
                    timeout=timeout,
                )

                logger.debug("DroidAgent initialized successfully")

                try:
                    logger.info("Running DroidAgent...")
                    res = await agent.run()
                    logger.debug("DroidAgent completed successfully")
                except Exception as e:
                    logger.error(f"Error completing task {task_name} {task_idx}: {e}")
                    logger.info("Continuing to next task...")
                    continue

                try:
                    self.env.tear_down_task(task_name, task_idx)
                except Exception as e:
                    logger.error(f"Error tearing down task {task_name} {task_idx}: {e}")
                    logger.info("Continuing to next task...")
                    continue

                self.env.reset(go_home=True)


def main():
    """Main entry point for the benchmark script."""
    parser = argparse.ArgumentParser(
        description="Run AndroidWorld benchmark tasks with DroidRun"
    )

    # Benchmark environment configuration
    env_group = parser.add_argument_group("Benchmark Environment Configuration")
    env_group.add_argument(
        "--base-url",
        type=str,
        default="http://localhost:5000",
        help="Base URL for the Android environment",
    )

    # Task selection arguments
    task_group = parser.add_argument_group("Task Selection")
    # task_group.add_argument(
    #    "--task-ids", type=int, nargs="+", help="Task IDs to run (1-116)"
    # )
    # task_group.add_argument(
    #    "--task-names", type=str, nargs="+", help="Task names to run"
    # )
    task_group.add_argument(
        "--list-tasks", action="store_true", help="List available tasks and exit"
    )
    task_group.add_argument(
        "--n-task-combinations",
        type=int,
        default=1,
        help="Number of parameter combinations per task",
    )

    # LLM configuration
    droidrun_group = parser.add_argument_group("Droidrun Configuration")
    droidrun_group.add_argument(
        "--llm-provider",
        type=str,
        default="Gemini",
        help="LLM provider (OpenAI, Anthropic, Gemini, etc.)",
    )
    droidrun_group.add_argument(
        "--llm-model",
        type=str,
        default="models/gemini-2.5-pro-preview-06-05",
        help="Model name to use",
    )
    droidrun_group.add_argument(
        "--temperature", type=float, default=0.2, help="Temperature for LLM sampling"
    )
    droidrun_group.add_argument(
        "--reasoning", action="store_true", help="Enable reasoning for LLM"
    )
    droidrun_group.add_argument(
        "--tracing",
        action="store_true",
        help="Enable tracing for Droidrun",
    )
    droidrun_group.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode for Droidrun",
    )

    # Benchmark configuration
    suite_group = parser.add_argument_group("Benchmark Suite Configuration")
    suite_group.add_argument(
        "--seed", type=int, default=42, help="Random seed for reproducibility"
    )
    suite_group.add_argument(
        "--task-family",
        type=str,
        default="android_world",
        help="Task family to run",
    )
    suite_group.add_argument(
        "--max-step-multiplier",
        type=int,
        default=15,
        help="Used to calculate max steps",
    )

    """suite_group.add_argument(
        "--results-dir",
        type=str,
        default="eval_results",
        help="Directory to save results",
    )"""

    args = parser.parse_args()

    # Create benchmark instance
    benchmark = AndroidWorldBenchmark(
        base_url=args.base_url,
    )
    benchmark.wait_for_env()

    # Just list tasks if requested
    if args.list_tasks:
        benchmark.list_tasks()
        return

    logger.info(
        textwrap.dedent(
            """

  ██████╗ ██████╗  ██████╗ ██╗██████╗ ██████╗ ██╗   ██╗███╗   ██╗
  ██╔══██╗██╔══██╗██╔═══██╗██║██╔══██╗██╔══██╗██║   ██║████╗  ██║
  ██║  ██║██████╔╝██║   ██║██║██║  ██║██████╔╝██║   ██║██╔██╗ ██║
  ██║  ██║██╔══██╗██║   ██║██║██║  ██║██╔══██╗██║   ██║██║╚██╗██║
  ██████╔╝██║  ██║╚██████╔╝██║██████╔╝██║  ██║╚██████╔╝██║ ╚████║
  ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝ Android World Benchmark
"""
        )
    )

    # Run the benchmark
    asyncio.run(
        benchmark.run(
            # droidrun params
            llm_provider=args.llm_provider,
            llm_model=args.llm_model,
            reasoning=args.reasoning,
            temperature=args.temperature,
            tracing=args.tracing,
            debug=args.debug,
            # suite params
            n_task_combinations=args.n_task_combinations,
            seed=args.seed,
            task_family=args.task_family,
            max_steps_multiplier=args.max_step_multiplier,
        )
    )


if __name__ == "__main__":
    main()
