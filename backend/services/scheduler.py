# backend/services/scheduler.py

import os
import asyncio
from utils import configure_logging, handle_exceptions, log_execution_time, timeout
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

# Initialize logger
logger = configure_logging()

class SchedulerService:
    """
    Manages scheduling tasks for the AI system, allowing for periodic tasks to be performed.
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        try:
            self.scheduler.start()
            logger.info("Scheduler started successfully.")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
        self.default_job_interval = int(os.getenv("DEFAULT_JOB_INTERVAL", 60))

    @handle_exceptions(default_return_value=None)
    @log_execution_time(threshold=0.5)
    def add_cron_job(self, job_function, cron_expression: str, job_id: str):
        """
        Add a cron job to the scheduler.

        Args:
            job_function (callable): The function to be executed.
            cron_expression (str): The cron expression for the job's schedule.
            job_id (str): The unique identifier for the job.

        Returns:
            Job: The job that was added to the scheduler.
        """
        try:
            trigger = CronTrigger.from_crontab(cron_expression)
            job = self.scheduler.add_job(job_function, trigger, id=job_id, replace_existing=True)
            logger.info(f"Cron job {job_id} added successfully with schedule: {cron_expression}")
            return job
        except Exception as e:
            logger.error(f"Failed to add cron job {job_id}: {e}")
            return None

    @handle_exceptions(default_return_value=None)
    @log_execution_time(threshold=0.5)
    def add_interval_job(self, job_function, interval_minutes: int = None, job_id: str = None):
        """
        Add an interval job to the scheduler.

        Args:
            job_function (callable): The function to be executed.
            interval_minutes (int, optional): The interval in minutes between job executions. Defaults to DEFAULT_JOB_INTERVAL.
            job_id (str, optional): The unique identifier for the job.

        Returns:
            Job: The job that was added to the scheduler.
        """
        try:
            interval_minutes = interval_minutes or self.default_job_interval
            if interval_minutes <= 0:
                raise ValueError("Interval minutes must be a positive integer.")
            trigger = IntervalTrigger(minutes=interval_minutes)
            job = self.scheduler.add_job(job_function, trigger, id=job_id, replace_existing=True)
            logger.info(f"Interval job {job_id} added successfully with interval: {interval_minutes} minutes")
            return job
        except Exception as e:
            logger.error(f"Failed to add interval job {job_id}: {e}")
            return None

    @handle_exceptions(default_return_value=False)
    @log_execution_time(threshold=0.5)
    def remove_job(self, job_id: str) -> bool:
        """
        Remove a job from the scheduler.

        Args:
            job_id (str): The unique identifier for the job.

        Returns:
            bool: True if the job was successfully removed, False otherwise.
        """
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Job {job_id} removed successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to remove job {job_id}: {e}")
            return False

    @handle_exceptions(default_return_value=False)
    @log_execution_time(threshold=0.5)
    async def schedule_one_time_task(self, job_function, delay_seconds: int, job_id: str = None) -> bool:
        """
        Schedule a one-time task to run after a delay.

        Args:
            job_function (callable): The function to be executed.
            delay_seconds (int): Delay in seconds before executing the job.
            job_id (str, optional): The unique identifier for the job.

        Returns:
            bool: True if the job was successfully scheduled, False otherwise.
        """
        try:
            if delay_seconds < 0:
                raise ValueError("Delay seconds must be a non-negative integer.")
            await asyncio.sleep(delay_seconds)
            try:
                await job_function()
                logger.info(f"One-time task {job_id} executed successfully after {delay_seconds} seconds.")
            except Exception as e:
                logger.error(f"Error occurred while executing job function for task {job_id}: {e}")
            return True
        except Exception as e:
            logger.error(f"Failed to execute one-time task {job_id}: {e}")
            return False

# Example usage
if __name__ == "__main__":
    scheduler_service = SchedulerService()

    async def example_task():
        logger.info("Executing example task.")

    # Adding a cron job
    scheduler_service.add_cron_job(example_task, "0 0 * * *", "daily_task")

    # Adding an interval job
    scheduler_service.add_interval_job(example_task, interval_minutes=10, job_id="interval_task")

    # Scheduling a one-time task
    asyncio.run(scheduler_service.schedule_one_time_task(example_task, delay_seconds=5, job_id="one_time_task"))

    try:
        # Keeping the scheduler alive
        asyncio.run(asyncio.Event().wait())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down the scheduler...")
        scheduler_service.scheduler.shutdown()
