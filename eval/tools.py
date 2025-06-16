from droidrun.tools import Tools
import asyncio
from typing import List, Optional, Dict, Any, Tuple
from eval.android_env_client import AndroidEnvClient
from android_world.env import json_action, representation_utils
import logging
from PIL import Image
import io

logger = logging.getLogger(__name__)


class AndroidWorldTools(Tools):
    def __init__(self, client: Optional[AndroidEnvClient] = None) -> None:
        self.client = client or AndroidEnvClient()
        self.memory: List[str] = []
        self.success: Optional[bool] = None
        self.reason: Optional[str] = None
        self.finished: bool = False
        self._clickables_cache: List[representation_utils.UIElement] = []

    async def get_clickables(self) -> str:
        """
        Return an indexed list of clickable elements from the a11y tree.
        """
        try:
            elements = await asyncio.to_thread(self.client.get_elements)
            self._clickables_cache = [
                el
                for el in elements
                if el.is_clickable
                or el.is_long_clickable
                or el.is_checkable
                or el.is_focusable
                or el.is_editable
            ]
            if not self._clickables_cache:
                return "No clickable elements found."
            return [
                {
                    "index": i,
                    "text": el.text,
                    "className": el.class_name,
                    "bounds": f"{el.bbox_pixels.x_min},{el.bbox_pixels.y_min},{el.bbox_pixels.x_max},{el.bbox_pixels.y_max}",
                    "resourceId": el.resource_id,
                }
                for i, el in enumerate(self._clickables_cache)
            ]

        except Exception as e:
            logger.exception("Error in get_clickables")
            return f"Error retrieving clickables: {e}"

    async def tap_by_index(self, index: int) -> bool:
        """
        Tap the clickable element at the given index using its center coordinates.
        """
        try:
            if index < 0 or index >= len(self._clickables_cache):
                logger.error(f"Invalid clickable index: {index}")
                return False
            el = self._clickables_cache[index]
            if not el.bbox_pixels:
                logger.error(f"Clickable element at index {index} has no bbox_pixels.")
                return False
            x, y = el.bbox_pixels.center
            action = json_action.JSONAction(action_type="click", x=int(x), y=int(y))
            await asyncio.to_thread(self.client.execute_action, action)
            return True
        except Exception as e:
            logger.exception(f"Error in tap_by_index: {e}")
            return False

    async def tap_by_coordinates(self, x: int, y: int) -> bool:
        """
        Tap on the device screen at specific coordinates using AndroidEnvClient.
        """
        action = json_action.JSONAction(action_type="click", x=x, y=y)
        try:
            await asyncio.to_thread(self.client.execute_action, action)
            return True
        except Exception:
            return False

    async def swipe(
        self, start_x: int, start_y: int, end_x: int, end_y: int, duration_ms: int = 300
    ) -> bool:
        """
        Perform a swipe gesture using AndroidEnvClient.
        """

        def get_swipe_direction(start_x, start_y, end_x, end_y):
            dx = end_x - start_x
            dy = end_y - start_y
            if abs(dx) > abs(dy):
                # Horizontal swipe
                if dx > 0:
                    return "right"
                else:
                    return "left"
            else:
                # Vertical swipe
                if dy < 0:
                    return "down"
                else:
                    return "up"

        action = json_action.JSONAction(
            action_type="scroll",
            direction=get_swipe_direction(start_x, start_y, end_x, end_y),
            # The backend expects x/y for start, end_x/end_y for end, but JSONAction only supports x/y.
            # If the backend expects direction, this may need to be adapted.
        )
        # The current JSONAction class does not support end_x/end_y directly, so this may need backend support.
        # For now, we only send start_x/start_y.
        try:
            await asyncio.to_thread(self.client.execute_action, action)
            return True
        except Exception:
            return False

    async def input_text(self, text: str) -> bool:
        """
        Input text using AndroidEnvClient.
        """
        action = json_action.JSONAction(action_type="input_text", text=text)
        try:
            await asyncio.to_thread(self.client.execute_action, action)
            return True
        except Exception:
            return False

    async def back(self) -> bool:
        """
        Press the back key using AndroidEnvClient.
        """
        action = json_action.JSONAction(action_type="navigate_back")
        try:
            await asyncio.to_thread(self.client.execute_action, action)
            return True
        except Exception:
            return False

    async def press_key(self, keycode: int) -> bool:
        """
        Press a key by keycode using AndroidEnvClient.
        """

        if keycode == 3:
            return await self.back()
        #elif keycode != 66:
        #    raise ValueError(f"Unsupported keycode: {keycode}. Valid keycodes are 3 (back) and 66 (enter).")
        elif keycode == 66:
            action = json_action.JSONAction(action_type="press_keyboard", keycode=keycode)
    
        else:
            action = json_action.JSONAction(action_type="press_keyboard", keycode=keycode)

        await asyncio.to_thread(self.client.execute_action, action)
        return True
    
    async def start_app(self, package: str, activity: str = "") -> bool:
        """
        Start an app by package name using AndroidEnvClient.
        """
        action = json_action.JSONAction(action_type="open_app", app_name=package)
        try:
            await asyncio.to_thread(self.client.execute_action, action)
            return True
        except Exception:
            return False

    async def take_screenshot(self) -> Tuple[str, bytes]:
        """
        Take a screenshot using AndroidEnvClient.
        """
        arr = await asyncio.to_thread(self.client.get_screenshot)
        img = Image.fromarray(arr, "RGB")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return ("image/png", buf.getvalue())

    async def get_phone_state(self) -> Dict[str, Any]:
        """
        Not implemented: No backend support for phone state.
        """
        return {}

    async def list_packages(self, include_system_apps: bool = False) -> List[str]:
        """
        List all packages on the device.
        """
        return await asyncio.to_thread(self.client.get_packages)

    async def remember(self, information: str) -> str:
        """
        Store important information to memory (copied from AdbTools).
        """
        if not information or not isinstance(information, str):
            return "Error: Please provide valid information to remember."
        self.memory.append(information.strip())
        max_memory_items = 10
        if len(self.memory) > max_memory_items:
            self.memory = self.memory[-max_memory_items:]
        return f"Remembered: {information}"

    async def get_memory(self) -> List[str]:
        """
        Retrieve all stored memory items (copied from AdbTools).
        """
        return self.memory.copy()

    async def extract(self, filename: Optional[str] = None) -> str:
        """
        Not implemented: No backend support for extract.
        """
        raise NotImplementedError("extract is not implemented in AndroidWorldTools.")

    def complete(self, success: bool, reason: str = "") -> bool:
        """
        Mark the task as finished (copied from AdbTools).
        """
        if success:
            self.success = True
            self.reason = reason or "Task completed successfully."
            self.finished = True
        else:
            self.success = False
            if not reason:
                raise ValueError("Reason for failure is required if success is False.")
            self.reason = reason
            self.finished = True
        return self.finished


async def test():
    env = AndroidEnvClient(base_url="http://localhost:5005")
    tools = AndroidWorldTools(env)
    await tools.swipe(540, 2200, 540, 200)
    # env.close()


if __name__ == "__main__":
    asyncio.run(test())
