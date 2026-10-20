import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from tmux_agent_fleet import (
    MASTER_ENGINEERING_PROMPT,
    AgentSlot,
    FleetWorktreeAllocator,
    RemoteControlBridge,
    TmuxFleetLauncher,
)
from tmux_agent_fleet.cli import main as cli_main

EXPECTED_PROMPT = (
    "You are an autonomous senior software engineer collaborating with an expert "
    "human developer on advanced AI development, agent orchestration, and "
    "application-steering workflows. Your codebase utilizes a modern technology "
    "stack, prioritizing Rust, Python, and TypeScript, alongside modern developer "
    "agents and command-line applications. Operate with high autonomy, executing "
    "multi-step reasoning to synthesize research, manage concurrent workflows, "
    "and ensure strict code-to-spec synchronization across all active branches."
)


def test_master_engineering_prompt_exact_match() -> None:
    assert MASTER_ENGINEERING_PROMPT == EXPECTED_PROMPT
    assert "Rust, Python, and TypeScript" in MASTER_ENGINEERING_PROMPT
    assert "code-to-spec synchronization" in MASTER_ENGINEERING_PROMPT


def test_worktree_allocator_16_slots_and_window_names() -> None:
    allocator = FleetWorktreeAllocator(session_name="dev_environment")
    slots = allocator.allocate_slots(claude_count=8, antigravity_count=8)

    assert len(slots) == 16
    claude_slots = slots[:8]
    antigravity_slots = slots[8:]

    assert [s.window_name for s in claude_slots] == [f"claude-{i}" for i in range(1, 9)]
    assert [s.window_name for s in antigravity_slots] == [
        f"antigravity-{i}" for i in range(1, 9)
    ]
    assert all(isinstance(s, AgentSlot) for s in slots)


def test_dangerously_skip_permissions_flag_in_all_slots() -> None:
    allocator = FleetWorktreeAllocator()
    slots = allocator.allocate_slots()

    for slot in slots[:8]:
        assert slot.harness == "claude-code"
        assert slot.command == "claude-code --dangerously-skip-permissions"

    for slot in slots[8:]:
        assert slot.harness == "antigravity-cli"
        assert slot.command == "antigravity-cli --dangerously-skip-permissions"


def test_port_and_worktree_isolation_uniqueness() -> None:
    allocator = FleetWorktreeAllocator()
    slots = allocator.allocate_slots()

    web_ports = [s.web_port for s in slots]
    api_ports = [s.api_port for s in slots]
    worktrees = [s.worktree_path for s in slots]
    channels = [s.remote_control_channel for s in slots]

    assert web_ports == list(range(3001, 3017))
    assert api_ports == list(range(8001, 8017))
    assert len(set(web_ports)) == 16
    assert len(set(api_ports)) == 16
    assert len(set(worktrees)) == 16
    assert len(set(channels)) == 16
    assert set(web_ports).isdisjoint(set(api_ports))


def test_remote_control_bridge_bootstrap_and_manifest() -> None:
    allocator = FleetWorktreeAllocator(session_name="dev_environment")
    slots = allocator.allocate_slots()
    bridge = RemoteControlBridge()

    manifest = bridge.build_steering_manifest(slots, session_name="dev_environment")
    assert manifest["session_name"] == "dev_environment"
    assert manifest["skill"] == "remote-control-skill"
    assert manifest["total_agents"] == 16
    assert manifest["master_prompt"] == EXPECTED_PROMPT
    assert len(manifest["agents"]) == 16

    first_agent = manifest["agents"][0]
    assert first_agent["window_name"] == "claude-1"
    assert first_agent["remote_control"]["enabled"] is True
    assert first_agent["remote_control"]["channel"] == "rc://dev_environment/claude-1"
    assert "/remote-control-skill" in first_agent["remote_control"]["bootstrap_command"]
    assert EXPECTED_PROMPT in first_agent["remote_control"]["bootstrap_command"]


def test_launcher_generate_bash_script_contains_all_16_windows_and_remote_control() -> None:
    launcher = TmuxFleetLauncher()
    script = launcher.generate_bash_script(
        session_name="dev_environment",
        claude_count=8,
        antigravity_count=8,
        enter_remote_control=True,
        isolate_worktrees=True,
    )

    assert 'SESSION="dev_environment"' in script
    assert 'tmux new-session -d -s $SESSION -n "claude-1"' in script
    for i in range(2, 9):
        assert f'tmux new-window -t $SESSION -n "claude-{i}"' in script
    for i in range(1, 9):
        assert f'tmux new-window -t $SESSION -n "antigravity-{i}"' in script

    assert script.count("claude-code --dangerously-skip-permissions") == 8
    assert script.count("antigravity-cli --dangerously-skip-permissions") == 8
    assert script.count("/remote-control-skill") == 16
    assert 'tmux select-window -t $SESSION:"claude-1"' in script
    assert "tmux attach-session -t $SESSION" in script


def test_launcher_tmux_commands_and_dry_run_vs_execute() -> None:
    launcher = TmuxFleetLauncher()
    res = launcher.launch(session_name="dev_environment", dry_run=True)

    assert res["dry_run"] is True
    assert res["total_windows"] == 16
    # 1 new-session + 15 new-window + 16*2 send-keys + 1 select-window + 1 attach-session = 50 commands
    assert len(res["commands"]) == 50

    with patch("subprocess.run") as mock_run:
        launcher.launch(session_name="dev_environment", dry_run=False, attach=False)
        assert mock_run.call_count == 49


def test_cli_prompt_and_script_subcommands(capsys: pytest.CaptureFixture[str]) -> None:
    rc_prompt = cli_main(["prompt"])
    captured_prompt = capsys.readouterr().out.strip()
    assert rc_prompt == 0
    assert captured_prompt == EXPECTED_PROMPT

    rc_script = cli_main(["script", "--isolate-worktrees"])
    captured_script = capsys.readouterr().out
    assert rc_script == 0
    assert "claude-code --dangerously-skip-permissions" in captured_script
    assert "antigravity-cli --dangerously-skip-permissions" in captured_script
    assert ".worktrees/claude-1" in captured_script


def test_cli_manifest_and_launch_subcommands(capsys: pytest.CaptureFixture[str]) -> None:
    rc_manifest = cli_main(["manifest"])
    manifest_data = json.loads(capsys.readouterr().out)
    assert rc_manifest == 0
    assert manifest_data["total_agents"] == 16
    assert manifest_data["agents"][0]["web_port"] == 3001
    assert manifest_data["agents"][-1]["web_port"] == 3016
    assert manifest_data["agents"][-1]["api_port"] == 8016

    rc_launch = cli_main(["launch", "--dry-run"])
    launch_data = json.loads(capsys.readouterr().out)
    assert rc_launch == 0
    assert launch_data["dry_run"] is True
    assert launch_data["total_windows"] == 16


def test_start_fleet_shell_script_dry_run_and_skill_md() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    script_path = repo_root / "scripts" / "start_fleet.sh"
    skill_md_path = repo_root / "SKILL.md"

    assert script_path.exists()
    proc = subprocess.run(
        [str(script_path), "--dry-run"],
        capture_output=True,
        text=True,
        check=True,
    )
    out = proc.stdout
    assert "tmux new-session -d -s dev_environment -n claude-1" in out
    assert out.count("claude-code --dangerously-skip-permissions") == 8
    assert out.count("antigravity-cli --dangerously-skip-permissions") == 8
    assert out.count("/remote-control-skill") == 16

    skill_text = skill_md_path.read_text(encoding="utf-8")
    assert skill_text.startswith("---\nname: tmux-agent-fleet\n")
    assert EXPECTED_PROMPT in skill_text
