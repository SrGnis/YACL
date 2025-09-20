# YACL Timeline Feature

## Quick Start

The Timeline feature provides Git-based version control for your Cataclysm: Dark Days Ahead save games.

### What it does:
- ✅ Create save points (checkpoints) at any time
- ✅ Restore to any previous checkpoint
- ✅ Create branches to explore different paths
- ✅ Switch between branches instantly
- ✅ Keep complete history of your game progress

### Requirements:
- YACL installed and configured
- Python 3.8+ with dulwich library
- Existing Cataclysm save games

## Installation

```bash
# Install required dependency
pip install dulwich>=0.24

# Timeline feature is included with YACL
# No additional installation needed
```

## Basic Usage

1. **Open YACL** and go to the Timeline tab
2. **Select a save game** from the list
3. **Create timeline** if it doesn't exist
4. **Create checkpoints** before important decisions
5. **Restore checkpoints** if things go wrong
6. **Create branches** to try different approaches

## Key Features

### 🎯 Checkpoints
Create save points with custom messages:
```
"Before entering the lab"
"Day 30: Found working vehicle"
"Pre-mutation threshold"
```

### 🌿 Branches
Explore different paths:
```
main → combat-focused
    → stealth-build
    → crafter-specialist
```

### 🔄 Instant Restoration
Restore any checkpoint in seconds, not minutes.

### 📊 Visual Timeline
See your complete game history at a glance.

## Documentation

- **[User Guide](TIMELINE_USER_GUIDE.md)**: Complete usage instructions
- **[Implementation](TIMELINE_IMPLEMENTATION.md)**: Technical documentation
- **[Tests](../tests/)**: Comprehensive test suite

## Quick Commands

| Action | Steps |
|--------|-------|
| Create Timeline | Select save → "Create Timeline" |
| Make Checkpoint | Enter message → "Create Checkpoint" |
| Restore State | Select checkpoint → "Restore Checkpoint" |
| Create Branch | Select checkpoint → "Create Branch" |
| Switch Branch | Select branch → "Switch Branch" |

## File Structure

```
saves/
├── YourSave/              # Original save
└── .yacl_timelines/
    └── repositories/      # Git data
    └── worktrees/        # Active states
```

## Safety Features

- ⚠️ Confirmation dialogs for destructive operations
- 🔒 Input validation and error handling
- 📝 Comprehensive logging
- 🛡️ Automatic backup of timeline data
- 🔄 Recovery procedures for corrupted data

## Performance

- **Fast**: Checkpoint creation in seconds
- **Efficient**: Uses Git worktrees for minimal disk usage
- **Scalable**: Handles large save games efficiently
- **Reliable**: Built on proven Git technology

## Troubleshooting

### Common Issues:
- **"No timeline found"** → Create timeline first
- **"Repository error"** → Check file permissions
- **Checkpoint fails** → Verify save game integrity

### Recovery:
```bash
# If timeline corrupts, delete and recreate:
rm -rf saves/.yacl_timelines/YourGame/YourSave/
# Then create new timeline in YACL
```

## Contributing

Timeline feature follows YACL's development guidelines:

- **MVC Architecture**: Models, Views, Controllers
- **Event-Driven**: Uses EventManager for communication
- **KISS Principle**: Simple, maintainable code
- **Comprehensive Tests**: Full test coverage

### Running Tests:
```bash
python run_tests.py
# or
python -m pytest tests/models/test_timeline*.py -v
```

## Roadmap

Future enhancements planned:
- 🌐 Remote timeline sync
- 📤 Timeline export/import
- 🔀 Advanced merge operations
- 📈 Timeline analytics
- 🤖 Automated checkpoints

## Support

- 📖 Read the [User Guide](TIMELINE_USER_GUIDE.md)
- 🐛 Report bugs via YACL issue tracker
- 💬 Get help in YACL community forums
- 📧 Contact maintainers for technical issues

## License

Timeline feature is part of YACL and follows the same license terms.

---

**Happy time traveling in the Cataclysm! 🕰️**
