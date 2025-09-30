"""
Git Operations Utilities for YACL

This module provides Git operations for managing save game timelines.
Uses high-level dulwich APIs for robust git operations.
"""

import logging
from typing import Optional, List, Dict
from datetime import datetime
from dulwich.repo import Repo
from dulwich import porcelain
from dulwich.refs import LOCAL_BRANCH_PREFIX
from dulwich.objectspec import parse_commit

logger = logging.getLogger("YACL")

def get_current_branch_name(repo: Repo) -> Optional[str]:
    """
    Get the current branch name from a repository using dulwich's high-level API.

    Args:
        repo: The Git repository

    Returns:
        Current branch name or None if not found
    """
    try:
        # Use dulwich's porcelain.active_branch function
        branch_name = porcelain.active_branch(repo)
        if isinstance(branch_name, bytes):
            return branch_name.decode()
        elif isinstance(branch_name, str):
            return branch_name
        else:
            return str(branch_name) if branch_name is not None else None
    except (KeyError, IndexError, ValueError) as e:
        logger.debug(f"Could not determine current branch: {e}")
        return None
    except Exception as e:
        logger.warning(f"Failed to get current branch name: {e}")
        return None


def get_all_branches(repo: Repo) -> List[str]:
    """
    Get all branch names from a repository using dulwich's high-level API.

    Args:
        repo: The Git repository

    Returns:
        List of branch names
    """
    try:
        # Use dulwich's porcelain.branch_list function
        branches = porcelain.branch_list(repo)
        # Convert bytes to strings if needed
        result = []
        for branch in branches:
            if isinstance(branch, bytes):
                result.append(branch.decode())
            else:
                result.append(str(branch))
        return result
    except Exception as e:
        logger.warning(f"Failed to get branches: {e}")
        return []


def branch_exists(repo: Repo, branch_name: str) -> bool:
    """
    Check if a branch exists in the repository using dulwich's refs API.

    Args:
        repo: The Git repository
        branch_name: Name of the branch to check

    Returns:
        True if branch exists, False otherwise
    """
    try:
        # Use dulwich's refs container with proper branch prefix
        branch_ref = LOCAL_BRANCH_PREFIX + branch_name.encode()
        return branch_ref in repo.refs
    except Exception as e:
        logger.warning(f"Failed to check if branch exists: {e}")
        return False


def get_current_commit_hash(repo: Repo) -> Optional[str]:
    """
    Get the current commit hash (HEAD) using dulwich's repo.head() method.

    Args:
        repo: The Git repository

    Returns:
        Current commit hash or None if not found
    """
    try:
        # Use dulwich's built-in head() method
        head_sha = repo.head()
        if isinstance(head_sha, bytes):
            return head_sha.decode()
        else:
            return str(head_sha)
    except Exception as e:
        logger.warning(f"Failed to get current commit hash: {e}")
        return None


def get_commit_info(repo: Repo, commit_hash: str) -> Optional[Dict]:
    """
    Get commit information for a specific commit hash using dulwich's parse_commit.

    Args:
        repo: The Git repository
        commit_hash: The commit hash to get info for

    Returns:
        Dictionary with commit info or None if not found
    """
    try:
        # Use dulwich's parse_commit function for robust commit parsing
        commit_obj = parse_commit(repo, commit_hash)

        return {
            "hash": commit_obj.id.decode(),
            "timestamp": datetime.fromtimestamp(commit_obj.commit_time),
            "message": commit_obj.message.decode().strip(),
            "author": commit_obj.author.decode(),
            "parent_hashes": [parent.decode() for parent in commit_obj.parents]
        }
    except Exception as e:
        logger.warning(f"Failed to get commit info for {commit_hash}: {e}")
        return None


def get_commit_history(repo: Repo, branch_name: str = None, limit: int = 50) -> List[Dict]:
    """
    Get commit history for a branch using dulwich's walker.

    Args:
        repo: The Git repository
        branch_name: Name of the branch (defaults to current branch)
        limit: Maximum number of commits to retrieve

    Returns:
        List of commit info dictionaries in chronological order (most recent first)
    """
    try:
        if branch_name:
            # Get specific branch
            branch_ref = LOCAL_BRANCH_PREFIX + branch_name.encode()
            if branch_ref not in repo.refs:
                logger.warning(f"Branch {branch_name} not found")
                return []
            commit_id = repo.refs[branch_ref]
        else:
            # Get current HEAD
            commit_id = repo.head()

        # Use dulwich's walker to get commit history
        walker = repo.get_walker([commit_id], max_entries=limit)

        commits = []
        for entry in walker:
            commit = entry.commit
            commit_info = {
                "hash": commit.id.decode(),
                "timestamp": datetime.fromtimestamp(commit.commit_time),
                "message": commit.message.decode().strip(),
                "author": commit.author.decode(),
                "parent_hashes": [parent.decode() for parent in commit.parents]
            }
            commits.append(commit_info)

        return commits

    except Exception as e:
        logger.warning(f"Failed to get commit history: {e}")
        return []


def stage_all_changes(repo: Repo) -> bool:
    """
    Stage all changes in the working directory using dulwich, excluding Git metadata files.

    Args:
        repo: The Git repository

    Returns:
        True if staging was successful, False otherwise
    """
    try:
        # Get the repository working directory
        from pathlib import Path
        repo_path = Path(repo.path).parent if repo.path.endswith('.git') else Path(repo.path)

        # Collect files to stage, excluding Git metadata
        files_to_stage = []
        for file_path in repo_path.rglob('*'):
            if (file_path.is_file() and
                file_path.name != ".git" and  # Skip worktree .git file
                not file_path.name.startswith('.git')):  # Skip other git files
                # Get relative path from repo root
                rel_path = file_path.relative_to(repo_path)
                files_to_stage.append(str(rel_path))

        # Stage the files
        if files_to_stage:
            porcelain.add(repo, files_to_stage)

        return True
    except Exception as e:
        logger.warning(f"Failed to stage changes: {e}")
        return False


def create_commit(repo: Repo, message: str, author: str = "YACL Timeline Manager") -> Optional[str]:
    """
    Create a new commit with the staged changes using dulwich.

    Args:
        repo: The Git repository
        message: Commit message
        author: Author name and email

    Returns:
        Commit hash if successful, None otherwise
    """
    try:
        # Use dulwich's porcelain.commit to create the commit
        commit_id = porcelain.commit(repo, message=message.encode(), author=author.encode())
        return commit_id.decode()
    except Exception as e:
        logger.warning(f"Failed to create commit: {e}")
        return None


def reset_to_commit(repo: Repo, commit_hash: str, hard: bool = True) -> bool:
    """
    Reset the repository to a specific commit using dulwich.

    Args:
        repo: The Git repository
        commit_hash: The commit hash to reset to
        hard: Whether to perform a hard reset (discard working directory changes)

    Returns:
        True if reset was successful, False otherwise
    """
    try:
        # Use dulwich's porcelain.reset to reset to the commit
        if hard:
            porcelain.reset(repo, "hard", commit_hash.encode())
        else:
            porcelain.reset(repo, "mixed", commit_hash.encode())
        return True
    except Exception as e:
        logger.warning(f"Failed to reset to commit {commit_hash}: {e}")
        return False


def checkout_commit(repo: Repo, commit_hash: str) -> bool:
    """
    Checkout a specific commit using dulwich.

    Args:
        repo: The Git repository
        commit_hash: The commit hash to checkout

    Returns:
        True if checkout was successful, False otherwise
    """
    try:
        # Use dulwich's porcelain.checkout to checkout the commit
        porcelain.checkout(repo, commit_hash.encode())
        return True
    except Exception as e:
        logger.warning(f"Failed to checkout commit {commit_hash}: {e}")
        return False


def create_branch(repo: Repo, branch_name: str, start_point: str = None) -> bool:
    """
    Create a new branch using dulwich.

    Args:
        repo: The Git repository
        branch_name: Name of the new branch
        start_point: Commit hash to start the branch from (defaults to HEAD)

    Returns:
        True if branch creation was successful, False otherwise
    """
    try:
        if start_point:
            # Create branch from specific commit
            porcelain.branch_create(repo, branch_name.encode(), start_point.encode())
        else:
            # Create branch from current HEAD
            porcelain.branch_create(repo, branch_name.encode())
        return True
    except Exception as e:
        logger.warning(f"Failed to create branch {branch_name}: {e}")
        return False


def checkout_branch(repo: Repo, branch_name: str) -> bool:
    """
    Checkout a branch using dulwich.

    Args:
        repo: The Git repository
        branch_name: Name of the branch to checkout

    Returns:
        True if checkout was successful, False otherwise
    """
    try:
        # Use dulwich's porcelain.checkout to checkout the branch
        porcelain.checkout(repo, branch_name.encode())
        return True
    except Exception as e:
        logger.warning(f"Failed to checkout branch {branch_name}: {e}")
        return False