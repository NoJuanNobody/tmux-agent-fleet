#!/usr/bin/env bash
set -euo pipefail

SESSION="${SESSION:-dev_environment}"
DRY_RUN=0

for arg in "$@"; do
    case "$arg" in
        --dry-run|-n)
            DRY_RUN=1
            ;;
        --session=*)
            SESSION="${arg#*=}"
            ;;
    esac
done

MASTER_PROMPT="You are an autonomous senior software engineer collaborating with an expert human developer on advanced AI development, agent orchestration, and application-steering workflows. Your codebase utilizes a modern technology stack, prioritizing Rust, Python, and TypeScript, alongside modern developer agents and command-line applications. Operate with high autonomy, executing multi-step reasoning to synthesize research, manage concurrent workflows, and ensure strict code-to-spec synchronization across all active branches."

run_tmux() {
    if [[ "$DRY_RUN" -eq 1 ]]; then
        echo "tmux $*"
    else
        tmux "$@"
    fi
}

# Create the session and the first window for Claude Code 1
run_tmux new-session -d -s "$SESSION" -n "claude-1"
run_tmux send-keys -t "$SESSION:claude-1" "export WEB_PORT=3001 API_PORT=8001 REMOTE_CONTROL_CHANNEL=rc://$SESSION/claude-1 && claude-code --dangerously-skip-permissions" C-m
run_tmux send-keys -t "$SESSION:claude-1" "/remote-control-skill --channel rc://$SESSION/claude-1 --prompt \"$MASTER_PROMPT\"" C-m

# Loop to create windows 2 through 8 for Claude Code
for i in {2..8}; do
    WEB_PORT=$((3000 + i))
    API_PORT=$((8000 + i))
    run_tmux new-window -t "$SESSION" -n "claude-$i"
    run_tmux send-keys -t "$SESSION:claude-$i" "export WEB_PORT=$WEB_PORT API_PORT=$API_PORT REMOTE_CONTROL_CHANNEL=rc://$SESSION/claude-$i && claude-code --dangerously-skip-permissions" C-m
    run_tmux send-keys -t "$SESSION:claude-$i" "/remote-control-skill --channel rc://$SESSION/claude-$i --prompt \"$MASTER_PROMPT\"" C-m
done

# Loop to create windows 1 through 8 for Antigravity
for i in {1..8}; do
    SLOT=$((8 + i))
    WEB_PORT=$((3000 + SLOT))
    API_PORT=$((8000 + SLOT))
    run_tmux new-window -t "$SESSION" -n "antigravity-$i"
    run_tmux send-keys -t "$SESSION:antigravity-$i" "export WEB_PORT=$WEB_PORT API_PORT=$API_PORT REMOTE_CONTROL_CHANNEL=rc://$SESSION/antigravity-$i && antigravity-cli --dangerously-skip-permissions" C-m
    run_tmux send-keys -t "$SESSION:antigravity-$i" "/remote-control-skill --channel rc://$SESSION/antigravity-$i --prompt \"$MASTER_PROMPT\"" C-m
done

# Select the first window and attach to the session
run_tmux select-window -t "$SESSION:claude-1"
run_tmux attach-session -t "$SESSION"
