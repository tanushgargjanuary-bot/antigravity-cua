from __future__ import annotations

import asyncio
from typing import Any, Optional
import cua

class SpacesManager:
    """Manages Cua Spaces lifecycle and tool execution in isolated environments."""

    def __init__(self) -> None:
        self._spaces: Any = None
        self._active_spaces: dict[str, Any] = {}

    def _get_client(self) -> Any:
        if self._spaces is None:
            self._spaces = cua.embedded().spaces()
        return self._spaces

    async def get_or_create(self, space_id: str = "antigravity-sandbox", image: str = "linux", on: str = "") -> Any:
        if space_id in self._active_spaces:
            return self._active_spaces[space_id]

        client = self._get_client()
        try:
            space = await client.space(space_id)
            self._active_spaces[space_id] = space
            return space
        except Exception:
            opts = cua.SpaceCreateOptions(name=space_id, image=image, on=on) if hasattr(cua, "SpaceCreateOptions") else None
            created = await client.create(opts) if opts else await client.create()
            sid = getattr(getattr(created, "space", created), "id", space_id)
            space = await client.space(sid)
            self._active_spaces[space_id] = space
            return space

    async def run_bash(self, command: str, space_id: str = "antigravity-sandbox") -> dict[str, Any]:
        space = await self.get_or_create(space_id)
        res = await space.bash(command)
        return {
            "stdout": getattr(res, "stdout", "") or "",
            "stderr": getattr(res, "stderr", "") or "",
            "exit_code": getattr(res, "exit_code", 0)
        }

    async def write_file(self, path: str, content: str, space_id: str = "antigravity-sandbox") -> str:
        space = await self.get_or_create(space_id)
        await space.write(path, content.encode("utf-8"))
        return f"Wrote {len(content)} bytes to {path} in space '{space_id}'."

    async def take_screenshot(self, space_id: str = "antigravity-sandbox") -> bytes:
        space = await self.get_or_create(space_id)
        shot = await space.screenshot()
        return getattr(shot, "image", b"")

    async def destroy_space(self, space_id: str = "antigravity-sandbox") -> str:
        if space_id in self._active_spaces:
            client = self._get_client()
            await client.delete(space_id)
            del self._active_spaces[space_id]
            return f"Space '{space_id}' deleted."
        return f"Space '{space_id}' not found."
