"""
File scanner module for recursively scanning directories and collecting file metadata.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional, Generator
from dataclasses import dataclass
from datetime import datetime


@dataclass
class FileInfo:
    """Data class to store file information."""
    path: str
    relative_path: str
    size: int
    modified_time: float
    is_file: bool
    permissions: str
    
    def to_dict(self) -> Dict:
        """Convert FileInfo to dictionary."""
        return {
            'path': self.path,
            'relative_path': self.relative_path,
            'size': self.size,
            'modified_time': self.modified_time,
            'is_file': self.is_file,
            'permissions': self.permissions
        }


class DirectoryScanner:
    """Scanner class for recursively scanning directories."""
    
    def __init__(self, root_path: str, exclude_patterns: Optional[List[str]] = None):
        """
        Initialize the directory scanner.
        
        Args:
            root_path: Root directory to scan
            exclude_patterns: List of patterns to exclude (e.g., ['*.log', '__pycache__'])
        """
        self.root_path = Path(root_path).resolve()
        self.exclude_patterns = exclude_patterns or []
        
        if not self.root_path.exists():
            raise ValueError(f"Path does not exist: {self.root_path}")
        if not self.root_path.is_dir():
            raise ValueError(f"Path is not a directory: {self.root_path}")
    
    def should_exclude(self, path: Path) -> bool:
        """
        Check if a path should be excluded based on exclude patterns.
        
        Args:
            path: Path to check
            
        Returns:
            True if path should be excluded, False otherwise
        """
        for pattern in self.exclude_patterns:
            if path.match(pattern):
                return True
        return False
    
    def scan_directory(self, recursive: bool = True) -> List[FileInfo]:
        """
        Scan directory and return list of file information.
        
        Args:
            recursive: Whether to scan subdirectories recursively
            
        Returns:
            List of FileInfo objects
        """
        files = []
        
        try:
            for file_info in self._scan_generator(recursive):
                files.append(file_info)
        except Exception as e:
            raise RuntimeError(f"Error during directory scan: {e}")
        
        return files
    
    def _scan_generator(self, recursive: bool = True) -> Generator[FileInfo, None, None]:
        """
        Generator that yields FileInfo objects during directory traversal.
        
        Args:
            recursive: Whether to scan subdirectories recursively
            
        Yields:
            FileInfo objects for each file found
        """
        if recursive:
            yield from self._recursive_scan(self.root_path)
        else:
            yield from self._single_level_scan(self.root_path)
    
    def _recursive_scan(self, directory: Path) -> Generator[FileInfo, None, None]:
        """
        Recursively scan directory using os.scandir for better performance.
        
        Args:
            directory: Directory to scan
            
        Yields:
            FileInfo objects for each file found
        """
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    entry_path = Path(entry.path)
                    
                    # Skip excluded patterns
                    if self.should_exclude(entry_path):
                        continue
                    
                    try:
                        if entry.is_symlink():
                            # Skip symbolic links to avoid infinite loops
                            continue
                        
                        if entry.is_dir(follow_symlinks=False):
                            # Recursively scan subdirectory
                            yield from self._recursive_scan(entry_path)
                        elif entry.is_file(follow_symlinks=False):
                            # Get file information
                            stat_info = entry.stat(follow_symlinks=False)
                            
                            file_info = FileInfo(
                                path=str(entry_path),
                                relative_path=str(entry_path.relative_to(self.root_path)),
                                size=stat_info.st_size,
                                modified_time=stat_info.st_mtime,
                                is_file=True,
                                permissions=oct(stat_info.st_mode)[-3:]
                            )
                            
                            yield file_info
                    
                    except PermissionError:
                        # Log permission errors but continue scanning
                        print(f"Permission denied: {entry_path}")
                        continue
                    except OSError as e:
                        print(f"OS error accessing {entry_path}: {e}")
                        continue
        
        except PermissionError:
            print(f"Permission denied accessing directory: {directory}")
        except OSError as e:
            print(f"OS error scanning directory {directory}: {e}")
    
    def _single_level_scan(self, directory: Path) -> Generator[FileInfo, None, None]:
        """
        Scan single directory level without recursion.
        
        Args:
            directory: Directory to scan
            
        Yields:
            FileInfo objects for each file found
        """
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    entry_path = Path(entry.path)
                    
                    # Skip excluded patterns
                    if self.should_exclude(entry_path):
                        continue
                    
                    try:
                        if entry.is_file(follow_symlinks=False) and not entry.is_symlink():
                            stat_info = entry.stat(follow_symlinks=False)
                            
                            file_info = FileInfo(
                                path=str(entry_path),
                                relative_path=str(entry_path.relative_to(self.root_path)),
                                size=stat_info.st_size,
                                modified_time=stat_info.st_mtime,
                                is_file=True,
                                permissions=oct(stat_info.st_mode)[-3:]
                            )
                            
                            yield file_info
                    
                    except (PermissionError, OSError) as e:
                        print(f"Error accessing {entry_path}: {e}")
                        continue
        
        except (PermissionError, OSError) as e:
            print(f"Error scanning directory {directory}: {e}")
    
    def get_file_count(self, recursive: bool = True) -> int:
        """
        Get count of files in directory.
        
        Args:
            recursive: Whether to count files recursively
            
        Returns:
            Number of files found
        """
        return len(self.scan_directory(recursive=recursive))
    
    def get_total_size(self, recursive: bool = True) -> int:
        """
        Calculate total size of all files in directory.
        
        Args:
            recursive: Whether to calculate size recursively
            
        Returns:
            Total size in bytes
        """
        total_size = 0
        for file_info in self.scan_directory(recursive=recursive):
            total_size += file_info.size
        return total_size


def scan_path(path: str, recursive: bool = True, exclude_patterns: Optional[List[str]] = None) -> List[FileInfo]:
    """
    Convenience function to scan a path and return file information.
    
    Args:
        path: Path to scan
        recursive: Whether to scan recursively
        exclude_patterns: Patterns to exclude from scan
        
    Returns:
        List of FileInfo objects
    """
    scanner = DirectoryScanner(path, exclude_patterns)
    return scanner.scan_directory(recursive=recursive)
