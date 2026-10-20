import argparse
import json
import sys
from typing import List, Optional

from tmux_agent_fleet.launcher import TmuxFleetLauncher
from tmux_agent_fleet.remote_bridge import MASTER_ENGINEERING_PROMPT, RemoteControlBridge
from tmux_agent_fleet.worktree_allocator import FleetWorktreeAllocator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tmux-agent-fleet",
        description=(
            "Spawn and orchestrate a 16-window multi-agent tmux fleet "
            "(8 Claude Code + 8 Antigravity CLI sessions) with worktree/port isolation "
            "and automatic remote-control-skill registration."
        ),
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # script subcommand
    script_parser = subparsers.add_parser(
        "script",
        help="Print the generated bash startup script for the tmux agent fleet.",
    )
    script_parser.add_argument(
        "--session",
        default="dev_environment",
        help="Tmux session name (default: dev_environment).",
    )
    script_parser.add_argument(
        "--claude-count",
        type=int,
        default=8,
        help="Number of Claude Code windows (default: 8).",
    )
    script_parser.add_argument(
        "--antigravity-count",
        type=int,
        default=8,
        help="Number of Antigravity CLI windows (default: 8).",
    )
    script_parser.add_argument(
        "--no-remote-control",
        action="store_true",
        help="Disable automatic remote-control-skill bootstrap injection.",
    )
    script_parser.add_argument(
        "--isolate-worktrees",
        action="store_true",
        help="Create and cd into isolated worktree directories for each window.",
    )

    # manifest subcommand
    manifest_parser = subparsers.add_parser(
        "manifest",
        help="Print the JSON 16-agent slot, port, and remote-control manifest.",
    )
    manifest_parser.add_argument(
        "--session",
        default="dev_environment",
        help="Tmux session name (default: dev_environment).",
    )
    manifest_parser.add_argument(
        "--claude-count",
        type=int,
        default=8,
        help="Number of Claude Code windows (default: 8).",
    )
    manifest_parser.add_argument(
        "--antigravity-count",
        type=int,
        default=8,
        help="Number of Antigravity CLI windows (default: 8).",
    )

    # prompt subcommand
    subparsers.add_parser(
        "prompt",
        help="Print the Master Autonomous Senior Software Engineer Prompt.",
    )

    # launch subcommand
    launch_parser = subparsers.add_parser(
        "launch",
        help="Launch the tmux agent fleet (--dry-run by default, or --execute).",
    )
    launch_parser.add_argument(
        "--session",
        default="dev_environment",
        help="Tmux session name (default: dev_environment).",
    )
    launch_parser.add_argument(
        "--claude-count",
        type=int,
        default=8,
        help="Number of Claude Code windows (default: 8).",
    )
    launch_parser.add_argument(
        "--antigravity-count",
        type=int,
        default=8,
        help="Number of Antigravity CLI windows (default: 8).",
    )
    launch_parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Print planned tmux commands without executing (default: True).",
    )
    launch_parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute the tmux commands live instead of dry-run.",
    )
    launch_parser.add_argument(
        "--no-remote-control",
        action="store_true",
        help="Disable automatic remote-control-skill bootstrap injection.",
    )
    launch_parser.add_argument(
        "--isolate-worktrees",
        action="store_true",
        help="Create and cd into isolated worktree directories for each window.",
    )
    launch_parser.add_argument(
        "--no-attach",
        action="store_true",
        help="Do not attach to the tmux session after spawning windows.",
    )

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.subcommand == "prompt":
        print(MASTER_ENGINEERING_PROMPT)
        return 0

    if args.subcommand == "script":
        launcher = TmuxFleetLauncher()
        script_text = launcher.generate_bash_script(
            session_name=args.session,
            claude_count=args.claude_count,
            antigravity_count=args.antigravity_count,
            enter_remote_control=not args.no_remote_control,
            isolate_worktrees=args.isolate_worktrees,
        )
        print(script_text, end="")
        return 0

    if args.subcommand == "manifest":
        allocator = FleetWorktreeAllocator(session_name=args.session)
        slots = allocator.allocate_slots(
            claude_count=args.claude_count,
            antigravity_count=args.antigravity_count,
        )
        bridge = RemoteControlBridge()
        print(bridge.to_json(slots=slots, session_name=args.session))
        return 0

    if args.subcommand == "launch":
        launcher = TmuxFleetLauncher()
        dry_run = not args.execute
        result = launcher.launch(
            session_name=args.session,
            claude_count=args.claude_count,
            antigravity_count=args.antigravity_count,
            enter_remote_control=not args.no_remote_control,
            isolate_worktrees=args.isolate_worktrees,
            dry_run=dry_run,
            attach=not args.no_attach,
        )
        print(json.dumps(result, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
