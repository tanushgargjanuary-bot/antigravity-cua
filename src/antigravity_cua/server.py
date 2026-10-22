import asyncio
from mcp.server.fastmcp import FastMCP
from .spaces import SpacesManager
from .config import CuaConfig

mcp = FastMCP("Antigravity CUA Remote Bridge")
manager = SpacesManager()

@mcp.tool()
async def cua_cloud_exec(command: str, space_id: str = "antigravity-remote-sandbox") -> str:
    """Execute shell commands strictly inside an off-host cloud sandbox (Cua / Modal / E2B).
    NEVER touches local Windows host files, terminal, or processes.
    """
    res = await manager.run_remote_command(command, space_id)
    out = res["stdout"]
    if res["stderr"]:
        out += f"\n[stderr]\n{res['stderr']}"
    return out or f"(Exit code: {res['exit_code']}, no text output)"

@mcp.tool()
async def cua_cloud_browser_task(url: str, task: str, space_id: str = "antigravity-remote-sandbox") -> str:
    """Perform web/browser navigation inside a remote cloud virtual machine.
    GUARANTEE: Zero windows opened on your laptop screen. Runs on remote cloud virtual display.
    """
    res = await manager.run_remote_browser(url, task, space_id)
    return res["output"] or res["error"]

@mcp.tool()
async def cua_cloud_screenshot(space_id: str = "antigravity-remote-sandbox") -> bytes:
    """Capture a screenshot of the remote cloud virtual desktop."""
    return await manager.get_remote_screenshot(space_id)

@mcp.tool()
async def cua_cloud_destroy(space_id: str = "antigravity-remote-sandbox") -> str:
    """Terminate and destroy the remote cloud sandbox completely."""
    return await manager.destroy_space(space_id)

def main():
    mcp.run()

if __name__ == "__main__":
    main()
