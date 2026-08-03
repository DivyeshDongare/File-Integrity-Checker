"""
File hasher module for generating cryptographic hashes of files.
Supports multiple hashing algorithms including SHA-256, SHA-512, MD5, and SHA-1.
"""

import hashlib
import sys
from pathlib import Path
from typing import Optional, Dict, List
from enum import Enum


class HashAlgorithm(Enum):
    """Supported hash algorithms."""
    MD5 = 'md5'
    SHA1 = 'sha1'
    SHA256 = 'sha256'
    SHA384 = 'sha384'
    SHA512 = 'sha512'
    BLAKE2B = 'blake2b'
    BLAKE2S = 'blake2s'


class FileHasher:
    """Class for calculating cryptographic hashes of files."""
    
    # Chunk size for reading files (128KB for optimal performance)
    CHUNK_SIZE = 128 * 1024
    
    def __init__(self, algorithm: str = 'sha256'):
        """
        Initialize FileHasher with specified algorithm.
        
        Args:
            algorithm: Hash algorithm to use (default: sha256)
            
        Raises:
            ValueError: If algorithm is not supported
        """
        self.algorithm = algorithm.lower()
        self._validate_algorithm()
    
    def _validate_algorithm(self) -> None:
        """Validate that the chosen algorithm is supported."""
        valid_algorithms = [algo.value for algo in HashAlgorithm]
        
        if self.algorithm not in valid_algorithms:
            raise ValueError(
                f"Unsupported algorithm: {self.algorithm}. "
                f"Supported algorithms: {', '.join(valid_algorithms)}"
            )
    
    def hash_file(self, file_path: str) -> str:
        """
        Calculate hash of a file.
        
        Args:
            file_path: Path to the file to hash
            
        Returns:
            Hexadecimal hash string
            
        Raises:
            FileNotFoundError: If file does not exist
            PermissionError: If file cannot be read
            IOError: If file reading fails
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        # Use optimized file_digest for Python 3.11+
        if sys.version_info >= (3, 11):
            return self._hash_file_optimized(path)
        else:
            return self._hash_file_chunked(path)
    
    def _hash_file_optimized(self, path: Path) -> str:
        """
        Hash file using hashlib.file_digest (Python 3.11+).
        
        Args:
            path: Path object to the file
            
        Returns:
            Hexadecimal hash string
        """
        try:
            with open(path, 'rb', buffering=0) as f:
                digest = hashlib.file_digest(f, self.algorithm)
                return digest.hexdigest()
        except PermissionError:
            raise PermissionError(f"Permission denied reading file: {path}")
        except IOError as e:
            raise IOError(f"Error reading file {path}: {e}")
    
    def _hash_file_chunked(self, path: Path) -> str:
        """
        Hash file by reading in chunks (for Python < 3.11 or manual control).
        Uses memoryview and readinto for optimal performance.
        
        Args:
            path: Path object to the file
            
        Returns:
            Hexadecimal hash string
        """
        try:
            # Create hash object
            hash_obj = hashlib.new(self.algorithm)
            
            # Use bytearray with memoryview for efficient reading
            buffer = bytearray(self.CHUNK_SIZE)
            buffer_view = memoryview(buffer)
            
            with open(path, 'rb', buffering=0) as f:
                # Read file in chunks using readinto for better performance
                while True:
                    bytes_read = f.readinto(buffer_view)
                    if bytes_read == 0:
                        break
                    hash_obj.update(buffer_view[:bytes_read])
            
            return hash_obj.hexdigest()
        
        except PermissionError:
            raise PermissionError(f"Permission denied reading file: {path}")
        except IOError as e:
            raise IOError(f"Error reading file {path}: {e}")
    
    def hash_file_simple(self, file_path: str) -> str:
        """
        Simplified hash calculation using standard chunk reading.
        Useful for compatibility and simpler implementations.
        
        Args:
            file_path: Path to the file to hash
            
        Returns:
            Hexadecimal hash string
        """
        hash_obj = hashlib.new(self.algorithm)
        
        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(self.CHUNK_SIZE):
                    hash_obj.update(chunk)
            
            return hash_obj.hexdigest()
        
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        except PermissionError:
            raise PermissionError(f"Permission denied: {file_path}")
        except IOError as e:
            raise IOError(f"Error reading file: {e}")
    
    def hash_bytes(self, data: bytes) -> str:
        """
        Calculate hash of raw bytes.
        
        Args:
            data: Bytes to hash
            
        Returns:
            Hexadecimal hash string
        """
        hash_obj = hashlib.new(self.algorithm)
        hash_obj.update(data)
        return hash_obj.hexdigest()
    
    def hash_string(self, text: str, encoding: str = 'utf-8') -> str:
        """
        Calculate hash of a string.
        
        Args:
            text: String to hash
            encoding: Character encoding (default: utf-8)
            
        Returns:
            Hexadecimal hash string
        """
        return self.hash_bytes(text.encode(encoding))
    
    def hash_multiple_files(self, file_paths: List[str]) -> Dict[str, str]:
        """
        Calculate hashes for multiple files.
        
        Args:
            file_paths: List of file paths to hash
            
        Returns:
            Dictionary mapping file paths to their hash values
        """
        results = {}
        
        for file_path in file_paths:
            try:
                results[file_path] = self.hash_file(file_path)
            except Exception as e:
                results[file_path] = f"ERROR: {str(e)}"
        
        return results
    
    def verify_hash(self, file_path: str, expected_hash: str) -> bool:
        """
        Verify if a file's hash matches the expected hash.
        
        Args:
            file_path: Path to the file to verify
            expected_hash: Expected hash value (case-insensitive)
            
        Returns:
            True if hashes match, False otherwise
        """
        try:
            calculated_hash = self.hash_file(file_path)
            return calculated_hash.lower() == expected_hash.lower()
        except Exception:
            return False
    
    @staticmethod
    def get_supported_algorithms() -> List[str]:
        """
        Get list of supported hash algorithms.
        
        Returns:
            List of algorithm names
        """
        return [algo.value for algo in HashAlgorithm]
    
    @staticmethod
    def detect_algorithm_from_hash(hash_value: str) -> Optional[str]:
        """
        Detect hash algorithm based on hash length.
        
        Args:
            hash_value: Hash string to analyze
            
        Returns:
            Detected algorithm name or None if unknown
        """
        hash_length = len(hash_value)
        
        length_map = {
            32: 'md5',
            40: 'sha1',
            64: 'sha256',
            96: 'sha384',
            128: 'sha512'
        }
        
        return length_map.get(hash_length)


class MultiHasher:
    """Calculate multiple hash algorithms simultaneously for a file."""
    
    def __init__(self, algorithms: Optional[List[str]] = None):
        """
        Initialize MultiHasher with specified algorithms.
        
        Args:
            algorithms: List of algorithms to use (default: ['md5', 'sha256'])
        """
        self.algorithms = algorithms or ['md5', 'sha256']
        self.hashers = {algo: FileHasher(algo) for algo in self.algorithms}
    
    def hash_file(self, file_path: str) -> Dict[str, str]:
        """
        Calculate multiple hashes for a file simultaneously.
        
        Args:
            file_path: Path to the file to hash
            
        Returns:
            Dictionary mapping algorithm names to hash values
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Create hash objects for all algorithms
        hash_objects = {algo: hashlib.new(algo) for algo in self.algorithms}
        
        # Read file once and update all hash objects
        buffer = bytearray(128 * 1024)
        buffer_view = memoryview(buffer)
        
        try:
            with open(path, 'rb', buffering=0) as f:
                while True:
                    bytes_read = f.readinto(buffer_view)
                    if bytes_read == 0:
                        break
                    
                    # Update all hash objects with same data
                    for hash_obj in hash_objects.values():
                        hash_obj.update(buffer_view[:bytes_read])
            
            # Return all hash values
            return {algo: hash_obj.hexdigest() 
                    for algo, hash_obj in hash_objects.items()}
        
        except (PermissionError, IOError) as e:
            raise IOError(f"Error reading file {file_path}: {e}")


# Convenience functions
def calculate_file_hash(file_path: str, algorithm: str = 'sha256') -> str:
    """
    Convenience function to calculate file hash.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use
        
    Returns:
        Hexadecimal hash string
    """
    hasher = FileHasher(algorithm)
    return hasher.hash_file(file_path)


def verify_file_integrity(file_path: str, expected_hash: str, 
                         algorithm: Optional[str] = None) -> bool:
    """
    Convenience function to verify file integrity.
    
    Args:
        file_path: Path to the file
        expected_hash: Expected hash value
        algorithm: Hash algorithm (auto-detected if None)
        
    Returns:
        True if file is intact, False otherwise
    """
    if algorithm is None:
        algorithm = FileHasher.detect_algorithm_from_hash(expected_hash)
        if algorithm is None:
            raise ValueError("Could not detect algorithm from hash length")
    
    hasher = FileHasher(algorithm)
    return hasher.verify_hash(file_path, expected_hash)
