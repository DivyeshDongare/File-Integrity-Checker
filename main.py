# # # # Driver function
# # # import os
# # # if __name__ == &quot;__main__&quot; :
# # #     for (root,dirs,files) in os.walk('.', topdown=True):
# # #         print (root)
# # #         print (dirs)
# # #         print (files)
# # #         print ('--------------------------------')
# # # import os

# # # def list_directory_contents(start_path='.'):
# # #     for root, dirs, files in os.walk(start_path, topdown=True):
# # #         print(f"📁 Root: {root}")
# # #         print(f"📂 Directories: {dirs}")
# # #         print(f"📄 Files: {files}")
# # #         print('--------------------------------')

# # # if __name__ == "__main__":
# # #     path_to_scan = '.'  # You can change this to any directory path, e.g., '/home/user/documents'
# # #     list_directory_contents(path_to_scan)

# # from pathlib import Path
# # from typing import List,Optional

# # def collect_file_paths(
# #         directory: str,
# #         include_extensions: Optional[List[str]] = None,
# #         exclude_hidden: int = True,
# #         max_depth: Optional[int] = None,
# # ) -> List[str]:
# #     start_path = Path(directory).resolve()
# #     collected_files = []
       
# import os
# from pathlib import Path
# from typing import List, Optional

# def scan_files(
#     directory: str,
#     file_types: Optional[List[str]] = None,
#     max_depth: Optional[int] = None
# ) -> List[str]:
#     """
#     Recursively scan a directory for files with optional filtering.

#     Parameters:
#         directory (str): The starting directory path.
#         file_types (List[str], optional): List of file extensions to include (e.g., ['.txt', '.pdf']).
#                                           If None, include all file types.
#         max_depth (int, optional): Maximum depth for recursion. If None, traverse fully.

#     Returns:
#         List[str]: List of absolute file paths.
#     """
#     directory = Path(directory).resolve()
#     if not directory.is_dir():
#         raise ValueError(f"{directory} is not a valid directory")

#     collected_files = []

#     # Walk with depth control
#     for root, dirs, files in os.walk(directory):
#         current_depth = Path(root).relative_to(directory).parts
#         if max_depth is not None and len(current_depth) > max_depth:
#             # Skip deeper directories
#             dirs[:] = []  # prevent descending further
#             continue

#         # Exclude hidden directories
#         dirs[:] = [d for d in dirs if not d.startswith(".")]

#         for file in files:
#             if file.startswith("."):  # skip hidden files
#                 continue

#             filepath = Path(root) / file

#             # Filter by file extension if provided
#             if file_types:
#                 if filepath.suffix.lower() not in [ext.lower() for ext in file_types]:
#                     continue

#             collected_files.append(str(filepath.resolve()))

#     return collected_files


# print(scan_files("S:\stock", max_depth=3))
"""
Main entry point for File Integrity Checker application.
"""

import sys
import argparse
from pathlib import Path
from typing import Optional
import json

# Import project modules
try:
    from scanner import DirectoryScanner
    from hasher import FileHasher
    from database import HashDatabase
    from checker import IntegrityChecker
    from logger import setup_logger, log_event
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure all required modules are present in the project directory.")
    sys.exit(1)


class FileIntegrityChecker:
    """Main class orchestrating the file integrity checking process."""
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the File Integrity Checker.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self.load_config(config_path)
        self.logger = setup_logger(
            log_dir=self.config.get('log_directory', 'logs'),
            log_level=self.config.get('log_level', 'INFO')
        )
        self.database = HashDatabase(self.config.get('database_path', 'file_hashes.db'))
        
    def load_config(self, config_path: str) -> dict:
        """
        Load configuration from JSON file.
        
        Args:
            config_path: Path to config file
            
        Returns:
            Configuration dictionary
        """
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Config file not found: {config_path}")
            print("Using default configuration...")
            return self.get_default_config()
        except json.JSONDecodeError:
            print(f"Invalid JSON in config file: {config_path}")
            print("Using default configuration...")
            return self.get_default_config()
    
    @staticmethod
    def get_default_config() -> dict:
        """Return default configuration."""
        return {
            'hash_algorithm': 'sha256',
            'recursive_scan': True,
            'exclude_patterns': ['*.log', '__pycache__', '*.pyc', '.git'],
            'database_path': 'file_hashes.db',
            'log_directory': 'logs',
            'log_level': 'INFO'
        }
    
    def create_baseline(self, target_path: str) -> None:
        """
        Create initial baseline of file hashes.
        
        Args:
            target_path: Directory to scan and create baseline
        """
        self.logger.info(f"Creating baseline for: {target_path}")
        
        try:
            # Scan directory
            scanner = DirectoryScanner(
                target_path, 
                exclude_patterns=self.config.get('exclude_patterns', [])
            )
            files = scanner.scan_directory(
                recursive=self.config.get('recursive_scan', True)
            )
            
            self.logger.info(f"Found {len(files)} files to process")
            
            # Calculate hashes
            hasher = FileHasher(
                algorithm=self.config.get('hash_algorithm', 'sha256')
            )
            
            # Store in database
            for idx, file_info in enumerate(files, 1):
                try:
                    file_hash = hasher.hash_file(file_info.path)
                    self.database.store_hash(
                        file_path=file_info.relative_path,
                        file_hash=file_hash,
                        file_size=file_info.size,
                        modified_time=file_info.modified_time
                    )
                    
                    if idx % 100 == 0:
                        self.logger.info(f"Processed {idx}/{len(files)} files")
                
                except Exception as e:
                    self.logger.error(f"Error processing {file_info.path}: {e}")
            
            self.logger.info("Baseline creation completed successfully")
            print(f"✓ Baseline created with {len(files)} files")
        
        except Exception as e:
            self.logger.error(f"Failed to create baseline: {e}")
            print(f"✗ Error creating baseline: {e}")
            raise
    
    def verify_integrity(self, target_path: str) -> dict:
        """
        Verify file integrity against baseline.
        
        Args:
            target_path: Directory to verify
            
        Returns:
            Dictionary with verification results
        """
        self.logger.info(f"Verifying integrity for: {target_path}")
        
        try:
            # Scan current state
            scanner = DirectoryScanner(
                target_path,
                exclude_patterns=self.config.get('exclude_patterns', [])
            )
            current_files = scanner.scan_directory(
                recursive=self.config.get('recursive_scan', True)
            )
            
            # Verify against baseline
            checker = IntegrityChecker(
                database=self.database,
                hasher=FileHasher(algorithm=self.config.get('hash_algorithm', 'sha256'))
            )
            
            results = checker.verify_files(current_files)
            
            # Log results
            self._log_verification_results(results)
            
            return results
        
        except Exception as e:
            self.logger.error(f"Verification failed: {e}")
            raise
    
    def _log_verification_results(self, results: dict) -> None:
        """Log and display verification results."""
        if results['modified']:
            self.logger.warning(f"Modified files: {len(results['modified'])}")
            for file_path in results['modified']:
                self.logger.warning(f"  - {file_path}")
        
        if results['added']:
            self.logger.info(f"New files: {len(results['added'])}")
            for file_path in results['added']:
                self.logger.info(f"  + {file_path}")
        
        if results['deleted']:
            self.logger.warning(f"Deleted files: {len(results['deleted'])}")
            for file_path in results['deleted']:
                self.logger.warning(f"  - {file_path}")
        
        if not any([results['modified'], results['added'], results['deleted']]):
            self.logger.info("No changes detected - all files match baseline")
            print("✓ Integrity verified - no changes detected")
        else:
            print(f"\n⚠ Changes detected:")
            print(f"  Modified: {len(results['modified'])}")
            print(f"  Added: {len(results['added'])}")
            print(f"  Deleted: {len(results['deleted'])}")
    
    def update_baseline(self, target_path: str) -> None:
        """
        Update baseline with current file states.
        
        Args:
            target_path: Directory to update baseline for
        """
        self.logger.info(f"Updating baseline for: {target_path}")
        
        # Clear existing baseline
        self.database.clear_baseline()
        
        # Create new baseline
        self.create_baseline(target_path)


def main():
    """Main function with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description='File Integrity Checker - Monitor file changes and detect tampering'
    )
    
    parser.add_argument(
        'action',
        choices=['baseline', 'verify', 'update'],
        help='Action to perform: baseline (create initial), verify (check integrity), update (update baseline)'
    )
    
    parser.add_argument(
        'path',
        help='Directory path to scan'
    )
    
    parser.add_argument(
        '-c', '--config',
        default='config.json',
        help='Path to configuration file (default: config.json)'
    )
    
    parser.add_argument(
        '--cli',
        action='store_true',
        help='Use interactive CLI mode'
    )
    
    parser.add_argument(
        '--gui',
        action='store_true',
        help='Launch GUI interface'
    )
    
    args = parser.parse_args()
    
    # Launch GUI if requested
    if args.gui:
        try:
            from gui import launch_gui
            launch_gui()
            return
        except ImportError:
            print("GUI module not available")
            sys.exit(1)
    
    # Launch CLI if requested
    if args.cli:
        try:
            from cli import interactive_cli
            interactive_cli()
            return
        except ImportError:
            print("CLI module not available")
            sys.exit(1)
    
    # Standard operation
    try:
        checker = FileIntegrityChecker(config_path=args.config)
        
        if args.action == 'baseline':
            print(f"Creating baseline for: {args.path}")
            checker.create_baseline(args.path)
        
        elif args.action == 'verify':
            print(f"Verifying integrity of: {args.path}")
            checker.verify_integrity(args.path)
        
        elif args.action == 'update':
            print(f"Updating baseline for: {args.path}")
            checker.update_baseline(args.path)
    
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
