# Timeline Implementation Documentation

## Overview

The YACL Timeline system provides Git-based version control for Cataclysm: Dark Days Ahead save games. It allows players to create checkpoints, manage multiple branches, and restore previous game states using Git worktrees.

## Architecture

The timeline system follows YACL's MVC architectural pattern:

### Models (`src/yacl/models/`)

#### `timeline.py`
- **Checkpoint**: Represents a single save state (Git commit)
- **TimelineBranch**: Represents a branch with multiple checkpoints
- **Timeline**: Main timeline object containing branches and metadata
- **TimelineStatus**: Enum for timeline states (ACTIVE, INACTIVE, ERROR, INITIALIZING)
- **Exception Classes**: Specific exceptions for different error types

#### `timeline_manager.py`
- **TimelineManager**: Core business logic for timeline operations
- Handles Git repository operations using dulwich
- Manages timeline creation, checkpoint creation, branch management
- Provides validation and error handling

### Views (`src/yacl/views/`)

#### `tabs/timeline_tab.py`
- Main timeline UI with two-column layout
- Save games list, timeline info, checkpoints list
- Action buttons for timeline operations

#### `dialogs/`
- **CheckpointDialog**: Create checkpoints with custom messages
- **BranchDialog**: Create new branches
- **TimelineCreationDialog**: Create timelines for save games
- **RestoreConfirmationDialog**: Confirm checkpoint restoration

### Controllers (`src/yacl/controllers/`)

#### `timeline_tab_controller.py`
- Handles UI events and user interactions
- Coordinates between view and model layers
- Manages event subscriptions and business logic

## Key Features

### 1. Timeline Creation
- Automatically detects save games without timelines
- Initializes Git repository with worktree structure
- Creates main branch with initial commit

### 2. Checkpoint Management
- Create checkpoints with custom messages
- View checkpoint history and details
- Restore to any previous checkpoint
- Automatic file staging and commit creation

### 3. Branch Management
- Create branches from any checkpoint
- Switch between branches
- Maintain separate game states per branch
- Visual branch indicators in UI

### 4. Git Integration
- Uses dulwich for pure Python Git operations
- Worktree-based architecture for file management
- Proper Git commit history and metadata
- Support for merge operations

## Data Flow

1. **Initialization**: TimelineManager discovers save games and initializes repositories
2. **UI Updates**: Controller refreshes UI based on current game type and available timelines
3. **User Actions**: UI events trigger controller methods
4. **Business Logic**: Controller calls TimelineManager methods
5. **Git Operations**: TimelineManager performs Git operations via dulwich
6. **Event Emission**: Success/failure events update UI and other components

## File Structure

```
saves/
├── game_name/
│   ├── save_game_1/          # Original save directory
│   └── save_game_2/
└── .yacl_timelines/
    └── game_name/
        ├── repositories/      # Bare Git repositories
        │   ├── save_game_1.git/
        │   └── save_game_2.git/
        └── worktrees/        # Git worktrees (active save states)
            ├── save_game_1/
            └── save_game_2/
```

## Error Handling

The system includes comprehensive error handling with specific exception types:

- **TimelineValidationError**: Input validation failures
- **TimelineRepositoryError**: Git repository issues
- **TimelineCheckpointError**: Checkpoint creation/restoration problems
- **TimelineBranchError**: Branch management issues
- **TimelineFileError**: File system problems

## Event System

Timeline operations emit events through the EventManager:

- `TIMELINE_CREATED`: New timeline created
- `TIMELINE_DELETED`: Timeline removed
- `CHECKPOINT_CREATED`: New checkpoint created
- `CHECKPOINT_RESTORED`: Checkpoint restored
- `BRANCH_CREATED`: New branch created
- `BRANCH_SWITCHED`: Branch switched

## Testing

Comprehensive test suite covers:

- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **Mock Testing**: External dependency isolation
- **Error Handling Tests**: Exception scenarios

Run tests with:
```bash
python run_tests.py
# or
python -m pytest tests/
```

## Configuration

Timeline settings are managed through the existing YACL configuration system:

- Repository paths configurable via paths service
- Git author information from user settings
- Timeline behavior preferences

## Performance Considerations

- **Lazy Loading**: Timelines loaded on-demand
- **Caching**: Repository objects cached for reuse
- **Efficient Git Operations**: Minimal file copying using worktrees
- **Background Operations**: Long-running Git operations handled asynchronously

## Security

- **Input Validation**: All user inputs validated before Git operations
- **Path Sanitization**: File paths checked for security issues
- **Git Safety**: Only safe Git operations allowed
- **Error Isolation**: Git errors don't crash the application

## Future Enhancements

Potential improvements for future versions:

1. **Remote Repositories**: Sync timelines across devices
2. **Timeline Sharing**: Export/import timeline data
3. **Advanced Branching**: Merge operations and conflict resolution
4. **Performance Optimization**: Incremental backups and compression
5. **Visual Timeline**: Graphical timeline representation
6. **Automated Checkpoints**: Periodic automatic checkpoint creation

## Troubleshooting

### Common Issues

1. **Repository Corruption**: Delete `.yacl_timelines` directory and recreate
2. **Permission Errors**: Check file system permissions
3. **Git Errors**: Ensure dulwich is properly installed
4. **Missing Save Games**: Verify save game directory structure

### Debug Information

Enable debug logging to troubleshoot issues:
```python
import logging
logging.getLogger('yacl.models.timeline_manager').setLevel(logging.DEBUG)
```

### Recovery Procedures

If timeline data becomes corrupted:

1. Backup current save games
2. Delete corrupted timeline directory
3. Recreate timeline from current save state
4. Manually restore checkpoints if needed

## API Reference

### TimelineManager Methods

- `initialize()`: Initialize timeline system
- `create_timeline(save_game)`: Create new timeline
- `create_checkpoint(save_game, message)`: Create checkpoint
- `restore_checkpoint(save_game, commit_hash)`: Restore checkpoint
- `create_branch(save_game, branch_name)`: Create branch
- `switch_branch(save_game, branch_name)`: Switch branch
- `get_timeline(save_game)`: Get timeline for save game

### Timeline Properties

- `name`: Timeline name
- `game_type`: Associated game type
- `save_path`: Original save directory
- `worktree_path`: Active worktree directory
- `repository_path`: Git repository directory
- `branches`: Dictionary of timeline branches
- `current_branch`: Currently active branch
- `current_checkpoint`: Current checkpoint
- `status`: Timeline status

## Integration Points

The timeline system integrates with:

- **Installation Manager**: Game type detection
- **Paths Service**: Directory management
- **Event Manager**: System-wide event communication
- **Main Application**: Lifecycle management
- **UI Framework**: Tab and dialog integration

## Dependencies

The timeline system requires:

- **dulwich**: Pure Python Git implementation (version 0.24+)
- **pathlib**: Path manipulation (Python standard library)
- **datetime**: Timestamp handling (Python standard library)
- **logging**: Debug and error logging (Python standard library)
- **tkinter**: UI components (Python standard library)

Install dependencies:
```bash
pip install dulwich>=0.24
```
