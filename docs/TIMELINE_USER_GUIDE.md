# Timeline User Guide

## Introduction

The Timeline feature in YACL allows you to create save points (checkpoints) for your Cataclysm: Dark Days Ahead games and restore to any previous state. Think of it as a sophisticated save/load system that keeps track of your entire game history.

## Getting Started

### Prerequisites

1. YACL must be installed and configured
2. At least one Cataclysm game installation
3. Existing save games to manage

### Accessing the Timeline Tab

1. Launch YACL
2. Select your game installation
3. Click on the "Timeline" tab

## Basic Concepts

### Timelines
A timeline is a version history for a specific save game. Each save game can have its own timeline with multiple checkpoints and branches.

### Checkpoints
Checkpoints are save points in your game. Each checkpoint captures the complete state of your save game at a specific moment.

### Branches
Branches allow you to explore different paths in your game. You can create a branch from any checkpoint and develop separate storylines.

## Creating Your First Timeline

### Step 1: Select a Save Game
1. In the Timeline tab, you'll see a list of your save games
2. Save games without timelines will be marked as "No Timeline"
3. Select a save game that doesn't have a timeline

### Step 2: Create Timeline
1. Click "Create Timeline" button
2. Confirm the timeline creation in the dialog
3. YACL will create a timeline and make an initial checkpoint

### Step 3: Verify Timeline Creation
- The save game should now show timeline information
- You'll see the initial checkpoint in the checkpoints list
- Timeline operations will become available

## Working with Checkpoints

### Creating Checkpoints

1. **Select your save game** from the list
2. **Enter a checkpoint message** in the text field (e.g., "Before entering the lab")
3. **Click "Create Checkpoint"**
4. The new checkpoint will appear in the checkpoints list

**Best Practices for Checkpoint Messages:**
- Be descriptive: "Before fighting the zombie hulk"
- Include location: "At the refugee center entrance"
- Note important decisions: "Before choosing mutation path"

### Viewing Checkpoint Details

1. Select a checkpoint from the list
2. View details in the right panel:
   - Commit hash (unique identifier)
   - Creation timestamp
   - Your custom message
   - Author information

### Restoring Checkpoints

⚠️ **Warning**: Restoring a checkpoint will overwrite your current save game state!

1. **Select the checkpoint** you want to restore to
2. **Click "Restore Checkpoint"**
3. **Confirm the restoration** in the warning dialog
4. Your save game will be restored to that exact state

## Working with Branches

### Why Use Branches?

Branches let you:
- Try different character builds
- Explore risky areas without losing progress
- Test different story choices
- Experiment with game mechanics

### Creating Branches

1. **Select a checkpoint** to branch from
2. **Click "Create Branch"**
3. **Enter a branch name** (e.g., "mutation-experiment", "lab-exploration")
4. **Confirm creation**

**Branch Naming Rules:**
- Use letters, numbers, hyphens, and underscores only
- No spaces or special characters
- Be descriptive but concise

### Switching Branches

1. **Select your save game**
2. **Choose a branch** from the branch dropdown
3. **Click "Switch Branch"**
4. Your save game will switch to that branch's current state

### Branch Strategy Examples

**Story Exploration:**
```
main branch: Safe, conservative choices
├── risky-choices: Aggressive, dangerous decisions
└── diplomatic: Peaceful, negotiation-focused
```

**Character Development:**
```
main branch: Balanced character
├── combat-focused: Pure fighter build
├── crafting-master: Crafting and building focus
└── survivor: Stealth and survival focus
```

## Timeline Interface Guide

### Left Panel: Save Games List
- Shows all save games for current game type
- Indicates which saves have timelines
- Click to select and view timeline

### Top Right: Timeline Information
- Current branch name
- Timeline status
- Branch selection dropdown
- Timeline operation buttons

### Bottom Right: Checkpoints
- **Left side**: List of checkpoints in current branch
- **Right side**: Details of selected checkpoint

### Action Buttons

- **Refresh**: Update the timeline display
- **Create Timeline**: Create timeline for selected save
- **Create Checkpoint**: Make new checkpoint with custom message
- **Restore Checkpoint**: Restore to selected checkpoint
- **Create Branch**: Create new branch from selected checkpoint
- **Switch Branch**: Change to selected branch

## Advanced Usage

### Timeline Workflow Example

1. **Start new character** → Create timeline
2. **Reach first town** → Create checkpoint "Reached Evac Shelter"
3. **Before dangerous area** → Create checkpoint "Before lab raid"
4. **Create branch** "lab-exploration" from "Before lab raid"
5. **Explore lab** → Create checkpoints as you progress
6. **If things go wrong** → Restore to earlier checkpoint
7. **Try different approach** → Switch to main branch, create new branch

### Managing Multiple Characters

Each save game has its own independent timeline:
- Character A: Timeline with exploration focus
- Character B: Timeline with base-building focus
- Character C: Timeline with combat testing

### Checkpoint Strategy

**Frequent Checkpoints:**
- Before entering new areas
- After major discoveries
- Before important decisions
- After significant progress

**Descriptive Messages:**
- "Day 15: Found working vehicle"
- "Before choosing CBM installation"
- "Safe base established at farm"
- "Pre-mutation threshold"

## Troubleshooting

### Common Issues

**"No timeline found" error:**
- Create a timeline for the save game first
- Ensure the save game directory exists

**"Repository error" messages:**
- Check file permissions
- Restart YACL
- If persistent, delete timeline and recreate

**Checkpoint creation fails:**
- Ensure checkpoint message is not empty
- Check available disk space
- Verify save game is not corrupted

**Branch operations fail:**
- Use valid branch names (no special characters)
- Ensure branch doesn't already exist
- Check that timeline is properly initialized

### Recovery

**If timeline becomes corrupted:**
1. Note your current save game state
2. Create manual backup of save directory
3. Delete the timeline (this removes all checkpoints!)
4. Create new timeline
5. Continue from current state

**If save game becomes corrupted:**
1. Use "Restore Checkpoint" to go back to working state
2. If no working checkpoints, restore from manual backup
3. Create new timeline from restored state

## Tips and Best Practices

### Checkpoint Management
- Create checkpoints before risky actions
- Use clear, descriptive messages
- Don't create too many checkpoints (they use disk space)
- Clean up old checkpoints periodically

### Branch Organization
- Use consistent naming conventions
- Document branch purposes
- Merge successful experiments back to main
- Delete unused branches

### Performance
- Timelines use disk space proportional to save game size
- Large save games = larger timeline storage
- Monitor available disk space
- Consider external storage for large timelines

### Safety
- Always create checkpoint before major changes
- Test timeline restoration with non-critical saves first
- Keep manual backups of important saves
- Don't rely solely on timelines for backup

## Keyboard Shortcuts

When Timeline tab is active:
- **F5**: Refresh timeline display
- **Ctrl+N**: Create new checkpoint (if message entered)
- **Ctrl+R**: Restore selected checkpoint (with confirmation)
- **Ctrl+B**: Create branch from selected checkpoint

## Integration with Other YACL Features

### Game Management
- Timelines work with all supported Cataclysm versions
- Switch between game installations normally
- Timelines are per-installation and per-save

### Backup System
- Timelines complement but don't replace regular backups
- Use both for maximum save game protection
- Timeline checkpoints are more granular than backups

### Settings
- Timeline behavior respects YACL settings
- File paths configured through YACL preferences
- Git author information from user settings

## Frequently Asked Questions

**Q: Do timelines affect game performance?**
A: No, timelines don't affect game performance. They only manage save files when you create/restore checkpoints.

**Q: Can I share timelines with other players?**
A: Currently, timelines are local only. Sharing features may be added in future versions.

**Q: How much disk space do timelines use?**
A: Each checkpoint stores a complete copy of your save game. A 10MB save with 20 checkpoints uses approximately 200MB.

**Q: Can I use timelines with modded games?**
A: Yes, timelines work with any Cataclysm installation, including heavily modded versions.

**Q: What happens if I manually edit save files?**
A: Manual edits won't be tracked by timelines. Create a new checkpoint after manual changes to include them in the timeline.

**Q: Can I recover deleted checkpoints?**
A: No, deleted checkpoints cannot be recovered. Be careful when managing timeline data.

## Getting Help

If you encounter issues with the Timeline feature:

1. Check this user guide for solutions
2. Review the troubleshooting section
3. Check YACL logs for error messages
4. Report bugs through YACL's issue tracker
5. Ask for help in YACL community forums

Remember: Timelines are a powerful tool for managing your Cataclysm experience. Start with simple checkpoint creation and gradually explore advanced features like branching as you become comfortable with the system.
