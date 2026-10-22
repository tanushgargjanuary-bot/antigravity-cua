---
name: cua-sandbox
description: Route code execution and browser navigation to an isolated remote cloud VM (CUA / Modal / E2B). Ensures zero local window popups and zero host desktop interference.
---

# Remote CUA Cloud Sandbox Skill

## Strict Invariant
**NEVER execute GUI tools or non-headless browsers on the user's host laptop.**
All commands, compilation jobs, and browser navigations MUST be dispatched to off-host cloud sandboxes.

## Available Tools
* `cua_cloud_exec`: Run terminal commands in the remote Linux VM.
* `cua_cloud_browser_task`: Run browser tasks in the remote cloud virtual display.
* `cua_cloud_screenshot`: Inspect the remote desktop frame buffer.
* `cua_cloud_destroy`: Clean up and terminate the remote space.
