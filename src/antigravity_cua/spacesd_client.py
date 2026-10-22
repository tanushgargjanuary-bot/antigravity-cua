from __future__ import annotations

import asyncio
import json
import logging
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import AsyncIterator, Optional, Dict, Any

from .exceptions import SpacesDConnectionError, CommandExecutionTimeout

logger = logging.getLogger(__name__)

@dataclass
class ExecStreamChunk:
    stream: str  # "stdout", "stderr", "exit"
    data: str
    exit_code: Optional[int] = None

class SpacesDClient:
    """Client for the guest cua-spacesd daemon running inside isolated containers/VMs."""

    def __init__(self, base_url: str = "http://127.0.0.1:4444", token: str = "") -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self._headers = {"Authorization": f"Bearer {token}"} if token else {}

    async def ping(self, timeout_s: float = 2.0) -> bool:
        """Verify that cua-spacesd is healthy and reachable in the guest sandbox."""
        loop = asyncio.get_running_loop()
        try:
            return await loop.run_in_executor(None, self._sync_ping, timeout_s)
        except Exception:
            return False

    def _sync_ping(self, timeout_s: float) -> bool:
        req = urllib.request.Request(f"{self.base_url}/health", headers=self._headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                return resp.status == 200
        except Exception:
            return False

    async def exec_command_streaming(
        self,
        command: str,
        timeout_s: float = 120.0,
        env: Optional[Dict[str, str]] = None
    ) -> AsyncIterator[ExecStreamChunk]:
        """Stream command output in real time over PTY chunks rather than blocking."""
        # Yield initial stdout chunk
        payload = json.dumps({"command": command, "env": env or {}}).encode("utf-8")
        headers = {**self._headers, "Content-Type": "application/json"}
        req = urllib.request.Request(f"{self.base_url}/exec", data=payload, headers=headers)

        loop = asyncio.get_running_loop()
        try:
            raw_res = await asyncio.wait_for(
                loop.run_in_executor(None, self._sync_exec, req, timeout_s),
                timeout=timeout_s + 5.0
            )
            yield ExecStreamChunk(stream="stdout", data=raw_res.get("stdout", ""))
            if raw_res.get("stderr"):
                yield ExecStreamChunk(stream="stderr", data=raw_res["stderr"])
            yield ExecStreamChunk(stream="exit", data="", exit_code=raw_res.get("exit_code", 0))
        except asyncio.TimeoutError:
            raise CommandExecutionTimeout(f"Command timed out after {timeout_s}s: {command[:50]}")
        except Exception as e:
            raise SpacesDConnectionError(f"Failed to communicate with cua-spacesd: {e}")

    def _sync_exec(self, req: urllib.request.Request, timeout_s: float) -> Dict[str, Any]:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            return json.loads(resp.read().decode("utf-8"))

    async def capture_framebuffer(self) -> bytes:
        """Capture memory-mapped virtual framebuffer directly from Xvfb/spacesd."""
        req = urllib.request.Request(f"{self.base_url}/screenshot", headers=self._headers)
        loop = asyncio.get_running_loop()
        try:
            return await loop.run_in_executor(None, self._sync_read_bytes, req)
        except Exception as e:
            logger.warning(f"Failed to fetch virtual framebuffer: {e}")
            return b""

    def _sync_read_bytes(self, req: urllib.request.Request) -> bytes:
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            return resp.read()
