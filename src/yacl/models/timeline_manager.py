"""
Timeline Manager for YACL

This module provides the TimelineManager class for managing save game timelines.
"""

import logging
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from dulwich.repo import Repo
from dulwich import porcelain
from dulwich.errors import NotGitRepository

from yacl.models.timeline import (
    TimelineTree, Checkpoint, Timeline, TimelineStatus, TimelineError,
    TimelineValidationError, TimelineRepositoryError, TimelineCheckpointError,
    TimelineBranchError, TimelineFileError
)
from yacl.models.game_type import GameType
from yacl.models.backup import SaveGame
from yacl.services.events import EventManager, Events
from yacl.services.paths import get_paths

class TimelineManager:
    """
    Manages Git-based timelines for save games using dulwich.

    This manager handles:
    - Git repository initialization for save directories
    - Worktree creation and management for individual save games
    - Branch and commit operations for timeline checkpoints
    - Integration with the existing YACL architecture
    """

    def __init__(self, event_manager: EventManager):
        """
        Initialize the timeline manager.

        Args:
            event_manager: Event manager for component communication
        """
        self.logger = logging.getLogger("YACL")
        self.event_manager = event_manager
        self.paths = get_paths()

        # Current state
        self.timelines: Dict[GameType, Dict[str, TimelineTree]] = {}
        self.repositories: Dict[GameType, Optional[Repo]] = {}

        self._is_initialized = False

        self.logger.info("Timeline manager initialized")

    def initialize(self) -> bool:
        """
        Initialize the timeline manager.

        This method should be called after the installation manager has been initialized.
        It will scan for existing save directories and initialize Git repositories as needed.

        Returns:
            bool: True if successful
        """
        try:
            self.logger.info("Initializing timeline manager...")

            # Initialize repositories for all game types
            for game_type in GameType.all:
                self._initialize_game_repository(game_type)

            self._is_initialized = True
            self.logger.info("Timeline manager initialization completed")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize timeline manager: {e}")
            return False

    def _validate_save_game(self, save_game: SaveGame) -> None:
        """
        Validate a save game for timeline operations.

        Args:
            save_game: The save game to validate

        Raises:
            TimelineValidationError: If validation fails
        """
        if not save_game:
            raise TimelineValidationError("Save game cannot be None")

        if not save_game.is_valid:
            raise TimelineValidationError(f"Save game '{save_game.name}' is not valid")

        if not save_game.exists:
            raise TimelineFileError(f"Save game directory does not exist: {save_game.path}")

        # Check if save game directory has any files
        try:
            if not any(save_game.path.iterdir()):
                raise TimelineValidationError(f"Save game directory is empty: {save_game.path}")
        except PermissionError:
            raise TimelineFileError(f"Permission denied accessing save game directory: {save_game.path}")

    def _validate_checkpoint_message(self, message: str) -> None:
        """
        Validate a checkpoint message.

        Args:
            message: The checkpoint message to validate

        Raises:
            TimelineValidationError: If validation fails
        """
        if not message or not message.strip():
            raise TimelineValidationError("Checkpoint message cannot be empty")

        if len(message.strip()) > 500:
            raise TimelineValidationError("Checkpoint message cannot exceed 500 characters")

    def _validate_branch_name(self, branch_name: str) -> None:
        """
        Validate a branch name.

        Args:
            branch_name: The branch name to validate

        Raises:
            TimelineValidationError: If validation fails
        """
        if not branch_name or not branch_name.strip():
            raise TimelineValidationError("Branch name cannot be empty")

        # Git branch name validation
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', branch_name):
            raise TimelineValidationError(
                "Branch name can only contain letters, numbers, hyphens, and underscores"
            )

        if len(branch_name) > 100:
            raise TimelineValidationError("Branch name cannot exceed 100 characters")

        # Reserved names
        reserved_names = ['HEAD', 'master', 'main']
        if branch_name in reserved_names:
            raise TimelineValidationError(f"Branch name '{branch_name}' is reserved")

    def _validate_repository(self, game_type: GameType) -> None:
        """
        Validate that a repository exists and is accessible for a game type.

        Args:
            game_type: The game type to validate

        Raises:
            TimelineRepositoryError: If validation fails
        """
        if game_type not in self.repositories:
            raise TimelineRepositoryError(f"No repository initialized for game type: {game_type.name}")

        repo = self.repositories[game_type]
        if not repo:
            raise TimelineRepositoryError(f"Repository not available for game type: {game_type.name}")

        # Check if repository path exists and is accessible
        try:
            repo_path = Path(repo.path)
            if not repo_path.exists():
                raise TimelineRepositoryError(f"Repository path does not exist: {repo_path}")

            if not (repo_path / '.git').exists():
                raise TimelineRepositoryError(f"Invalid Git repository: {repo_path}")

        except Exception as e:
            raise TimelineRepositoryError(f"Error accessing repository: {e}")

    def discover_save_games(self, game_type: GameType) -> List[SaveGame]:
        """
        Discover all save games for a specific game type.

        Args:
            game_type: The game type to discover save games for

        Returns:
            List of SaveGame objects
        """
        save_games = []
        try:
            saves_dir = self.paths.get_saves_dir(game_type.name)

            if not saves_dir.exists():
                return save_games

            for save_dir in saves_dir.iterdir():
                if save_dir.is_dir() and save_dir.name != ".git":
                    save_game = SaveGame(
                        name=save_dir.name,
                        game=game_type,
                        path=save_dir
                    )
                    save_games.append(save_game)

        except Exception as e:
            self.logger.error(f"Error discovering save games for {game_type.name}: {e}")

        return save_games

    def get_save_games_without_timelines(self, game_type: GameType) -> List[SaveGame]:
        """
        Get save games that don't have timelines yet.

        Args:
            game_type: The game type to check

        Returns:
            List of SaveGame objects without timelines
        """
        all_saves = self.discover_save_games(game_type)
        existing_timelines = self.get_timelines_for_game(game_type)

        return [save for save in all_saves if save.name not in existing_timelines]

    def _initialize_game_repository(self, game_type: GameType) -> bool:
        """
        Initialize Git repository for a specific game type.

        Args:
            game_type: The game type to initialize repository for

        Returns:
            bool: True if successful
        """
        try:
            saves_dir = self.paths.get_saves_dir(game_type.name)

            # Initialize empty state for this game type
            self.timelines[game_type] = {}
            self.repositories[game_type] = None

            if not saves_dir.exists():
                self.logger.debug(f"Saves directory does not exist for {game_type.name}: {saves_dir}")
                return True

            # Check if repository already exists
            try:
                repo = Repo(str(saves_dir))
                self.repositories[game_type] = repo
                self.logger.info(f"Found existing Git repository for {game_type.name}")

                # Load existing timelines
                self._load_existing_timeline_trees(game_type, repo)

            except NotGitRepository:
                # Initialize new repository
                self.logger.info(f"Initializing new Git repository for {game_type.name}")
                repo = porcelain.init(str(saves_dir))
                self.repositories[game_type] = repo

                # Create a first empty commit
                porcelain.commit(repo.path, message="Initial commit".encode())
                self.logger.info(f"Created initial commit for {game_type.name}")

            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize repository for {game_type.name}: {e}")
            return False


    def _load_existing_timeline_trees(self, game_type: GameType, repo: Repo) -> None:
        """
        Load existing timeline trees from a Git repository.

        Args:
            game_type: The game type
            repo: The Git repository
        """
        try:
            self.logger.debug(f"Loading existing timeline trees for {game_type.name}")
            self.logger.debug(f"Repository path: {repo.path}")

            # Get all worktrees
            worktrees = porcelain.worktree_list(str(repo.path))
            self.logger.debug(f"Found {len(worktrees)} worktrees")

            for worktree_info in worktrees:
                worktree_path = Path(worktree_info.path)
                self.logger.debug(f"Processing worktree: {worktree_path}")

                # Skip the main repository directory
                if worktree_path == Path(repo.path):
                    self.logger.debug("Skipping main repository directory")
                    continue

                # Extract save game name from worktree path
                save_name = worktree_path.name
                self.logger.debug(f"Processing save game: {save_name}")

                # Load timeline tree for this save game
                timeline_tree = TimelineTree.from_worktree(worktree_path, game_type)
                if timeline_tree:
                    self.logger.debug(f"Successfully loaded timeline tree for {save_name}")
                    self.timelines[game_type][save_name] = timeline_tree
                else:
                    self.logger.debug(f"Failed to load timeline tree for {save_name}")

            self.logger.debug(f"Finished loading timeline trees for {game_type.name}")

        except Exception as e:
            self.logger.warning(f"Failed to load existing timelines for {game_type.name}: {e}")


    def load_timelines_trees(self, game_type: GameType) -> bool:
        """
        Load timelines for a specific game type.

        Args:
            game_type: The game type to load timelines for

        Returns:
            bool: True if successful
        """
        try:
            self.logger.info(f"Loading timelines for {game_type.name}")

            if game_type not in self.repositories or not self.repositories[game_type]:
                self.logger.warning(f"No repository found for {game_type.name}")
                return False

            repo = self.repositories[game_type]
            if repo:  # Type guard to ensure repo is not None
                self._load_existing_timeline_trees(game_type, repo)

            return True
        except Exception as e:
            self.logger.error(f"Failed to load timelines for {game_type.name}: {e}")
            return False

    def create_timeline(self, save_game: SaveGame) -> Optional[TimelineTree]:
        """
        Create a new timeline for a save game.

        This method will create a new worktree for the save game and initialize the main branch.

        Args:
            save_game: The save game to create a timeline for

        Returns:
            Timeline object if successful, None otherwise
        """
        try:
            self.logger.info(f"Creating timeline for {save_game.name}")

            # Get the repository for this game type
            if save_game.game not in self.repositories or not self.repositories[save_game.game]:
                raise TimelineError(f"No repository found for {save_game.game.name}")

            repo = self.repositories[save_game.game]
            if not repo:
                raise TimelineError(f"Repository is None for {save_game.game.name}")

            # Check if timeline already exists
            if save_game.game in self.timelines and save_game.name in self.timelines[save_game.game]:
                raise TimelineError(f"Timeline already exists for {save_game.name}")

            # Create worktree
            timeline = self._create_worktree_timeline(save_game, repo)

            # Add to timelines
            if save_game.game not in self.timelines:
                self.timelines[save_game.game] = {}
            self.timelines[save_game.game][save_game.name] = timeline

            # Emit timeline created event
            if self.event_manager:
                self.event_manager.emit(Events.TIMELINE_CREATED, timeline=timeline)

            self.logger.info(f"Successfully created timeline for {save_game.name}")
            return timeline

        except Exception as e:
            self.logger.error(f"Failed to create timeline for {save_game.name}: {e}")
            return None

    def _create_worktree_timeline(self, save_game: SaveGame, repo: Repo) -> TimelineTree:
        """
        Create a new worktree and timeline tree for a save game.

        Args:
            save_game: The save game to create timeline for
            repo: The main Git repository

        Returns:
            Timeline object
        """
        # Temporarily move existing directory if it exists
        temp_dir = None
        if save_game.path.exists():
            temp_dir = Path(tempfile.mkdtemp())
            # Move all contents to temp directory
            for item in save_game.path.iterdir():
                shutil.move(str(item), str(temp_dir))
            # Remove the empty directory
            save_game.path.rmdir()

        # Create worktree with new branch using dulwich
        main_branch_name = f"{save_game.name}-main"
        porcelain.worktree_add(
            repo=repo.path,
            path=str(save_game.path),
            branch=main_branch_name
        )

        # Move files back if they were temporarily moved
        if temp_dir:
            for item in temp_dir.iterdir():
                shutil.move(str(item), str(save_game.path))
            # Clean up temp directory
            temp_dir.rmdir()

        # Open the worktree repository and stage/commit files
        wt_repo = Repo(str(save_game.path))
        worktree = wt_repo.get_worktree()

        # Stage all files in the save game directory
        file_names = []
        for file_path in save_game.path.iterdir():
            if file_path.is_file():
                file_names.append(file_path.name)

        if file_names:
            worktree.stage(file_names)
            commit_id = worktree.commit(message=f"Initial commit for {save_game.name}".encode())

            # Create checkpoint
            checkpoint = Checkpoint(
                commit_hash=commit_id.decode(),
                timestamp=datetime.now(),
                message=f"Initial commit for {save_game.name}",
                author="YACL Timeline Manager"
            )
        else:
            # Create empty commit if no files
            commit_id = worktree.commit(message=f"Empty initial commit for {save_game.name}".encode())
            checkpoint = Checkpoint(
                commit_hash=commit_id.decode(),
                timestamp=datetime.now(),
                message=f"Empty initial commit for {save_game.name}",
                author="YACL Timeline Manager"
            )

        # Create timeline branches
        main_branch = Timeline(name=main_branch_name, is_main=True)
        main_branch.add_checkpoint(checkpoint)

        # Create timeline
        timeline = TimelineTree(
            name=save_game.name,
            game_type=save_game.game,
            save_path=save_game.path,
            worktree_path=save_game.path,
            repository_path=Path(repo.path),
            main_branch=main_branch,
            current_branch=main_branch,
            current_checkpoint=checkpoint,
            status=TimelineStatus.ACTIVE
        )

        return timeline

    def delete_timeline(self, save_game: SaveGame) -> bool:
        """
        Delete a timeline for a save game.

        This method will delete the worktree for the save game and remove the timeline from the manager.

        Args:
            save_game: The save game to delete the timeline for

        Returns:
            bool: True if successful
        """
        try:
            self.logger.info(f"Deleting timeline for {save_game.name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete timeline for {save_game.name}: {e}")
            return False

    def create_checkpoint(self, save_game: SaveGame, message: str) -> Optional[Checkpoint]:
        """
        Create a new checkpoint for a save game.

        This method will create a new commit in the current branch of the timeline.

        Args:
            save_game: The save game to create a checkpoint for
            message: The commit message

        Returns:
            Checkpoint object if successful, None otherwise
        """
        try:
            # Validate inputs
            self._validate_save_game(save_game)
            self._validate_checkpoint_message(message)
            self._validate_repository(save_game.game)

            self.logger.info(f"Creating checkpoint for {save_game.name}: {message}")

            # Get the timeline for this save game
            if save_game.game not in self.timelines or save_game.name not in self.timelines[save_game.game]:
                raise TimelineCheckpointError(f"No timeline found for {save_game.name}")

            timeline = self.timelines[save_game.game][save_game.name]

            # Open the worktree repository
            wt_repo = Repo(str(timeline.worktree_path))
            worktree = wt_repo.get_worktree()

            # Stage all changes
            file_names = []
            for file_path in timeline.worktree_path.rglob('*'):
                if file_path.is_file() and file_path.name != "README.md":  # Skip the initial README
                    # Get relative path from worktree root
                    rel_path = file_path.relative_to(timeline.worktree_path)
                    file_names.append(str(rel_path))

            if file_names:
                worktree.stage(file_names)

            # Create commit
            commit_id = worktree.commit(message=message.encode())

            # Create checkpoint
            checkpoint = Checkpoint(
                commit_hash=commit_id.decode(),
                timestamp=datetime.now(),
                message=message,
                author="YACL Timeline Manager"
            )

            # Add checkpoint to current branch
            timeline.current_branch.add_checkpoint(checkpoint)
            timeline.current_checkpoint = checkpoint
            timeline.last_updated = datetime.now()

            # Emit checkpoint created event
            if self.event_manager:
                self.event_manager.emit(Events.CHECKPOINT_CREATED, checkpoint=checkpoint, timeline=timeline)

            self.logger.info(f"Successfully created checkpoint for {save_game.name}")
            return checkpoint

        except Exception as e:
            self.logger.error(f"Failed to create checkpoint for {save_game.name}: {e}")
            return None
        
    def restore_checkpoint(self, save_game: SaveGame, checkpoint: Checkpoint) -> bool:
        """
        Restore a checkpoint for a save game.

        This method will checkout the specified commit and optionally create a new branch.
        If commits exist in the current branch after the checkpoint, a new branch will be created.

        Args:
            save_game: The save game to restore
            checkpoint: The checkpoint to restore to

        Returns:
            bool: True if successful
        """
        try:
            self.logger.info(f"Restoring checkpoint {checkpoint.commit_hash[:8]} for {save_game.name}")

            # Get the timeline for this save game
            if save_game.game not in self.timelines or save_game.name not in self.timelines[save_game.game]:
                raise TimelineError(f"No timeline found for {save_game.name}")

            timeline = self.timelines[save_game.game][save_game.name]

            # Open the worktree repository
            wt_repo = Repo(str(timeline.worktree_path))

            # Checkout the specific commit
            porcelain.checkout(wt_repo, checkpoint.commit_hash)

            # Update timeline state
            timeline.current_checkpoint = checkpoint
            timeline.last_updated = datetime.now()

            # Emit checkpoint restored event
            if self.event_manager:
                self.event_manager.emit(Events.CHECKPOINT_RESTORED, checkpoint=checkpoint, timeline=timeline)

            self.logger.info(f"Successfully restored checkpoint for {save_game.name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to restore checkpoint for {save_game.name}: {e}")
            return False

    def get_timeline(self, save_game: SaveGame) -> Optional[TimelineTree]:
        """
        Get the timeline for a specific save game.

        Args:
            save_game: The save game to get timeline for

        Returns:
            Timeline object if found, None otherwise
        """
        if save_game.game in self.timelines and save_game.name in self.timelines[save_game.game]:
            return self.timelines[save_game.game][save_game.name]
        return None

    def get_timelines_for_game(self, game_type: GameType) -> Dict[str, TimelineTree]:
        """
        Get all timelines for a specific game type.

        Args:
            game_type: The game type to get timelines for

        Returns:
            Dictionary of save name to Timeline objects
        """
        return self.timelines.get(game_type, {})

    def create_branch(self, save_game: SaveGame, branch_name: str, from_checkpoint: Optional[Checkpoint] = None) -> bool:
        """
        Create a new branch in a timeline.

        Args:
            save_game: The save game to create branch for
            branch_name: Name of the new branch
            from_checkpoint: Checkpoint to branch from (defaults to current)

        Returns:
            bool: True if successful
        """
        try:
            # Validate inputs
            self._validate_save_game(save_game)
            self._validate_branch_name(branch_name)
            self._validate_repository(save_game.game)

            self.logger.info(f"Creating branch '{branch_name}' for {save_game.name}")

            # Get the timeline for this save game
            timeline = self.get_timeline(save_game)
            if not timeline:
                raise TimelineBranchError(f"No timeline found for {save_game.name}")

            # Check if branch already exists
            if branch_name in timeline.branches:
                raise TimelineBranchError(f"Branch '{branch_name}' already exists")

            # Open the worktree repository
            wt_repo = Repo(str(timeline.worktree_path))

            # Determine the commit to branch from
            if from_checkpoint:
                commit_hash = from_checkpoint.commit_hash
            else:
                commit_hash = timeline.current_checkpoint.commit_hash if timeline.current_checkpoint else None

            if not commit_hash:
                raise TimelineError("No commit to branch from")

            # Create new branch at the specified commit
            new_branch_ref = f"refs/heads/{branch_name}".encode()
            wt_repo.refs[new_branch_ref] = commit_hash.encode()

            # Create timeline branch
            new_branch = Timeline(name=branch_name)
            if from_checkpoint:
                new_branch.add_checkpoint(from_checkpoint)

            timeline.add_branch(new_branch)

            # Emit branch created event
            if self.event_manager:
                self.event_manager.emit(Events.BRANCH_CREATED, branch=new_branch, timeline=timeline)

            self.logger.info(f"Successfully created branch '{branch_name}' for {save_game.name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create branch '{branch_name}' for {save_game.name}: {e}")
            return False

    def switch_branch(self, save_game: SaveGame, branch_name: str) -> bool:
        """
        Switch to a different branch in a timeline.

        Args:
            save_game: The save game to switch branch for
            branch_name: Name of the branch to switch to

        Returns:
            bool: True if successful
        """
        try:
            self.logger.info(f"Switching to branch '{branch_name}' for {save_game.name}")

            # Get the timeline for this save game
            timeline = self.get_timeline(save_game)
            if not timeline:
                raise TimelineError(f"No timeline found for {save_game.name}")

            # Check if branch exists
            if branch_name not in timeline.branches:
                raise TimelineError(f"Branch '{branch_name}' does not exist")

            # Open the worktree repository
            wt_repo = Repo(str(timeline.worktree_path))

            # Checkout the branch
            porcelain.checkout(wt_repo, branch_name)

            # Update timeline state
            timeline.switch_branch(branch_name)

            # Emit branch switched event
            if self.event_manager:
                self.event_manager.emit(Events.BRANCH_SWITCHED, branch_name=branch_name, timeline=timeline)

            self.logger.info(f"Successfully switched to branch '{branch_name}' for {save_game.name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to switch to branch '{branch_name}' for {save_game.name}: {e}")
            return False

    def get_repository_status(self, save_game: SaveGame) -> Optional[Dict[str, Any]]:
        """
        Get the Git repository status for a save game.

        Args:
            save_game: The save game to get status for

        Returns:
            Dictionary with status information or None if error
        """
        try:
            timeline = self.get_timeline(save_game)
            if not timeline:
                return None

            # Open the worktree repository
            wt_repo = Repo(str(timeline.worktree_path))

            # Get status using dulwich
            status = porcelain.status(wt_repo)

            return {
                "staged": list(status.staged),
                "unstaged": list(status.unstaged),
                "untracked": list(status.untracked),
                "current_branch": timeline.current_branch.name,
                "current_commit": timeline.current_checkpoint.commit_hash if timeline.current_checkpoint else None,
                "has_changes": bool(status.staged or status.unstaged or status.untracked)
            }

        except Exception as e:
            self.logger.error(f"Failed to get repository status for {save_game.name}: {e}")
            return None

    def get_commit_history(self, save_game: SaveGame, branch_name: Optional[str] = None, limit: int = 50) -> List[Checkpoint]:
        """
        Get commit history for a save game timeline.

        Args:
            save_game: The save game to get history for
            branch_name: Specific branch to get history for (defaults to current)
            limit: Maximum number of commits to return

        Returns:
            List of Checkpoint objects
        """
        try:
            timeline = self.get_timeline(save_game)
            if not timeline:
                return []

            # Use specified branch or current branch
            if branch_name and branch_name in timeline.branches:
                branch = timeline.branches[branch_name]
            else:
                branch = timeline.current_branch

            # Open the worktree repository
            wt_repo = Repo(str(timeline.worktree_path))

            # Get branch head commit
            branch_ref = f"refs/heads/{branch.name}".encode()
            if branch_ref not in wt_repo.refs:
                return []

            commit_id = wt_repo.refs[branch_ref]
            walker = wt_repo.get_walker([commit_id], max_entries=limit)

            checkpoints = []
            for entry in walker:
                commit = entry.commit
                checkpoint = Checkpoint(
                    commit_hash=commit.id.decode(),
                    timestamp=datetime.fromtimestamp(commit.commit_time),
                    message=commit.message.decode().strip(),
                    author=commit.author.decode(),
                    parent_hashes=[parent.decode() for parent in commit.parents]
                )
                checkpoints.append(checkpoint)

            return checkpoints

        except Exception as e:
            self.logger.error(f"Failed to get commit history for {save_game.name}: {e}")
            return []

    def has_uncommitted_changes(self, save_game: SaveGame) -> bool:
        """
        Check if a save game has uncommitted changes.

        Args:
            save_game: The save game to check

        Returns:
            bool: True if there are uncommitted changes
        """
        status = self.get_repository_status(save_game)
        return status["has_changes"] if status else False

    def get_timeline_info(self, save_game: SaveGame) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive timeline information for a save game.

        Args:
            save_game: The save game to get info for

        Returns:
            Dictionary with timeline information or None if error
        """
        try:
            timeline = self.get_timeline(save_game)
            if not timeline:
                return None

            status = self.get_repository_status(save_game)

            return {
                "name": timeline.name,
                "game_type": timeline.game_type.name,
                "status": timeline.status.value,
                "created_at": timeline.created_at.isoformat(),
                "last_updated": timeline.last_updated.isoformat(),
                "current_branch": timeline.current_branch.name,
                "current_checkpoint": {
                    "hash": timeline.current_checkpoint.commit_hash,
                    "message": timeline.current_checkpoint.message,
                    "timestamp": timeline.current_checkpoint.timestamp.isoformat()
                } if timeline.current_checkpoint else None,
                "branches": [
                    {
                        "name": branch.name,
                        "is_main": branch.is_main,
                        "checkpoint_count": len(branch.checkpoints),
                        "head_commit": branch.head_commit
                    }
                    for branch in timeline.branches.values()
                ],
                "repository_status": status
            }

        except Exception as e:
            self.logger.error(f"Failed to get timeline info for {save_game.name}: {e}")
            return None

    def shutdown(self) -> None:
        """Shutdown the timeline manager and clean up resources."""
        try:
            self.logger.info("Shutting down timeline manager...")

            # Clear all timelines
            self.timelines.clear()
            self.repositories.clear()

            self.logger.info("Timeline manager shutdown complete")

        except Exception as e:
            self.logger.error(f"Error during timeline manager shutdown: {e}")


# Global timeline manager instance
_timeline_manager: Optional[TimelineManager] = None


def initialize_timeline_manager(event_manager: EventManager) -> bool:
    """
    Initialize the global timeline manager.

    Args:
        event_manager: Event manager for component communication

    Returns:
        bool: True if initialization was successful
    """
    global _timeline_manager

    try:
        if _timeline_manager is not None:
            logging.getLogger("YACL").warning("Timeline manager already initialized")
            return True

        _timeline_manager = TimelineManager(event_manager)
        success = _timeline_manager.initialize()

        if success:
            logging.getLogger("YACL").info("Global timeline manager initialized")
        else:
            logging.getLogger("YACL").error("Failed to initialize global timeline manager")

        return success

    except Exception as e:
        logging.getLogger("YACL").error(f"Failed to initialize timeline manager: {e}")
        return False


def get_timeline_manager() -> TimelineManager:
    """
    Get the global timeline manager instance.

    Returns:
        TimelineManager: Global timeline manager instance

    Raises:
        RuntimeError: If timeline manager hasn't been initialized
    """
    if _timeline_manager is None:
        raise RuntimeError("Timeline manager not initialized")
    return _timeline_manager


def shutdown_timeline_manager():
    """Shutdown the global timeline manager instance."""
    global _timeline_manager
    if _timeline_manager:
        _timeline_manager.shutdown()
        _timeline_manager = None
