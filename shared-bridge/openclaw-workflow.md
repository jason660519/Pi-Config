# OpenClaw Cross-App Integration Workflow

Status: v0.1
Date: 2026-05-19

## Overview

OpenClaw runs as a sidecar within Project Manager (`npm run openclaw`) and can
dispatch agents across all 4 company apps. This document describes how OpenClaw
discovers each app, validates its health, and sends agent tasks.

## App Discovery

OpenClaw reads `/Volumes/KLEVV-4T-1/shared-bridge/openclaw-apps-config.json` to
discover the 4 apps:

| App | Root Path | Dev Port | Tauri |
|---|---|---|---|
| Project Manager | `/Volumes/KLEVV-4T-1/Project-Manager` | 43187 | ✅ |
| SayDo | `/Volumes/KLEVV-4T-1/SayDo` | 1420 | ✅ |
| Realestate_Management_Apps | `/Volumes/KLEVV-4T-1/Realestate_Management_Apps` | 5173 | ✅ |
| Company AI App Standards | `/Volumes/KLEVV-4T-1/Company-AI-App-Standards` | — | ❌ |

## OpenClaw Gateway API

OpenClaw's gateway runs at `http://127.0.0.1:18790`. The shared bridge
`OpenClawBridge` class in `shared-bridge/src/openclaw.ts` wraps the API:

### `POST /api/dispatch` — Send agent task

```json
{
  "projectRoot": "/Volumes/KLEVV-4T-1/Project-Manager",
  "prompt": "Run typecheck on this project",
  "model": "openrouter/anthropic/claude-3.5-sonnet"
}
```

Returns: `{ "sessionId": "uuid" }` or `{ "error": "..." }`

### `POST /api/events` — Cross-app event

```json
{
  "source": "realestate-management",
  "target": "project-manager",
  "eventType": "task.export",
  "payload": { "taskId": "uuid", "title": "..." },
  "timestamp": "2026-05-19T00:00:00Z"
}
```

### `GET /api/health/:appId` — Health check

Returns: `{ "appId": "...", "isRunning": true, "typecheck": "pass", "port": 43187 }`

## OpenClaw Workspace Config

The OpenClaw workspace root is:
```
/Volumes/KLEVV-4T-1/Project-Manager/.project-manager/openclaw/workspace
```

To add cross-app awareness, the workspace already contains:
- `AGENTS.md` — agent rules
- `SOUL.md` — persona
- `USER.md` — user profile
- `TOOLS.md` — local notes
- `BOOTSTRAP.md` — bootstrap (active)

## Plugin Capabilities (Registered)

| Capability | Provider → Consumer | Transport |
|---|---|---|
| `realestate.task.export` | Realestate → Project Manager | HTTP API |
| `saydo.text.handoff` | SayDo → Realestate | Local IPC |
| `openclaw.agent.dispatch` | OpenClaw → Project Manager | HTTP API |

To add a new capability: edit `shared-bridge/src/registry.ts` and rebuild.

## Verification

```bash
# Test shared bridge
cd /Volumes/KLEVV-4T-1/shared-bridge && npm run typecheck

# Test each app
cd /Volumes/KLEVV-4T-1/Project-Manager && npm run typecheck && npm test -- --run
cd /Volumes/KLEVV-4T-1/SayDo && npm run typecheck && npm test -- --run
cd /Volumes/KLEVV-4T-1/Realestate_Management_Apps && npm run typecheck && npm test -- --run
cd /Volumes/KLEVV-4T-1/Company-AI-App-Standards && npm run typecheck

# Test OpenClaw gateway (if running)
curl http://127.0.0.1:18790/health
```
