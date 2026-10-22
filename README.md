# Antigravity CUA Bridge

An open-source integration that connects **Google Antigravity** to **CUA (trycua)** isolated sandboxes and computer use via the Model Context Protocol (MCP).

---

## What It Does
* **Zero Host Interference**: Runs untrusted shell commands, heavy compilation jobs, and scripts inside an isolated remote or containerized Cua Space micro-VM. It never opens windows on your physical laptop or touches your local desktop.
* **Isolated Virtual Screen**: Captures and inspects dedicated headless virtual desktops instead of interfering with your personal active workspace.
* **Full MCP Integration**: Exposes standard tools (`cua_exec_command`, `cua_save_file`, `cua_space_screenshot`, `cua_cleanup_space`) directly to the Antigravity agent loop.

---

## Quickstart

### 1. Installation
```bash
pip install -e .
```
*(Requires `cua` and `mcp`).*

### 2. Connect to Antigravity (`mcp_config.json`)
Add to `~/.gemini/config/mcp_config.json`:
```json
{
  "mcpServers": {
    "cua-spaces": {
      "command": "python",
      "args": ["-m", "antigravity_cua.server"]
    }
  }
}
```

### 3. Usage
Once enabled, Antigravity can dispatch tasks to isolated Cua spaces:
```
"Run this script inside an isolated Ubuntu Cua Space and show me the output."
```
The command executes in the remote container and returns the output to Antigravity without ever touching your local machine.

---

## License
MIT
