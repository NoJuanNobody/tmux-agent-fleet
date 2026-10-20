---
name: tmux-agent-fleet
description: Spawn and orchestrate a 16-window multi-agent tmux fleet (8 Claude Code + 8 Antigravity CLI sessions) with --dangerously-skip-permissions, deterministic git worktree & port isolation (3001..3016, 8001..8016), and automatic remote-control-skill registration pre-loaded with the Master Autonomous Senior Software Engineer Prompt.
---

# Tmux Agent Fleet (`tmux-agent-fleet`)

Launch a persistent 16-window `tmux` agent fleet (`claude-1..8` and `antigravity-1..8`) in a single command, with optional git worktree isolation, deterministic port allocation (`3001..3016`, `8001..8016`), and automatic `remote-control-skill` steering injection.

## Overview

When working on high-velocity multi-agent engineering, manually spinning up 16 terminal windows, configuring permissions, assigning non-colliding ports, and bootstrapping each agent with your steering protocol is error-prone. `tmux-agent-fleet` automates this entire startup lifecycle:

1. **8 Claude Code Windows (`claude-1` .. `claude-8`)**:
   Launched with `claude-code --dangerously-skip-permissions`.
2. **8 Antigravity CLI Windows (`antigravity-1` .. `antigravity-8`)**:
   Launched with `antigravity-cli --dangerously-skip-permissions`.
3. **Automatic `remote-control-skill` Registration**:
   Every window automatically receives the `remote-control-skill` bootstrap command and registers on a deterministic channel (`rc://dev_environment/<window_name>`) with the Master Autonomous Senior Software Engineer Prompt pre-loaded.
4. **Worktree & Port Isolation**:
   Allocates isolated git worktrees (`.worktrees/claude-1` .. `.worktrees/antigravity-8`) and unique port pairs (`WEB_PORT=3001..3016`, `API_PORT=8001..8016`) so all 16 agents can run dev servers and test suites concurrently without collision.

## Master Autonomous Senior Software Engineer Prompt

Every agent in the fleet is primed with the following Master Engineering Prompt:

> "You are an autonomous senior software engineer collaborating with an expert human developer on advanced AI development, agent orchestration, and application-steering workflows. Your codebase utilizes a modern technology stack, prioritizing Rust, Python, and TypeScript, alongside modern developer agents and command-line applications. Operate with high autonomy, executing multi-step reasoning to synthesize research, manage concurrent workflows, and ensure strict code-to-spec synchronization across all active branches."

## Quick Start

### 1. Bash Startup Script

Run the standalone fleet script directly (or pass `--dry-run` to inspect the `tmux` commands):

```bash
./scripts/start_fleet.sh --dry-run
./scripts/start_fleet.sh
```

### 2. Python CLI

```bash
# Print the generated bash startup script
tmux-agent-fleet script

# Print the 16-slot JSON manifest (worktrees, ports 3001..3016 / 8001..8016, remote-control channels)
tmux-agent-fleet manifest

# Print the Master Autonomous Senior Software Engineer Prompt
tmux-agent-fleet prompt

# Dry-run or execute the fleet launch
tmux-agent-fleet launch --dry-run
tmux-agent-fleet launch --execute
```

## Slot & Port Allocation Table

| Slot ID | Window Name | Harness | Command | Web Port | API Port | Worktree Path |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1..8 | `claude-1..8` | `claude-code` | `claude-code --dangerously-skip-permissions` | `3001..3008` | `8001..8008` | `.worktrees/claude-1..8` |
| 9..16 | `antigravity-1..8` | `antigravity-cli` | `antigravity-cli --dangerously-skip-permissions` | `3009..3016` | `8009..8016` | `.worktrees/antigravity-1..8` |
