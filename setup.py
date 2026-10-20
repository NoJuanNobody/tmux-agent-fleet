from setuptools import find_packages, setup

setup(
    name="tmux-agent-fleet",
    version="0.1.0",
    description="Multi-agent tmux fleet launcher for 8 Claude Code + 8 Antigravity CLI sessions with worktree/port isolation and remote-control-skill integration.",
    author="Alejandro Londono",
    packages=find_packages(exclude=["tests*"]),
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "tmux-agent-fleet = tmux_agent_fleet.cli:main",
        ],
    },
)
