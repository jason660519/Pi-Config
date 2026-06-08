# Agent Swarm Harness

A monorepo with two related agent-swarm projects.

## 项目信息
- **目标**：构建与运行多后端 AI agent 编排工具
- **语言栈**：hivestack 为纯 Markdown / Bash slash-commands；hivewire 为 Python (FastAPI) + TypeScript/React
- 两个子项目：

### hivestack/
把 Claude Code 变成一支虚拟工程团队 —— 23 个专家角色（6 个 squad：Executive / Product / Engineering / Quality / Security / Ops）、8 个 power tool、19 个 slash command，全 Markdown、MIT。围绕 `swarm-bridge` 把任务路由到多个 AI 编码后端（Claude / Codex / Gemini / 本地 OSS）。跨会话记忆走 SQLite。

### hivewire/
Provider-agnostic 的 agent swarm harness。把 agent runtime 与 UI 解耦，提升为**可观测、可恢复、可版本化**的协议层，wire-compatible with AG-UI（额外提供 append-only event store、fork、replay）。每次模型调用经 LiteLLM 网关，Anthropic / OpenAI / Gemini 与本地后端（Ollama / llama.cpp / vLLM）只是配置改动。

## gstack
Use `/browse` from gstack for all web browsing. Never use `mcp__claude-in-chrome__*` tools.

gstack skills are installed globally and loaded automatically — no need to list them here.
