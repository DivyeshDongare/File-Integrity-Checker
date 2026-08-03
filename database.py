"""
Database module for storing and retrieving file hashes.
Uses SQLite for persistent storage of file integrity baselines.
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from contextlib import contextmanager


class HashDatabase:
    """SQLite database handler for file hash storage."""
    
    # Database schema version
    SCHEMA_VERSION = 1
    
    def __init__(self, db_path: str = 'file_hashes.db'):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.connection = None
        self._initialize_database()
    
    def _initialize_database(self) -> None:
        """Initialize database and create tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Create file hashes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS file_hashes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL UNIQUE,
                    hash TEXT NOT NULL,
                    algorithm TEXT DEFAULT 'sha256',
                    size INTEGER NOT NULL,
                    modified_time REAL,
                    permissions TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            # Create indexes for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_file_path 
                ON file_hashes(file_path)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_hash 
                ON file_hashes(hash)
            ''')
            
            # Create metadata table for database info
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            ''')
            
            # Store schema version
            cursor.execute('''
                INSERT OR REPLACE INTO metadata (key, value) 
                VALUES ('schema_version', ?)
            ''', (str(self.SCHEMA_VERSION),))
            
            # Create audit log table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    file_path TEXT,
                    details TEXT,
                    user TEXT
                )
            ''')
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """
        Context manager for database connections.
        
        Yields:
            SQLite connection object
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        finally:
            conn.close()
    
    def store_hash(self,
                   file_path: str,
                   file_hash: str,
                   file_size: int,
                   modified_time: float,
                   algorithm: str = 'sha256',
                   permissions: Optional[str] = None) -> bool:
        """
        Store or update file hash in database.
        
        Args:
            file_path: Relative path to the file
            file_hash: Hash value
            file_size: File size in bytes
            modified_time: File modification timestamp
            algorithm: Hash algorithm used
            permissions: File permissions (octal string)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                timestamp = datetime.now().isoformat()
                
                # Use INSERT OR REPLACE to handle updates
                cursor.execute('''
                    INSERT OR REPLACE INTO file_hashes 
                    (file_path, hash, algorithm, size, modified_time, permissions, 
                     created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, 
                            COALESCE((SELECT created_at FROM file_hashes WHERE file_path = ?), ?),
                            ?)
                ''', (file_path, file_hash, algorithm, file_size, modified_time,
                      permissions, file_path, timestamp, timestamp))
                
                conn.commit()
                
                # Log to audit table
                self._log_audit(conn, 'STORE', file_path, 
                               f"hash={file_hash[:16]}..., size={file_size}")
                
                return True
        
        except sqlite3.Error as e:
            print(f"Database error storing hash: {e}")
            return False
    
    def get_hash(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve hash information for a file.
        
        Args:
            file_path: Relative path to the file
            
        Returns:
            Dictionary with file information or None if not found
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT file_path, hash, algorithm, size, modified_time, 
                           permissions, created_at, updated_at
                    FROM file_hashes
                    WHERE file_path = ?
                ''', (file_path,))
                
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                
                return None
        
        except sqlite3.Error as e:
            print(f"Database error retrieving hash: {e}")
            return None
    
    def get_all_hashes(self) -> List[Dict[str, Any]]:
        """
        Retrieve all file hashes from database.
        
        Returns:
            List of dictionaries with file information
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT file_path, hash, algorithm, size, modified_time,
                           permissions, created_at, updated_at
                    FROM file_hashes
                    ORDER BY file_path
                ''')
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        
        except sqlite3.Error as e:
            print(f"Database error retrieving all hashes: {e}")
            return []
    
    def delete_hash(self, file_path: str) -> bool:
        """
        Delete hash entry for a file.
        
        Args:
            file_path: Relative path to the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM file_hashes WHERE file_path = ?', 
                             (file_path,))
                conn.commit()
                
                self._log_audit(conn, 'DELETE', file_path, 'Entry removed')
                
                return cursor.rowcount > 0
        
        except sqlite3.Error as e:
            print(f"Database error deleting hash: {e}")
            return False
    
    def clear_baseline(self) -> bool:
        """
        Clear all file hashes (reset baseline).
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM file_hashes')
                conn.commit()
                
                self._log_audit(conn, 'CLEAR_BASELINE', None, 
                               f'Removed {cursor.rowcount} entries')
                
                return True
        
        except sqlite3.Error as e:
            print(f"Database error clearing baseline: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with statistics
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Total files
                cursor.execute('SELECT COUNT(*) FROM file_hashes')
                total_files = cursor.fetchone()[0]
                
                # Total size
                cursor.execute('SELECT SUM(size) FROM file_hashes')
                total_size = cursor.fetchone()[0] or 0
                
                # Algorithms used
                cursor.execute('''
                    SELECT algorithm, COUNT(*) as count 
                    FROM file_hashes 
                    GROUP BY algorithm
                ''')
                algorithms = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Latest update
                cursor.execute('SELECT MAX(updated_at) FROM file_hashes')
                latest_update = cursor.fetchone()[0]
                
                return {
                    'total_files': total_files,
                    'total_size': total_size,
                    'algorithms': algorithms,
                    'latest_update': latest_update
                }
        
        except sqlite3.Error as e:
            print(f"Database error getting statistics: {e}")
            return {}
    
    def search_by_hash(self, hash_value: str) -> List[Dict[str, Any]]:
        """
        Search for files with a specific hash (detect duplicates).
        
        Args:
            hash_value: Hash to search for
            
        Returns:
            List of files with matching hash
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT file_path, hash, size, modified_time
                    FROM file_hashes
                    WHERE hash = ?
                ''', (hash_value,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        
        except sqlite3.Error as e:
            print(f"Database error searching by hash: {e}")
            return []
    
    def update_metadata(self, key: str, value: str) -> bool:
        """
        Update metadata key-value pair.
        
        Args:
            key: Metadata key
            value: Metadata value
            
        Returns:
            True if successful
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO metadata (key, value) 
                    VALUES (?, ?)
                ''', (key, value))
                
                conn.commit()
                return True
        
        except sqlite3.Error as e:
            print(f"Database error updating metadata: {e}")
            return False
    
    def get_metadata(self, key: str) -> Optional[str]:
        """
        Get metadata value by key.
        
        Args:
            key: Metadata key
            
        Returns:
            Metadata value or None
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT value FROM metadata WHERE key = ?', (key,))
                row = cursor.fetchone()
                
                return row[0] if row else None
        
        except sqlite3.Error as e:
            print(f"Database error getting metadata: {e}")
            return None
    
    def _log_audit(self, conn: sqlite3.Connection,
                   operation: str,
                   file_path: Optional[str],
                   details: str) -> None:
        """
        Internal method to log operations to audit table.
        
        Args:
            conn: Database connection
            operation: Operation type
            file_path: File path involved
            details: Additional details
        """
        try:
            cursor = conn.cursor()
            timestamp = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO audit_log (timestamp, operation, file_path, details)
                VALUES (?, ?, ?, ?)
            ''', (timestamp, operation, file_path, details))
            
            conn.commit()
        
        except sqlite3.Error:
            # Don't fail main operation if audit logging fails
            pass
    
    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve recent audit log entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of audit log entries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT timestamp, operation, file_path, details
                    FROM audit_log
                    ORDER BY id DESC
                    LIMIT ?
                ''', (limit,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        
        except sqlite3.Error as e:
            print(f"Database error retrieving audit log: {e}")
            return []
    
    def export_baseline(self, output_file: str) -> bool:
        """
        Export baseline to JSON file.
        
        Args:
            output_file: Path to output JSON file
            
        Returns:
            True if successful
        """
        try:
            baseline = self.get_all_hashes()
            
            with open(output_file, 'w') as f:
                json.dump(baseline, f, indent=2)
            
            return True
        
        except Exception as e:
            print(f"Error exporting baseline: {e}")
            return False
    
    def import_baseline(self, input_file: str, clear_existing: bool = False) -> bool:
        """
        Import baseline from JSON file.
        
        Args:
            input_file: Path to input JSON file
            clear_existing: Clear existing baseline before import
            
        Returns:
            True if successful
        """
        try:
            with open(input_file, 'r') as f:
                baseline = json.load(f)
            
            if clear_existing:
                self.clear_baseline()
            
            for entry in baseline:
                self.store_hash(
                    file_path=entry['file_path'],
                    file_hash=entry['hash'],
                    file_size=entry['size'],
                    modified_time=entry['modified_time'],
                    algorithm=entry.get('algorithm', 'sha256'),
                    permissions=entry.get('permissions')
                )
            
            return True
        
        except Exception as e:
            print(f"Error importing baseline: {e}")
            return False
    
    def close(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
