"""
Timeline Data Models for YACL

This module contains all data classes, enums, and exceptions related to save game timelines.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

@dataclass
class Checkpoint:
    """Represents a single checkpoint(commit) in a timeline"""
    commit_hash: str
    timestamp: datetime
    message: str

@dataclass
class TimelineBranch:
    """Represents a branch in a timeline"""
    name: str
    checkpoints: Dict[str,Checkpoint]

@dataclass
class Timeline:
    """Represents a complete timeline (worktree) for a save game"""
    name: str
    save_path: Path
    worktree_path: Path
    main_branch: TimelineBranch
    current_branch: TimelineBranch
    current_checkpoint: Checkpoint
    branches: Dict[str, TimelineBranch]

