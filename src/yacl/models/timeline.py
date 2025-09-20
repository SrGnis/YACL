"""
Timeline Data Models for YACL

This module contains all data classes, enums, and exceptions related to save game timelines.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from enum import Enum

from yacl.models.game_type import GameType


class TimelineStatus(Enum):
    """Timeline status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    INITIALIZING = "initializing"


class TimelineError(Exception):
    """Base exception raised for timeline-related errors."""
    pass


class TimelineValidationError(TimelineError):
    """Exception raised for timeline validation errors."""
    pass


class TimelineRepositoryError(TimelineError):
    """Exception raised for Git repository-related errors."""
    pass


class TimelineCheckpointError(TimelineError):
    """Exception raised for checkpoint-related errors."""
    pass


class TimelineBranchError(TimelineError):
    """Exception raised for branch-related errors."""
    pass


class TimelineFileError(TimelineError):
    """Exception raised for file system-related errors."""
    pass


@dataclass
class Checkpoint:
    """Represents a single checkpoint (commit) in a timeline."""
    commit_hash: str
    timestamp: datetime
    message: str
    author: str = "YACL Timeline Manager"
    parent_hashes: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        return f"{self.commit_hash[:8]} - {self.message} ({self.timestamp.strftime('%Y-%m-%d %H:%M:%S')})"


@dataclass
class TimelineBranch:
    """Represents a branch in a timeline."""
    name: str
    checkpoints: Dict[str, Checkpoint] = field(default_factory=dict)
    head_commit: Optional[str] = None
    is_main: bool = False
    created_at: datetime = field(default_factory=datetime.now)

    def add_checkpoint(self, checkpoint: Checkpoint) -> None:
        """Add a checkpoint to this branch."""
        self.checkpoints[checkpoint.commit_hash] = checkpoint
        self.head_commit = checkpoint.commit_hash

    def get_latest_checkpoint(self) -> Optional[Checkpoint]:
        """Get the latest checkpoint in this branch."""
        if self.head_commit and self.head_commit in self.checkpoints:
            return self.checkpoints[self.head_commit]
        return None

    def __str__(self) -> str:
        return f"Branch '{self.name}' ({len(self.checkpoints)} checkpoints)"


@dataclass
class Timeline:
    """Represents a complete timeline (worktree) for a save game."""
    name: str
    game_type: GameType
    save_path: Path
    worktree_path: Path
    repository_path: Path
    main_branch: TimelineBranch
    current_branch: TimelineBranch
    current_checkpoint: Optional[Checkpoint]
    branches: Dict[str, TimelineBranch] = field(default_factory=dict)
    status: TimelineStatus = TimelineStatus.INACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Post-initialization setup."""
        # Ensure main branch is in branches dict
        if self.main_branch.name not in self.branches:
            self.branches[self.main_branch.name] = self.main_branch

        # Set main branch flag
        self.main_branch.is_main = True

    def add_branch(self, branch: TimelineBranch) -> None:
        """Add a new branch to this timeline."""
        self.branches[branch.name] = branch
        self.last_updated = datetime.now()

    def switch_branch(self, branch_name: str) -> bool:
        """Switch to a different branch."""
        if branch_name in self.branches:
            self.current_branch = self.branches[branch_name]
            latest_checkpoint = self.current_branch.get_latest_checkpoint()
            self.current_checkpoint = latest_checkpoint
            self.last_updated = datetime.now()
            return True
        return False

    def get_branch_names(self) -> List[str]:
        """Get list of all branch names."""
        return list(self.branches.keys())

    def get_main_branch_name(self) -> str:
        """Get the main branch name for this timeline."""
        return f"{self.name}-main"

    def __str__(self) -> str:
        return f"Timeline '{self.name}' ({len(self.branches)} branches, status: {self.status.value})"

