"""
Keepalive service for the DroidRun accessibility overlay.

This module provides functionality to continuously disable the overlay of the
DroidRun accessibility service, which is necessary for some tasks.
"""

import os
import sys
import time
import logging
import asyncio
import subprocess
from typing import Optional

logger = logging.getLogger("droidrun-portal")


class OverlayKeepalive:
    """Manages the keepalive service for disabling the DroidRun overlay."""

    def __init__(
        self,
        adb_path: str = "adb",
        device_serial: Optional[str] = None,
        interval: int = 5,
    ):
        """Initialize the keepalive service.

        Args:
            adb_path: Path to ADB executable
            device_serial: Device serial number
            interval: Interval in seconds between commands
        """
        self.adb_path = adb_path
        self.device_serial = device_serial
        self.interval = interval
        self.process = None
        self.running = False

    def start(self):
        """Start the keepalive service as a subprocess."""
        if self.process and self.process.poll() is None:
            logger.info("Keepalive service is already running")
            return

        # Path to the script file
        script_path = os.path.join(os.path.dirname(__file__), "keepalive_script.py")

        # Build command
        cmd = [sys.executable, script_path]
        if self.adb_path:
            cmd.extend(["--adb-path", self.adb_path])
        if self.device_serial:
            cmd.extend(["--device-serial", self.device_serial])
        cmd.extend(["--interval", str(self.interval)])

        # Start the process
        try:
            logger.info(f"Starting keepalive service with interval {self.interval}s")
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
            self.running = True
            logger.info(f"Keepalive service started (PID: {self.process.pid})")
        except Exception as e:
            logger.error(f"Failed to start keepalive service: {e}")

    def stop(self):
        """Stop the keepalive service."""
        if not self.process:
            logger.info("No keepalive service to stop")
            return

        try:
            logger.info("Stopping keepalive service")
            self.process.terminate()

            # Wait for process to terminate
            try:
                self.process.wait(timeout=5)
                logger.info("Keepalive service stopped")
            except subprocess.TimeoutExpired:
                logger.warning(
                    "Keepalive service did not terminate gracefully, killing..."
                )
                self.process.kill()
                self.process.wait()
                logger.info("Keepalive service killed")

            self.process = None
            self.running = False
        except Exception as e:
            logger.error(f"Error stopping keepalive service: {e}")


async def disable_overlay_once(adb_path: str, device_serial: str):
    """Disable the overlay once.

    Args:
        adb_path: Path to ADB executable
        device_serial: Device serial number
    """
    try:
        cmd = [
            adb_path,
            "-s",
            device_serial,
            "shell",
            "am broadcast -a com.droidrun.portal.TOGGLE_OVERLAY --ez overlay_visible false",
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        await process.communicate()
        logger.debug("Disabled overlay once")
        return True
    except Exception as e:
        logger.error(f"Failed to disable overlay: {e}")
        return False
