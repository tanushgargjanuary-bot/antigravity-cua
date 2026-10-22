---
name: cua-sandbox
description: Route code execution and browser navigation to an isolated remote cloud VM or headless container (CUA / Modal / E2B). Ensures zero local window popups and zero host desktop interference.
---

# Remote CUA Cloud Sandbox Skill

## Strict Invariant
**NEVER execute GUI tools or non-headless browsers on the user's host laptop.**
All commands, compilation jobs, and browser navigations MUST be dispatched to off-host cloud sandboxes or RAM-based virtual displays (`DISPLAY=:99`).

## Production Tools
* `cua_spawn_sandbox`: Spin up an isolated micro-VM / container with lease TTL.
* `cua_exec_isolated`: Execute shell commands inside the remote sandbox.
* `cua_capture_virtual_screen`: Capture the virtual Xvfb framebuffer directly from guest RAM.
* `cua_mouse_click`: Send mouse click events to virtual display coordinates.
* `cua_keyboard_type`: Type keystrokes into the active virtual window.
* `cua_keyboard_key`: Send special key combinations.
* `cua_release_sandbox`: Clean up and terminate the sandbox.
* `cua_reap_orphans`: Watchdog cleanup of expired sandboxes.
