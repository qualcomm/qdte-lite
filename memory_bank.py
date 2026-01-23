# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
"""
@file memory_bank.py
This file implements a workspace memory system for the QDTE application.

The MemoryBank class provides functionality to save and restore project states,
including open files, tree view states, highlights, and other workspace information.

Copyright (c) 2024 Qualcomm Technologies, Inc.
All Rights Reserved.
Confidential and Proprietary - Qualcomm Technologies, Inc.
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import dtlogger
from flags import global_info as gl_info


class WorkspaceState:
    """Represents a single workspace state snapshot"""
    
    def __init__(self, name: str = None):
        self.name = name or f"workspace_{int(time.time())}"
        self.timestamp = datetime.now().isoformat()
        self.current_file = None
        self.tree_expansion_state = {}
        self.highlights = []
        self.recent_files = []
        self.window_geometry = None
        self.hex_view_visible = False
        self.view_style_hex = True
        self.find_options = None
        self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workspace state to dictionary for JSON serialization"""
        return {
            'name': self.name,
            'timestamp': self.timestamp,
            'current_file': self.current_file,
            'tree_expansion_state': self.tree_expansion_state,
            'highlights': self.highlights,
            'recent_files': self.recent_files,
            'window_geometry': self.window_geometry,
            'hex_view_visible': self.hex_view_visible,
            'view_style_hex': self.view_style_hex,
            'find_options': self.find_options,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkspaceState':
        """Create workspace state from dictionary"""
        state = cls(data.get('name'))
        state.timestamp = data.get('timestamp', datetime.now().isoformat())
        state.current_file = data.get('current_file')
        state.tree_expansion_state = data.get('tree_expansion_state', {})
        state.highlights = data.get('highlights', [])
        state.recent_files = data.get('recent_files', [])
        state.window_geometry = data.get('window_geometry')
        state.hex_view_visible = data.get('hex_view_visible', False)
        state.view_style_hex = data.get('view_style_hex', True)
        state.find_options = data.get('find_options')
        state.metadata = data.get('metadata', {})
        return state


class MemoryBank:
    """
    Memory Bank system for managing workspace states in QDTE.
    
    This class provides functionality to:
    - Save current workspace state
    - Restore previous workspace states
    - Manage multiple named workspaces
    - Maintain workspace history
    - Auto-save functionality
    """
    
    def __init__(self, storage_path: str = None):
        """
        Initialize the Memory Bank
        
        :param storage_path: Path to store workspace data. Defaults to QDTE config directory.
        """
        if storage_path is None:
            # Use the QDTE config directory
            config_dir = os.path.dirname(gl_info.get("user_cfg", ""))
            if not config_dir:
                config_dir = os.path.join(os.path.expanduser("~"), ".qdte")
            storage_path = os.path.join(config_dir, "workspaces.json")
        
        self.storage_path = storage_path
        self.workspaces: Dict[str, WorkspaceState] = {}
        self.current_workspace_name: Optional[str] = None
        self.max_recent_files = 10
        self.max_workspaces = 50
        self.auto_save_enabled = True
        
        # Ensure storage directory exists
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        
        # Load existing workspaces
        self.load_from_disk()
        
        dtlogger.info(f"Memory Bank initialized at: {self.storage_path}")
    
    def create_workspace(self, name: str = None) -> WorkspaceState:
        """
        Create a new workspace
        
        :param name: Name for the workspace. Auto-generated if not provided.
        :return: The created WorkspaceState object
        """
        workspace = WorkspaceState(name)
        self.workspaces[workspace.name] = workspace
        self.current_workspace_name = workspace.name
        
        dtlogger.info(f"Created new workspace: {workspace.name}")
        return workspace
    
    def save_workspace(self, name: str = None, state_data: Dict[str, Any] = None) -> bool:
        """
        Save current workspace state
        
        :param name: Name for the workspace. Uses current workspace if not provided.
        :param state_data: Dictionary containing state data to save
        :return: True if successful, False otherwise
        """
        try:
            if name is None:
                name = self.current_workspace_name
            
            if name is None:
                # Create a new workspace if none exists
                workspace = self.create_workspace()
                name = workspace.name
            elif name not in self.workspaces:
                # Create new workspace with given name
                workspace = self.create_workspace(name)
            else:
                workspace = self.workspaces[name]
            
            # Update workspace with provided state data
            if state_data:
                if 'current_file' in state_data:
                    workspace.current_file = state_data['current_file']
                if 'tree_expansion_state' in state_data:
                    workspace.tree_expansion_state = state_data['tree_expansion_state']
                if 'highlights' in state_data:
                    workspace.highlights = state_data['highlights']
                if 'window_geometry' in state_data:
                    workspace.window_geometry = state_data['window_geometry']
                if 'hex_view_visible' in state_data:
                    workspace.hex_view_visible = state_data['hex_view_visible']
                if 'view_style_hex' in state_data:
                    workspace.view_style_hex = state_data['view_style_hex']
                if 'find_options' in state_data:
                    workspace.find_options = state_data['find_options']
                if 'metadata' in state_data:
                    workspace.metadata.update(state_data['metadata'])
                
                # Update recent files
                if workspace.current_file and workspace.current_file not in workspace.recent_files:
                    workspace.recent_files.insert(0, workspace.current_file)
                    workspace.recent_files = workspace.recent_files[:self.max_recent_files]
            
            # Update timestamp
            workspace.timestamp = datetime.now().isoformat()
            
            # Persist to disk if auto-save is enabled
            if self.auto_save_enabled:
                self.save_to_disk()
            
            dtlogger.info(f"Saved workspace: {name}")
            return True
            
        except Exception as e:
            dtlogger.error(f"Failed to save workspace {name}: {e}")
            return False
    
    def load_workspace(self, name: str) -> Optional[WorkspaceState]:
        """
        Load a workspace by name
        
        :param name: Name of the workspace to load
        :return: WorkspaceState object if found, None otherwise
        """
        if name in self.workspaces:
            self.current_workspace_name = name
            dtlogger.info(f"Loaded workspace: {name}")
            return self.workspaces[name]
        else:
            dtlogger.warning(f"Workspace not found: {name}")
            return None
    
    def delete_workspace(self, name: str) -> bool:
        """
        Delete a workspace
        
        :param name: Name of the workspace to delete
        :return: True if successful, False otherwise
        """
        if name in self.workspaces:
            del self.workspaces[name]
            if self.current_workspace_name == name:
                self.current_workspace_name = None
            
            if self.auto_save_enabled:
                self.save_to_disk()
            
            dtlogger.info(f"Deleted workspace: {name}")
            return True
        return False
    
    def list_workspaces(self) -> List[Dict[str, Any]]:
        """
        Get list of all workspaces with metadata
        
        :return: List of workspace information dictionaries
        """
        workspace_list = []
        for name, workspace in self.workspaces.items():
            workspace_list.append({
                'name': name,
                'timestamp': workspace.timestamp,
                'current_file': workspace.current_file,
                'is_current': name == self.current_workspace_name
            })
        
        # Sort by timestamp (most recent first)
        workspace_list.sort(key=lambda x: x['timestamp'], reverse=True)
        return workspace_list
    
    def get_current_workspace(self) -> Optional[WorkspaceState]:
        """
        Get the current active workspace
        
        :return: Current WorkspaceState or None
        """
        if self.current_workspace_name and self.current_workspace_name in self.workspaces:
            return self.workspaces[self.current_workspace_name]
        return None
    
    def save_to_disk(self) -> bool:
        """
        Persist all workspaces to disk
        
        :return: True if successful, False otherwise
        """
        try:
            # Limit number of workspaces
            if len(self.workspaces) > self.max_workspaces:
                # Keep only the most recent workspaces
                sorted_workspaces = sorted(
                    self.workspaces.items(),
                    key=lambda x: x[1].timestamp,
                    reverse=True
                )
                self.workspaces = dict(sorted_workspaces[:self.max_workspaces])
            
            data = {
                'version': '1.0',
                'current_workspace': self.current_workspace_name,
                'workspaces': {
                    name: workspace.to_dict()
                    for name, workspace in self.workspaces.items()
                }
            }
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, separators=(',', ': '))
            
            dtlogger.debug(f"Saved {len(self.workspaces)} workspaces to disk")
            return True
            
        except Exception as e:
            dtlogger.error(f"Failed to save workspaces to disk: {e}")
            return False
    
    def load_from_disk(self) -> bool:
        """
        Load workspaces from disk
        
        :return: True if successful, False otherwise
        """
        try:
            if not os.path.exists(self.storage_path):
                dtlogger.info("No existing workspace file found, starting fresh")
                return True
            
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.current_workspace_name = data.get('current_workspace')
            
            workspaces_data = data.get('workspaces', {})
            self.workspaces = {
                name: WorkspaceState.from_dict(ws_data)
                for name, ws_data in workspaces_data.items()
            }
            
            dtlogger.info(f"Loaded {len(self.workspaces)} workspaces from disk")
            return True
            
        except Exception as e:
            dtlogger.error(f"Failed to load workspaces from disk: {e}")
            return False
    
    def add_recent_file(self, filepath: str) -> None:
        """
        Add a file to recent files list
        
        :param filepath: Path to the file
        """
        workspace = self.get_current_workspace()
        if workspace is None:
            workspace = self.create_workspace()
        
        if filepath not in workspace.recent_files:
            workspace.recent_files.insert(0, filepath)
            workspace.recent_files = workspace.recent_files[:self.max_recent_files]
            
            if self.auto_save_enabled:
                self.save_to_disk()
    
    def get_recent_files(self) -> List[str]:
        """
        Get list of recent files
        
        :return: List of recent file paths
        """
        workspace = self.get_current_workspace()
        if workspace:
            return workspace.recent_files
        return []
    
    def clear_recent_files(self) -> None:
        """Clear recent files list"""
        workspace = self.get_current_workspace()
        if workspace:
            workspace.recent_files = []
            if self.auto_save_enabled:
                self.save_to_disk()
    
    def export_workspace(self, name: str, export_path: str) -> bool:
        """
        Export a workspace to a separate file
        
        :param name: Name of workspace to export
        :param export_path: Path to export to
        :return: True if successful, False otherwise
        """
        try:
            if name not in self.workspaces:
                dtlogger.error(f"Workspace not found: {name}")
                return False
            
            workspace = self.workspaces[name]
            data = {
                'version': '1.0',
                'workspace': workspace.to_dict()
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, separators=(',', ': '))
            
            dtlogger.info(f"Exported workspace {name} to {export_path}")
            return True
            
        except Exception as e:
            dtlogger.error(f"Failed to export workspace: {e}")
            return False
    
    def import_workspace(self, import_path: str, name: str = None) -> bool:
        """
        Import a workspace from a file
        
        :param import_path: Path to import from
        :param name: Optional new name for the workspace
        :return: True if successful, False otherwise
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            workspace_data = data.get('workspace')
            if not workspace_data:
                dtlogger.error("Invalid workspace file format")
                return False
            
            workspace = WorkspaceState.from_dict(workspace_data)
            
            if name:
                workspace.name = name
            
            # Ensure unique name
            original_name = workspace.name
            counter = 1
            while workspace.name in self.workspaces:
                workspace.name = f"{original_name}_{counter}"
                counter += 1
            
            self.workspaces[workspace.name] = workspace
            
            if self.auto_save_enabled:
                self.save_to_disk()
            
            dtlogger.info(f"Imported workspace as {workspace.name}")
            return True
            
        except Exception as e:
            dtlogger.error(f"Failed to import workspace: {e}")
            return False


# Global memory bank instance
_memory_bank_instance: Optional[MemoryBank] = None


def get_memory_bank() -> MemoryBank:
    """
    Get the global memory bank instance (singleton pattern)
    
    :return: MemoryBank instance
    """
    global _memory_bank_instance
    if _memory_bank_instance is None:
        _memory_bank_instance = MemoryBank()
    return _memory_bank_instance


def init_memory_bank(storage_path: str = None) -> MemoryBank:
    """
    Initialize the memory bank system
    
    :param storage_path: Optional custom storage path
    :return: MemoryBank instance
    """
    global _memory_bank_instance
    _memory_bank_instance = MemoryBank(storage_path)
    dtlogger.info("Memory Bank system initialized")
    return _memory_bank_instance
