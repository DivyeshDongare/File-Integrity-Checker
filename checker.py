"""
File integrity checker module for comparing and verifying file hashes.
Detects modified, added, and deleted files by comparing against a baseline.
"""

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# Import project modules
from hasher import FileHasher
from database import HashDatabase
from scanner import FileInfo


@dataclass
class IntegrityResult:
    """Data class to store integrity check results."""
    modified: List[str] = field(default_factory=list)
    added: List[str] = field(default_factory=list)
    deleted: List[str] = field(default_factory=list)
    unchanged: List[str] = field(default_factory=list)
    errors: Dict[str, str] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        """Convert result to dictionary."""
        return {
            'modified': self.modified,
            'added': self.added,
            'deleted': self.deleted,
            'unchanged': self.unchanged,
            'errors': self.errors,
            'timestamp': self.timestamp,
            'total_checked': self.get_total_files(),
            'has_changes': self.has_changes()
        }
    
    def get_total_files(self) -> int:
        """Get total number of files checked."""
        return len(self.modified) + len(self.added) + len(self.deleted) + len(self.unchanged)
    
    def has_changes(self) -> bool:
        """Check if any changes were detected."""
        return bool(self.modified or self.added or self.deleted)
    
    def get_summary(self) -> str:
        """Get human-readable summary of results."""
        if not self.has_changes():
            return f"✓ No changes detected ({len(self.unchanged)} files intact)"
        
        summary_parts = []
        if self.modified:
            summary_parts.append(f"{len(self.modified)} modified")
        if self.added:
            summary_parts.append(f"{len(self.added)} added")
        if self.deleted:
            summary_parts.append(f"{len(self.deleted)} deleted")
        
        return f"⚠ Changes detected: {', '.join(summary_parts)}"


@dataclass
class FileChange:
    """Data class to store detailed file change information."""
    file_path: str
    change_type: str  # 'modified', 'added', 'deleted'
    old_hash: Optional[str] = None
    new_hash: Optional[str] = None
    old_size: Optional[int] = None
    new_size: Optional[int] = None
    old_modified_time: Optional[float] = None
    new_modified_time: Optional[float] = None
    
    def get_change_description(self) -> str:
        """Get description of the change."""
        if self.change_type == 'modified':
            details = []
            if self.old_hash != self.new_hash:
                details.append("content changed")
            if self.old_size != self.new_size:
                details.append(f"size: {self.old_size} → {self.new_size}")
            return f"Modified: {', '.join(details)}"
        elif self.change_type == 'added':
            return f"Added: {self.new_size} bytes"
        elif self.change_type == 'deleted':
            return f"Deleted: was {self.old_size} bytes"
        return "Unknown change"


class IntegrityChecker:
    """Main class for checking file integrity against a baseline."""
    
    def __init__(self, database: HashDatabase, hasher: FileHasher):
        """
        Initialize IntegrityChecker.
        
        Args:
            database: HashDatabase instance for storing/retrieving hashes
            hasher: FileHasher instance for calculating hashes
        """
        self.database = database
        self.hasher = hasher
        self.detailed_changes: List[FileChange] = []
    
    def verify_files(self, current_files: List[FileInfo]) -> Dict:
        """
        Verify files against baseline and detect changes.
        
        Args:
            current_files: List of FileInfo objects for current file state
            
        Returns:
            Dictionary with modified, added, deleted, and unchanged files
        """
        result = IntegrityResult()
        
        # Get baseline from database
        baseline = self.database.get_all_hashes()
        baseline_paths = {entry['file_path'] for entry in baseline}
        
        # Create lookup dictionary for baseline
        baseline_dict = {entry['file_path']: entry for entry in baseline}
        
        # Track current file paths
        current_paths = set()
        
        # Check each current file
        for file_info in current_files:
            current_paths.add(file_info.relative_path)
            
            try:
                # Calculate current hash
                current_hash = self.hasher.hash_file(file_info.path)
                
                if file_info.relative_path in baseline_dict:
                    # File exists in baseline - check if modified
                    baseline_entry = baseline_dict[file_info.relative_path]
                    
                    if self._is_file_modified(baseline_entry, file_info, current_hash):
                        result.modified.append(file_info.relative_path)
                        
                        # Store detailed change information
                        change = FileChange(
                            file_path=file_info.relative_path,
                            change_type='modified',
                            old_hash=baseline_entry['hash'],
                            new_hash=current_hash,
                            old_size=baseline_entry['size'],
                            new_size=file_info.size,
                            old_modified_time=baseline_entry.get('modified_time'),
                            new_modified_time=file_info.modified_time
                        )
                        self.detailed_changes.append(change)
                    else:
                        result.unchanged.append(file_info.relative_path)
                else:
                    # File not in baseline - it's new
                    result.added.append(file_info.relative_path)
                    
                    change = FileChange(
                        file_path=file_info.relative_path,
                        change_type='added',
                        new_hash=current_hash,
                        new_size=file_info.size,
                        new_modified_time=file_info.modified_time
                    )
                    self.detailed_changes.append(change)
            
            except Exception as e:
                result.errors[file_info.relative_path] = str(e)
        
        # Find deleted files (in baseline but not in current)
        deleted_paths = baseline_paths - current_paths
        result.deleted = list(deleted_paths)
        
        for deleted_path in deleted_paths:
            baseline_entry = baseline_dict[deleted_path]
            change = FileChange(
                file_path=deleted_path,
                change_type='deleted',
                old_hash=baseline_entry['hash'],
                old_size=baseline_entry['size'],
                old_modified_time=baseline_entry.get('modified_time')
            )
            self.detailed_changes.append(change)
        
        return result.to_dict()
    
    def _is_file_modified(self, baseline_entry: Dict, 
                         file_info: FileInfo, current_hash: str) -> bool:
        """
        Determine if a file has been modified.
        
        Args:
            baseline_entry: Baseline database entry
            file_info: Current file information
            current_hash: Current file hash
            
        Returns:
            True if file is modified, False otherwise
        """
        # Primary check: hash comparison
        if baseline_entry['hash'] != current_hash:
            return True
        
        # Secondary checks: size or modification time
        if baseline_entry['size'] != file_info.size:
            return True
        
        # Note: Modification time alone is not conclusive
        # but combined with other factors can indicate changes
        return False
    
    def verify_single_file(self, file_path: str, 
                          relative_path: Optional[str] = None) -> Tuple[bool, str]:
        """
        Verify integrity of a single file.
        
        Args:
            file_path: Absolute path to the file
            relative_path: Relative path for database lookup (optional)
            
        Returns:
            Tuple of (is_valid, message)
        """
        if relative_path is None:
            relative_path = file_path
        
        try:
            # Get baseline hash from database
            baseline = self.database.get_hash(relative_path)
            
            if baseline is None:
                return False, f"File not in baseline: {relative_path}"
            
            # Calculate current hash
            current_hash = self.hasher.hash_file(file_path)
            
            # Compare hashes
            if baseline['hash'] == current_hash:
                return True, f"File intact: {relative_path}"
            else:
                return False, f"File modified: {relative_path}"
        
        except FileNotFoundError:
            return False, f"File not found: {file_path}"
        except Exception as e:
            return False, f"Error verifying file: {e}"
    
    def get_detailed_changes(self) -> List[FileChange]:
        """
        Get detailed information about detected changes.
        
        Returns:
            List of FileChange objects
        """
        return self.detailed_changes
    
    def get_changes_by_type(self, change_type: str) -> List[FileChange]:
        """
        Get changes filtered by type.
        
        Args:
            change_type: Type of change ('modified', 'added', 'deleted')
            
        Returns:
            List of FileChange objects matching the type
        """
        return [change for change in self.detailed_changes 
                if change.change_type == change_type]
    
    def generate_report(self, result: Dict, verbose: bool = False) -> str:
        """
        Generate a formatted integrity check report.
        
        Args:
            result: Result dictionary from verify_files
            verbose: Include detailed file listings
            
        Returns:
            Formatted report string
        """
        lines = []
        lines.append("=" * 60)
        lines.append("FILE INTEGRITY CHECK REPORT")
        lines.append("=" * 60)
        lines.append(f"Timestamp: {result['timestamp']}")
        lines.append(f"Total Files Checked: {result['total_checked']}")
        lines.append("")
        
        if not result['has_changes']:
            lines.append("✓ STATUS: All files match baseline (No changes detected)")
        else:
            lines.append("⚠ STATUS: Changes detected")
        
        lines.append("")
        lines.append(f"Modified Files: {len(result['modified'])}")
        lines.append(f"Added Files: {len(result['added'])}")
        lines.append(f"Deleted Files: {len(result['deleted'])}")
        lines.append(f"Unchanged Files: {len(result['unchanged'])}")
        
        if result['errors']:
            lines.append(f"Errors: {len(result['errors'])}")
        
        if verbose:
            if result['modified']:
                lines.append("\n--- MODIFIED FILES ---")
                for change in self.get_changes_by_type('modified'):
                    lines.append(f"  • {change.file_path}")
                    lines.append(f"    {change.get_change_description()}")
            
            if result['added']:
                lines.append("\n--- ADDED FILES ---")
                for change in self.get_changes_by_type('added'):
                    lines.append(f"  + {change.file_path}")
                    lines.append(f"    {change.get_change_description()}")
            
            if result['deleted']:
                lines.append("\n--- DELETED FILES ---")
                for change in self.get_changes_by_type('deleted'):
                    lines.append(f"  - {change.file_path}")
                    lines.append(f"    {change.get_change_description()}")
            
            if result['errors']:
                lines.append("\n--- ERRORS ---")
                for file_path, error in result['errors'].items():
                    lines.append(f"  ✗ {file_path}: {error}")
        
        lines.append("\n" + "=" * 60)
        
        return "\n".join(lines)
    
    def clear_changes(self) -> None:
        """Clear stored detailed changes."""
        self.detailed_changes.clear()


# Convenience functions
def quick_verify(file_path: str, expected_hash: str, 
                algorithm: str = 'sha256') -> bool:
    """
    Quick verification of a single file.
    
    Args:
        file_path: Path to file
        expected_hash: Expected hash value
        algorithm: Hash algorithm to use
        
    Returns:
        True if file matches expected hash
    """
    hasher = FileHasher(algorithm)
    return hasher.verify_hash(file_path, expected_hash)


def compare_files(file1: str, file2: str, 
                 algorithm: str = 'sha256') -> bool:
    """
    Compare two files by hash.
    
    Args:
        file1: Path to first file
        file2: Path to second file
        algorithm: Hash algorithm to use
        
    Returns:
        True if files are identical
    """
    hasher = FileHasher(algorithm)
    
    try:
        hash1 = hasher.hash_file(file1)
        hash2 = hasher.hash_file(file2)
        return hash1 == hash2
    except Exception:
        return False
