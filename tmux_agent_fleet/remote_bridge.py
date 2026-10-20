import json
from typing import Any, Dict, Sequence

from tmux_agent_fleet.worktree_allocator import AgentSlot

MASTER_ENGINEERING_PROMPT = (
    "You are an autonomous senior software engineer collaborating with an expert "
    "human developer on advanced AI development, agent orchestration, and "
    "application-steering workflows. Your codebase utilizes a modern technology "
    "stack, prioritizing Rust, Python, and TypeScript, alongside modern developer "
    "agents and command-line applications. Operate with high autonomy, executing "
    "multi-step reasoning to synthesize research, manage concurrent workflows, "
    "and ensure strict code-to-spec synchronization across all active branches."
)


class RemoteControlBridge:
    """Generates remote-control-skill bootstrap commands and steering manifests for the fleet."""

    SKILL_NAME = "remote-control-skill"

    def __init__(self, master_prompt: str = MASTER_ENGINEERING_PROMPT) -> None:
        self.master_prompt = master_prompt

    def build_bootstrap_command(self, slot: AgentSlot) -> str:
        """Return the remote-control-skill activation command injected into a tmux window."""
        return (
            f"/{self.SKILL_NAME} "
            f"--channel {slot.remote_control_channel} "
            f'--prompt "{self.master_prompt}"'
        )

    def build_slot_payload(self, slot: AgentSlot) -> Dict[str, Any]:
        """Build the remote-control registration and steering payload for a single agent slot."""
        return {
            "slot_id": slot.slot_id,
            "window_name": slot.window_name,
            "harness": slot.harness,
            "command": slot.command,
            "worktree_path": slot.worktree_path,
            "web_port": slot.web_port,
            "api_port": slot.api_port,
            "remote_control": {
                "skill": self.SKILL_NAME,
                "enabled": True,
                "channel": slot.remote_control_channel,
                "bootstrap_command": self.build_bootstrap_command(slot),
                "master_prompt": self.master_prompt,
            },
        }

    def build_steering_manifest(
        self,
        slots: Sequence[AgentSlot],
        session_name: str = "dev_environment",
    ) -> Dict[str, Any]:
        """Generate the full steering manifest for all agent windows in the fleet."""
        return {
            "session_name": session_name,
            "skill": self.SKILL_NAME,
            "total_agents": len(slots),
            "master_prompt": self.master_prompt,
            "agents": [self.build_slot_payload(slot) for slot in slots],
        }

    def to_json(
        self,
        slots: Sequence[AgentSlot],
        session_name: str = "dev_environment",
        indent: int = 2,
    ) -> str:
        """Serialize the steering manifest as formatted JSON."""
        return json.dumps(
            self.build_steering_manifest(slots=slots, session_name=session_name),
            indent=indent,
        )
