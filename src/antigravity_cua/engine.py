from __future__ import annotations

import asyncio
import logging
from typing import Optional, Dict, Any, AsyncIterator
import cua

from .config import CuaConfig
from .session_manager import SessionManager, SandboxSession
from .spacesd_client import SpacesDClient, ExecStreamChunk
from .exceptions import SandboxNotFoundError, LeaseExpiredError

logger = logging.getLogger(__name__)

class SandboxEngine:
    """Production sandbox orchestrator combining persistent leases, spacesd streaming, and isolation."""

    def __init__(self, config: Optional[CuaConfig] = None) -> None:
        self.config = config or CuaConfig.load()
        self.session_manager = SessionManager()
        self._cua_client: Any = None

    def _get_cua(self) -> Any:
        if self._cua_client is None:
            self._cua_client = cua.embedded().spaces()
        return self._cua_client

    async def spawn_sandbox(
        self,
        space_id: str,
        image: Optional[str] = None,
        lease_seconds: int = 900
    ) -> SandboxSession:
        """Spawn an isolated container/cloud VM with Xvfb virtual display."""
        target_image = image or self.config.default_image
        cua_client = self._get_cua()

        opts = None
        if hasattr(cua, "SpaceCreateOptions"):
            opts = cua.SpaceCreateOptions(
                name=space_id,
                image=target_image,
                on=self.config.provider if self.config.provider != "docker" else "local"
            )

        try:
            created = await cua_client.create(opts) if opts else await cua_client.create()
            raw_id = getattr(getattr(created, "space", created), "id", space_id)
            sid = str(raw_id) if isinstance(raw_id, str) else space_id
        except Exception:
            sid = space_id

        # Register in persistent SQLite lease store
        session = self.session_manager.register_session(
            space_id=sid,
            provider=self.config.provider,
            image=target_image,
            lease_seconds=lease_seconds
        )
        return session

    async def execute_command(
        self,
        space_id: str,
        command: str,
        timeout_s: float = 120.0
    ) -> Dict[str, Any]:
        """Execute command in sandbox with automatic lease extension."""
        session = self.session_manager.get_session(space_id)
        if not session:
            # Auto-spawn if not present
            session = await self.spawn_sandbox(space_id)

        # Renew lease on activity
        self.session_manager.renew_lease(space_id, extend_seconds=900)

        cua_client = self._get_cua()
        space = await cua_client.space(space_id)
        res = await space.bash(command)

        return {
            "stdout": getattr(res, "stdout", "") or "",
            "stderr": getattr(res, "stderr", "") or "",
            "exit_code": getattr(res, "exit_code", 0),
            "space_id": space_id
        }

    async def capture_virtual_screen(self, space_id: str) -> bytes:
        """Capture the Xvfb virtual framebuffer (isolated in RAM, never host screen)."""
        session = self.session_manager.get_session(space_id)
        if not session:
            raise SandboxNotFoundError(f"Sandbox {space_id} does not exist.")

        self.session_manager.renew_lease(space_id)
        cua_client = self._get_cua()
        space = await cua_client.space(space_id)
        shot = await space.screenshot()
        return getattr(shot, "image", b"")

    async def virtual_mouse_click(
        self,
        space_id: str,
        x: int,
        y: int,
        button: str = "left"
    ) -> Dict[str, Any]:
        """Send mouse click to virtual display in sandbox RAM (zero host interference)."""
        btn_map = {"left": 1, "middle": 2, "right": 3, "double": "--repeat 2 1"}
        btn_code = btn_map.get(button.lower(), 1)
        cmd = f"DISPLAY=:99 xdotool mousemove {x} {y} click {btn_code}"
        return await self.execute_command(space_id, cmd)

    async def virtual_mouse_move(self, space_id: str, x: int, y: int) -> Dict[str, Any]:
        """Move cursor inside virtual display."""
        cmd = f"DISPLAY=:99 xdotool mousemove {x} {y}"
        return await self.execute_command(space_id, cmd)

    async def virtual_keyboard_type(self, space_id: str, text: str) -> Dict[str, Any]:
        """Type text into active window in virtual display."""
        import shlex
        escaped = shlex.quote(text)
        cmd = f"DISPLAY=:99 xdotool type --delay 10 -- {escaped}"
        return await self.execute_command(space_id, cmd)

    async def virtual_keyboard_key(self, space_id: str, key: str) -> Dict[str, Any]:
        """Press special key (e.g. Return, Tab, BackSpace, Control_L+c) in virtual display."""
        import shlex
        escaped = shlex.quote(key)
        cmd = f"DISPLAY=:99 xdotool key {escaped}"
        return await self.execute_command(space_id, cmd)

    async def virtual_mouse_scroll(self, space_id: str, direction: str = "down", clicks: int = 3) -> Dict[str, Any]:
        """Scroll virtual display mouse wheel (up/down)."""
        btn = 5 if direction.lower() == "down" else 4
        cmd = f"DISPLAY=:99 xdotool click --repeat {clicks} {btn}"
        return await self.execute_command(space_id, cmd)

    async def terminate_sandbox(self, space_id: str) -> bool:
        """Explicitly destroy and release sandbox resources."""
        cua_client = self._get_cua()
        try:
            await cua_client.delete(space_id)
        except Exception as e:
            logger.warning(f"Error terminating remote space {space_id}: {e}")

        return self.session_manager.remove_session(space_id)

    async def reap_orphaned_sandboxes(self) -> int:
        """Watchdog: Automatically discover and destroy expired sandboxes to prevent cost leaks."""
        expired = self.session_manager.list_expired()
        reaped_count = 0
        cua_client = self._get_cua()

        for s in expired:
            logger.info(f"Reaping expired sandbox lease: {s.space_id} (expired {s.lease_expires_at})")
            try:
                await cua_client.delete(s.space_id)
            except Exception:
                pass
            self.session_manager.remove_session(s.space_id)
            reaped_count += 1

        return reaped_count
