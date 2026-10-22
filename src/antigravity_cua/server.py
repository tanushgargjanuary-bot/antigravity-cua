from __future__ import annotations

import asyncio
try:
    from mcp.server.mcpserver import MCPServer as FastMCP
except (ImportError, ModuleNotFoundError):
    try:
        from mcp.server.fastmcp import FastMCP
    except (ImportError, ModuleNotFoundError):
        class FastMCP:  # type: ignore
            def __init__(self, name: str):
                self.name = name
            def tool(self, *args, **kwargs):
                def decorator(fn):
                    return fn
                return decorator
            def run(self):
                pass

from .engine import SandboxEngine
from .config import CuaConfig

mcp = FastMCP("Antigravity CUA Production Bridge")
engine = SandboxEngine()

@mcp.tool()
async def cua_spawn_sandbox(
    space_id: str = "antigravity-sandbox",
    image: str = "ghcr.io/trycua/linux:24.04-slim",
    lease_minutes: int = 15
) -> str:
    """Spawn an isolated headless sandbox (Xvfb virtual display in RAM).
    Guarantees zero physical monitor popups, zero host focus changes.
    """
    session = await engine.spawn_sandbox(space_id, image, lease_seconds=lease_minutes * 60)
    return f"Sandbox spawned: id={session.space_id}, provider={session.provider}, lease={lease_minutes}m, status={session.status}"

@mcp.tool()
async def cua_exec_isolated(
    command: str,
    space_id: str = "antigravity-sandbox",
    timeout_seconds: int = 120
) -> str:
    """Execute shell commands inside the isolated sandbox container.
    Renews the lease automatically upon execution. Never touches host files.
    """
    res = await engine.execute_command(space_id, command, timeout_s=float(timeout_seconds))
    out = res["stdout"]
    if res["stderr"]:
        out += f"\n[stderr]\n{res['stderr']}"
    return out or f"(Command exited with code {res['exit_code']} and no output)"

@mcp.tool()
async def cua_capture_virtual_screen(space_id: str = "antigravity-sandbox") -> bytes:
    """Capture the virtual Xvfb framebuffer directly from the sandbox RAM.
    Guaranteed off-host: captures the sandbox's virtual display, not the user's desktop.
    """
    return await engine.capture_virtual_screen(space_id)

@mcp.tool()
async def cua_mouse_click(
    x: int,
    y: int,
    button: str = "left",
    space_id: str = "antigravity-sandbox"
) -> str:
    """Perform a mouse click (left, right, middle, double) at coordinates (x, y) on the virtual display."""
    res = await engine.virtual_mouse_click(space_id, x, y, button=button)
    return f"Clicked {button} at ({x}, {y}) on virtual display in sandbox '{space_id}'."

@mcp.tool()
async def cua_mouse_move(
    x: int,
    y: int,
    space_id: str = "antigravity-sandbox"
) -> str:
    """Move the virtual mouse pointer to (x, y) on the virtual display."""
    await engine.virtual_mouse_move(space_id, x, y)
    return f"Moved cursor to ({x}, {y}) on virtual display in sandbox '{space_id}'."

@mcp.tool()
async def cua_keyboard_type(
    text: str,
    space_id: str = "antigravity-sandbox"
) -> str:
    """Type text into the active window on the virtual display."""
    await engine.virtual_keyboard_type(space_id, text)
    return f"Typed '{text[:20]}...' into virtual display in sandbox '{space_id}'."

@mcp.tool()
async def cua_keyboard_key(
    key: str,
    space_id: str = "antigravity-sandbox"
) -> str:
    """Press a key (e.g. Return, Tab, BackSpace, Escape, ctrl+c) on the virtual display."""
    await engine.virtual_keyboard_key(space_id, key)
    return f"Pressed '{key}' on virtual display in sandbox '{space_id}'."

@mcp.tool()
async def cua_mouse_scroll(
    direction: str = "down",
    clicks: int = 3,
    space_id: str = "antigravity-sandbox"
) -> str:
    """Scroll mouse wheel (up/down) on the virtual display."""
    await engine.virtual_mouse_scroll(space_id, direction=direction, clicks=clicks)
    return f"Scrolled {direction} {clicks} clicks on virtual display in sandbox '{space_id}'."

@mcp.tool()
async def cua_release_sandbox(space_id: str = "antigravity-sandbox") -> str:
    """Explicitly destroy and tear down the sandbox, freeing all cloud/container resources."""
    success = await engine.terminate_sandbox(space_id)
    return f"Sandbox '{space_id}' released." if success else f"Sandbox '{space_id}' was not running."

@mcp.tool()
async def cua_reap_orphans() -> str:
    """Watchdog: Discover and clean up any expired or dangling sandboxes to eliminate resource leaks."""
    count = await engine.reap_orphaned_sandboxes()
    return f"Watchdog check complete. Reaped {count} expired sandbox(es)."

def main():
    mcp.run()

if __name__ == "__main__":
    main()
