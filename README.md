# tmux-agent-fleet

Spawn and orchestrate a 16-window autonomous coding agent fleet in `tmux` (**8 Claude Code** + **8 Antigravity CLI** sessions) with `--dangerously-skip-permissions`, deterministic git worktree & port isolation (`3001..3016`, `8001..8016`), and automatic `remote-control-skill` registration.

## Installation

Install globally as an Agent Skill via the Skills CLI:

```bash
npx skills add NoJuanNobody/tmux-agent-fleet -g
```

Or install the Python CLI package locally:

```bash
pip install -e .
```

## Features

- **16-Agent Tmux Fleet**: Spawns 8 `claude-code --dangerously-skip-permissions` windows (`claude-1..8`) and 8 `antigravity-cli --dangerously-skip-permissions` windows (`antigravity-1..8`) inside the `dev_environment` tmux session.
- **Automatic Remote Control Registration**: Immediately boots every agent into `remote-control-skill` mode and injects the Master Autonomous Senior Software Engineer Prompt.
- **Deterministic Worktree & Port Isolation**: Assigns isolated git worktree paths (`.worktrees/claude-1` .. `.worktrees/antigravity-8`) and non-overlapping port pairs (`WEB_PORT=3001..3016`, `API_PORT=8001..8016`).

## Master Autonomous Senior Software Engineer Prompt

> "You are an autonomous senior software engineer collaborating with an expert human developer on advanced AI development, agent orchestration, and application-steering workflows. Your codebase utilizes a modern technology stack, prioritizing Rust, Python, and TypeScript, alongside modern developer agents and command-line applications. Operate with high autonomy, executing multi-step reasoning to synthesize research, manage concurrent workflows, and ensure strict code-to-spec synchronization across all active branches."

## Shell Script Example

```bash
#!/bin/bash

SESSION="dev_environment"

# Create the session and the first window for Claude Code 1
tmux new-session -d -s $SESSION -n "claude-1"
tmux send-keys -t $SESSION:"claude-1" "claude-code --dangerously-skip-permissions" C-m

# Loop to create windows 2 through 8 for Claude Code
for i in {2..8}; do
    tmux new-window -t $SESSION -n "claude-$i"
    tmux send-keys -t $SESSION:"claude-$i" "claude-code --dangerously-skip-permissions" C-m
done

# Loop to create windows 1 through 8 for Antigravity
for i in {1..8}; do
    tmux new-window -t $SESSION -n "antigravity-$i"
    tmux send-keys -t $SESSION:"antigravity-$i" "antigravity-cli --dangerously-skip-permissions" C-m
done

# Select the first window and attach to the session
tmux select-window -t $SESSION:"claude-1"
tmux attach-session -t $SESSION
```

Or run the included fleet startup script with remote-control registration and `--dry-run` support:

```bash
./scripts/start_fleet.sh --dry-run
./scripts/start_fleet.sh
```

## CLI Usage

```bash
# 1. Print the generated bash startup script
tmux-agent-fleet script
tmux-agent-fleet script --isolate-worktrees

# 2. Print the 16-agent JSON manifest (slots, ports, worktrees, remote-control channels)
tmux-agent-fleet manifest

# 3. Print the Master Autonomous Senior Software Engineer Prompt
tmux-agent-fleet prompt

# 4. Launch the fleet (dry-run by default, or --execute to run live)
tmux-agent-fleet launch --dry-run
tmux-agent-fleet launch --execute
```

## Testing

```bash
pytest -v
```
