# Cataclysm Timeline Management Specification

## Overview
Implement a Git-based timeline management system for Cataclysm game saves that allows players to create, manage, and restore multiple checkpoints per world using Git worktrees.

## Background & Context
Cataclysm games store save data as directories within the `save/` folder of the userdata directory. Each save represents a world state, and the game enforces permadeath by only maintaining the latest world state. When a character dies, the world is deleted or reset.

This system aims to circumvent this limitation by providing:
- Multiple save checkpoints per world (timelines)
- Ability to branch and explore different strategies
- Safe restoration to previous game states
- Non-intrusive implementation that doesn't interfere with game mechanics

### Technical Approach
Since individual save folders may be deleted/reset by the game, we use the parent `save/` directory as the Git repository root and leverage Git worktrees to manage individual save states as separate branches.

Each savegame folder will be a separate worktree, tracking its own branches and commits. The names of the branches of each worktree will be based on the savegame name. The main branch of each worktree will be named `<savegame_name>-main`. Additional branches can be created from any commit in the main branch.

## Architecture

### File Structure
```
save/                          # Git repository root
├── .git/                     # Main Git directory
├── world1/                   # Game save folder (worktree)
├── world2/                   # Game save folder (worktree)
```

## Requirements

### Core Dependencies
- **dulwich**: All Git operations must use the dulwich library exclusively
- **Python 3.11+**: Minimum Python version for dataclass and type hints support

## POC

There is already a proof of concept implemented in the `git_poc` folder. This POC can be used as a starting point and example for the implementation.

The POC is implemented in `git_worktree_poc.py`. It creates a main repository in the `test/` folder and two worktrees in the `test/savegame01/` and `test/savegame02/` folders. The worktrees are based on the `savegame01-main` and `savegame02-main` branches, respectively.

## Implementation

The implementation is split into two main parts:
1. **Data Model**: The `yacl.models` package contains all data classes, enums, and exceptions related to save game timelines, we can adapt tose classes to our needs with new attributes or methods.
2. **Timeline Manager**: The `yacl.models.timeline_manager` module provides the `TimelineManager` class for managing save game timelines.

The `TimelineManager` can use other managers from the `yacl.models` package to get the necessary information to manage the timelines. For example, it can use the `BackupManager` to get the list of save games for each installation. And it can use the path manager to get the paths to the save game folders.