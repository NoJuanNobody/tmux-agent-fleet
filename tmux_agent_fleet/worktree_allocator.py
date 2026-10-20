from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Union


@dataclass(frozen=True)
class AgentSlot:
    """Represents a single isolated agent window slot in the tmux fleet."""

    slot_id: int
    window_name: str
    harness: str
    command: str
    worktree_path: str
    web_port: int
    api_port: int
    remote_control_channel: str

    def to_dict(self) -> Dict[str, Union[int, str]]:
        return asdict(self)


class FleetWorktreeAllocator:
    """Allocates deterministic worktree paths and ports for a multi-agent tmux fleet."""

    DEFAULT_BASE_WEB_PORT = 3001
    DEFAULT_BASE_API_PORT = 8001

    def __init__(
        self,
        session_name: str = "dev_environment",
        worktree_root: Union[str, Path] = ".worktrees",
        base_web_port: int = DEFAULT_BASE_WEB_PORT,
        base_api_port: int = DEFAULT_BASE_API_PORT,
    ) -> None:
        self.session_name = session_name
        self.worktree_root = Path(worktree_root)
        self.base_web_port = base_web_port
        self.base_api_port = base_api_port

    def allocate_slots(
        self,
        claude_count: int = 8,
        antigravity_count: int = 8,
    ) -> List[AgentSlot]:
        """Generate ordered AgentSlot entries for all Claude Code and Antigravity windows."""
        if claude_count < 0 or antigravity_count < 0:
            raise ValueError("Agent counts must be non-negative")

        slots: List[AgentSlot] = []
        idx = 0

        for c_idx in range(1, claude_count + 1):
            window_name = f"claude-{c_idx}"
            slots.append(
                AgentSlot(
                    slot_id=idx + 1,
                    window_name=window_name,
                    harness="claude-code",
                    command="claude-code --dangerously-skip-permissions",
                    worktree_path=str(self.worktree_root / window_name),
                    web_port=self.base_web_port + idx,
                    api_port=self.base_api_port + idx,
                    remote_control_channel=f"rc://{self.session_name}/{window_name}",
                )
            )
            idx += 1

        for a_idx in range(1, antigravity_count + 1):
            window_name = f"antigravity-{a_idx}"
            slots.append(
                AgentSlot(
                    slot_id=idx + 1,
                    window_name=window_name,
                    harness="antigravity-cli",
                    command="antigravity-cli --dangerously-skip-permissions",
                    worktree_path=str(self.worktree_root / window_name),
                    web_port=self.base_web_port + idx,
                    api_port=self.base_api_port + idx,
                    remote_control_channel=f"rc://{self.session_name}/{window_name}",
                )
            )
            idx += 1

        return slots
