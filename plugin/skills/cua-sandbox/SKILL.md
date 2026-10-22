---
name: cua-sandbox
description: Run untrusted commands, heavy builds, or containerized automation inside an isolated Cua Space. Use when the user wants isolated execution without touching the local host machine.
---

# Cua Sandbox Skill

## When to Use
Use this skill when:
1. The user asks to run untrusted code, shell commands, or test scripts in a clean sandbox.
2. The user wants to run Linux commands on a Windows machine without local WSL setup.
3. The user requests remote/cloud execution that should never open windows on the host desktop.

## Tools
* `cua_exec_command`: Run commands inside the isolated Cua Space.
* `cua_save_file`: Write files directly into the sandbox filesystem.
* `cua_space_screenshot`: View the headless virtual desktop of the space.
* `cua_cleanup_space`: Delete and destroy the throwaway space.
