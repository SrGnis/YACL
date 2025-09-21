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