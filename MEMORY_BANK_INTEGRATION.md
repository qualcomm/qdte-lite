# Memory Bank System Documentation

## Overview
The Memory Bank system (memory_bank.py) provides workspace state management for QDTE.

## Integration with QDTE
- Stores workspace states in ~/.qdte/workspaces.json
- Manages multiple named workspaces
- Auto-saves workspace changes
- Tracks recent files (up to 10 per workspace)

## Key Classes
- WorkspaceState: Represents a workspace snapshot
- MemoryBank: Main workspace management system

## Usage in Controller
To integrate with controller.py:
1. Import: from memory_bank import init_memory_bank, get_memory_bank
2. Initialize in __init__: self.memory_bank = init_memory_bank()
3. Save on file open: memory_bank.add_recent_file(filepath)
4. Save workspace state on changes

## Testing
Run: python test_memory_bank.py

## Maintainer Notes
- Follows QDTE coding standards
- Uses qdtelogger for logging
- JSON-based persistence
- Singleton pattern for global access
