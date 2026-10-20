import subprocess
from typing import Any, Dict, List, Optional

from tmux_agent_fleet.remote_bridge import RemoteControlBridge
from tmux_agent_fleet.worktree_allocator import AgentSlot, FleetWorktreeAllocator


class TmuxFleetLauncher:
    """Builds and executes the multi-agent tmux session and window startup sequence."""

    def __init__(
        self,
        allocator: Optional[FleetWorktreeAllocator] = None,
        bridge: Optional[RemoteControlBridge] = None,
    ) -> None:
        self.allocator = allocator
        self.bridge = bridge or RemoteControlBridge()

    def build_slots(
        self,
        session_name: str = "dev_environment",
        claude_count: int = 8,
        antigravity_count: int = 8,
    ) -> List[AgentSlot]:
        allocator = self.allocator or FleetWorktreeAllocator(session_name=session_name)
        return allocator.allocate_slots(
            claude_count=claude_count,
            antigravity_count=antigravity_count,
        )

    def _build_window_shell_command(
        self,
        slot: AgentSlot,
        isolate_worktrees: bool = False,
    ) -> str:
        env_prefix = (
            f"export WEB_PORT={slot.web_port} "
            f"API_PORT={slot.api_port} "
            f"REMOTE_CONTROL_CHANNEL={slot.remote_control_channel}"
        )
        if isolate_worktrees:
            return (
                f"mkdir -p {slot.worktree_path} && "
                f"cd {slot.worktree_path} && "
                f"{env_prefix} && {slot.command}"
            )
        return f"{env_prefix} && {slot.command}"

    def build_tmux_commands(
        self,
        session_name: str = "dev_environment",
        claude_count: int = 8,
        antigravity_count: int = 8,
        enter_remote_control: bool = True,
        isolate_worktrees: bool = False,
        attach: bool = True,
    ) -> List[List[str]]:
        """Return the ordered list of tmux argv commands for launching the entire fleet."""
        slots = self.build_slots(
            session_name=session_name,
            claude_count=claude_count,
            antigravity_count=antigravity_count,
        )
        if not slots:
            return []

        commands: List[List[str]] = []
        first_slot = slots[0]

        commands.append(
            ["tmux", "new-session", "-d", "-s", session_name, "-n", first_slot.window_name]
        )
        commands.append(
            [
                "tmux",
                "send-keys",
                "-t",
                f"{session_name}:{first_slot.window_name}",
                self._build_window_shell_command(first_slot, isolate_worktrees=isolate_worktrees),
                "C-m",
            ]
        )
        if enter_remote_control:
            commands.append(
                [
                    "tmux",
                    "send-keys",
                    "-t",
                    f"{session_name}:{first_slot.window_name}",
                    self.bridge.build_bootstrap_command(first_slot),
                    "C-m",
                ]
            )

        for slot in slots[1:]:
            commands.append(["tmux", "new-window", "-t", session_name, "-n", slot.window_name])
            commands.append(
                [
                    "tmux",
                    "send-keys",
                    "-t",
                    f"{session_name}:{slot.window_name}",
                    self._build_window_shell_command(slot, isolate_worktrees=isolate_worktrees),
                    "C-m",
                ]
            )
            if enter_remote_control:
                commands.append(
                    [
                        "tmux",
                        "send-keys",
                        "-t",
                        f"{session_name}:{slot.window_name}",
                        self.bridge.build_bootstrap_command(slot),
                        "C-m",
                    ]
                )

        commands.append(
            ["tmux", "select-window", "-t", f"{session_name}:{first_slot.window_name}"]
        )
        if attach:
            commands.append(["tmux", "attach-session", "-t", session_name])

        return commands

    def generate_bash_script(
        self,
        session_name: str = "dev_environment",
        claude_count: int = 8,
        antigravity_count: int = 8,
        enter_remote_control: bool = True,
        isolate_worktrees: bool = False,
        attach: bool = True,
    ) -> str:
        """Generate a standalone bash script that creates and populates the tmux fleet."""
        slots = self.build_slots(
            session_name=session_name,
            claude_count=claude_count,
            antigravity_count=antigravity_count,
        )
        lines: List[str] = [
            "#!/bin/bash",
            "",
            f'SESSION="{session_name}"',
            "",
        ]
        if not slots:
            return "\n".join(lines)

        first_slot = slots[0]
        lines.append("# Create the session and the first window")
        lines.append(f'tmux new-session -d -s $SESSION -n "{first_slot.window_name}"')
        lines.append(
            f'tmux send-keys -t $SESSION:"{first_slot.window_name}" '
            f'"{self._build_window_shell_command(first_slot, isolate_worktrees=isolate_worktrees)}" C-m'
        )
        if enter_remote_control:
            bootstrap_escaped = self.bridge.build_bootstrap_command(first_slot).replace('"', '\\"')
            lines.append(
                f'tmux send-keys -t $SESSION:"{first_slot.window_name}" '
                f'"{bootstrap_escaped}" C-m'
            )

        lines.append("")
        lines.append("# Create remaining agent windows")
        for slot in slots[1:]:
            lines.append(f'tmux new-window -t $SESSION -n "{slot.window_name}"')
            lines.append(
                f'tmux send-keys -t $SESSION:"{slot.window_name}" '
                f'"{self._build_window_shell_command(slot, isolate_worktrees=isolate_worktrees)}" C-m'
            )
            if enter_remote_control:
                bootstrap_escaped = self.bridge.build_bootstrap_command(slot).replace('"', '\\"')
                lines.append(
                    f'tmux send-keys -t $SESSION:"{slot.window_name}" '
                    f'"{bootstrap_escaped}" C-m'
                )

        lines.append("")
        lines.append("# Select the first window and attach to the session")
        lines.append(f'tmux select-window -t $SESSION:"{first_slot.window_name}"')
        if attach:
            lines.append("tmux attach-session -t $SESSION")

        return "\n".join(lines) + "\n"

    def launch(
        self,
        session_name: str = "dev_environment",
        claude_count: int = 8,
        antigravity_count: int = 8,
        enter_remote_control: bool = True,
        isolate_worktrees: bool = False,
        dry_run: bool = True,
        attach: bool = True,
    ) -> Dict[str, Any]:
        """Execute or dry-run the tmux fleet launch sequence."""
        commands = self.build_tmux_commands(
            session_name=session_name,
            claude_count=claude_count,
            antigravity_count=antigravity_count,
            enter_remote_control=enter_remote_control,
            isolate_worktrees=isolate_worktrees,
            attach=attach,
        )
        slots = self.build_slots(
            session_name=session_name,
            claude_count=claude_count,
            antigravity_count=antigravity_count,
        )

        if not dry_run:
            for cmd in commands:
                subprocess.run(cmd, check=True)

        return {
            "session_name": session_name,
            "dry_run": dry_run,
            "total_windows": len(slots),
            "commands": commands,
            "manifest": self.bridge.build_steering_manifest(
                slots=slots,
                session_name=session_name,
            ),
        }
