import asyncio
import sys
from mcp.server.fastmcp import FastMCP
from .spaces import SpacesManager

mcp = FastMCP("Antigravity CUA Bridge")
manager = SpacesManager()

@mcp.tool()
async def cua_exec_command(command: str, space_id: str = "antigravity-sandbox") -> str:
    """Run a terminal command inside an isolated Cua Space micro-VM/container.
    Never executes on the local host machine.
    """
    res = await manager.run_bash(command, space_id)
    out = res["stdout"]
    if res["stderr"]:
        out += f"\n[stderr]\n{res['stderr']}"
    return out or f"(Command exited with code {res['exit_code']} and no output)"

@mcp.tool()
async def cua_save_file(path: str, content: str, space_id: str = "antigravity-sandbox") -> str:
    """Write file directly into the isolated sandbox filesystem without touching host disk."""
    return await manager.write_file(path, content, space_id)

@mcp.tool()
async def cua_space_screenshot(space_id: str = "antigravity-sandbox") -> bytes:
    """Capture screenshot of the isolated virtual desktop running in Cua Space."""
    return await manager.take_screenshot(space_id)

@mcp.tool()
async def cua_cleanup_space(space_id: str = "antigravity-sandbox") -> str:
    """Delete the isolated throwaway space and clean up all remote resources."""
    return await manager.destroy_space(space_id)

def main():
    mcp.run()

if __name__ == "__main__":
    main()
