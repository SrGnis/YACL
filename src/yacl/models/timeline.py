"""
Timeline Data Models for YACL

This module contains all data classes, enums, and exceptions related to save game timelines.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from enum import Enum

from dulwich.repo import Repo

from yacl.models.game_type import GameType
from yacl.utils.git_ops import (
    get_current_branch_name,
    get_all_branches,
    branch_exists,
    get_current_commit_hash,
    get_commit_info
)

logger = logging.getLogger("YACL")


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
class Timeline:
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
class TimelineTree:
    """Represents a complete timeline (worktree) for a save game."""
    name: str
    game_type: GameType
    save_path: Path
    worktree_path: Path
    repository_path: Path
    main_branch: Timeline
    current_branch: Timeline
    current_checkpoint: Optional[Checkpoint]
    branches: Dict[str, Timeline] = field(default_factory=dict)
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

    def add_branch(self, branch: Timeline) -> None:
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

    def __str__(self) -> str:
        return f"Timeline '{self.name}' ({len(self.branches)} branches, status: {self.status.value})"
    
    @classmethod
    def from_worktree(cls, worktree_path: Path, game_type: GameType) -> "TimelineTree":
        """
        Create a timeline tree from an existing worktree.

        This method will load the existing branches, checkpoints from the worktree.

        Args:
            worktree_path: Path to the worktree
            game_type: The game type

        Returns:
            TimelineTree object

        Raises:
            TimelineRepositoryError: If repository cannot be opened
            TimelineValidationError: If main branch doesn't exist
            TimelineBranchError: If current branch cannot be determined
            TimelineCheckpointError: If current checkpoint cannot be loaded
        """
        logger.debug(f"Loading timeline from worktree: {worktree_path}")

        try:
            # Open the worktree repository
            worktree_repo = Repo(str(worktree_path))
            logger.debug(f"Successfully opened worktree repository at {worktree_path}")
        except Exception as e:
            logger.error(f"Failed to open worktree repository at {worktree_path}: {e}")
            raise TimelineRepositoryError(f"Failed to open worktree repository at {worktree_path}: {e}")

        # Extract save name from worktree path
        save_name = worktree_path.name
        logger.debug(f"Extracted save name: {save_name}")

        # Get all branches
        all_branches = get_all_branches(worktree_repo)
        logger.debug(f"Found branches: {all_branches}")
        if not all_branches:
            raise TimelineBranchError("No branches found in repository")

        # Validate main branch exists (named as save_name + "-main")
        main_branch_name = f"{save_name.replace(' ', '_').lower()}-main"
        logger.debug(f"Looking for main branch: {main_branch_name}")
        if not branch_exists(worktree_repo, main_branch_name):
            logger.error(f"Main branch '{main_branch_name}' does not exist. Available branches: {all_branches}")
            raise TimelineValidationError(f"Main branch '{main_branch_name}' does not exist")

        # Get current branch name
        current_branch_name = get_current_branch_name(worktree_repo)
        logger.debug(f"Current branch: {current_branch_name}")
        if not current_branch_name:
            # We're in detached HEAD state, switch back to main branch
            logger.warning("Repository is in detached HEAD state, switching to main branch")
            from yacl.utils.git_ops import checkout_branch
            if checkout_branch(worktree_repo, main_branch_name):
                current_branch_name = main_branch_name
                logger.info(f"Successfully switched to main branch: {main_branch_name}")
            else:
                raise TimelineBranchError("Could not determine current branch and failed to switch to main branch")

        # Get current checkpoint (HEAD commit)
        current_commit_hash = get_current_commit_hash(worktree_repo)
        logger.debug(f"Current commit hash: {current_commit_hash}")
        if not current_commit_hash:
            raise TimelineCheckpointError("Could not get current commit hash")

        # Get commit info for current checkpoint
        commit_info = get_commit_info(worktree_repo, current_commit_hash)
        logger.debug(f"Current commit info: {commit_info}")
        if not commit_info:
            raise TimelineCheckpointError(f"Could not get commit info for {current_commit_hash}")

        # Create current checkpoint
        current_checkpoint = Checkpoint(
            commit_hash=commit_info["hash"],
            timestamp=commit_info["timestamp"],
            message=commit_info["message"],
            author=commit_info["author"],
            parent_hashes=commit_info["parent_hashes"]
        )
        logger.debug(f"Created current checkpoint: {current_checkpoint}")

        # Create timeline branches and load their checkpoints
        branches = {}
        logger.debug("Creating timeline branches and loading checkpoints")

        # Create main branch
        logger.debug(f"Creating main branch: {main_branch_name}")
        main_branch = Timeline(name=main_branch_name, is_main=True)
        cls._load_branch_checkpoints(worktree_repo, main_branch)
        branches[main_branch_name] = main_branch
        logger.debug(f"Main branch loaded with {len(main_branch.checkpoints)} checkpoints")

        # Create current branch (if different from main)
        if current_branch_name != main_branch_name:
            logger.debug(f"Creating current branch: {current_branch_name}")
            current_branch = Timeline(name=current_branch_name)
            cls._load_branch_checkpoints(worktree_repo, current_branch)
            branches[current_branch_name] = current_branch
            logger.debug(f"Current branch loaded with {len(current_branch.checkpoints)} checkpoints")
        else:
            logger.debug("Current branch is the same as main branch")
            current_branch = main_branch

        # Load all other branches that belong to this save game
        # Only load branches that start with the save name (e.g., "savegame01-*")
        relevant_branches = [b for b in all_branches if b.startswith(f"{save_name.replace(' ', '_').lower()}-") and b not in branches]
        logger.debug(f"Loading remaining relevant branches: {relevant_branches}")
        for branch_name in relevant_branches:
            logger.debug(f"Loading branch: {branch_name}")
            branch = Timeline(name=branch_name)
            cls._load_branch_checkpoints(worktree_repo, branch)
            branches[branch_name] = branch
            logger.debug(f"Branch {branch_name} loaded with {len(branch.checkpoints)} checkpoints")

        # Determine repository path (parent of worktree for worktrees, or worktree itself for main repo)
        repository_path = worktree_path.parent if worktree_path.name != ".git" else worktree_path
        logger.debug(f"Repository path: {repository_path}")

        # Create timeline tree
        logger.debug("Creating TimelineTree object")
        timeline_tree = cls(
            name=save_name,
            game_type=game_type,
            save_path=worktree_path,
            worktree_path=worktree_path,
            repository_path=repository_path,
            main_branch=main_branch,
            current_branch=current_branch,
            current_checkpoint=current_checkpoint,
            branches=branches,
            status=TimelineStatus.ACTIVE
        )

        logger.info(f"Successfully created timeline tree for {save_name} with {len(branches)} branches")
        return timeline_tree

    @staticmethod
    def _load_branch_checkpoints(repo: Repo, branch: Timeline) -> None:
        """
        Load checkpoints for a specific branch.

        Args:
            repo: The Git repository
            branch: The branch to load checkpoints for
        """
        logger.debug(f"Loading checkpoints for branch: {branch.name}")
        try:
            branch_ref = f"refs/heads/{branch.name}".encode()
            if branch_ref not in repo.refs:
                logger.debug(f"Branch ref {branch_ref} not found in repository refs")
                return

            commit_id = repo.refs[branch_ref]
            logger.debug(f"Branch {branch.name} points to commit: {commit_id.decode()}")
            walker = repo.get_walker([commit_id])

            checkpoint_count = 0
            for entry in walker:
                commit = entry.commit
                checkpoint = Checkpoint(
                    commit_hash=commit.id.decode(),
                    timestamp=datetime.fromtimestamp(commit.commit_time),
                    message=commit.message.decode().strip(),
                    author=commit.author.decode(),
                    parent_hashes=[parent.decode() for parent in commit.parents]
                )
                branch.add_checkpoint(checkpoint)
                checkpoint_count += 1
                logger.debug(f"Added checkpoint {checkpoint.commit_hash[:8]} to branch {branch.name}")

            logger.debug(f"Loaded {checkpoint_count} checkpoints for branch {branch.name}")

        except Exception as e:
            # Log warning but don't raise - some branches might not have commits yet
            logger.warning(f"Failed to load checkpoints for branch {branch.name}: {e}")
            pass


