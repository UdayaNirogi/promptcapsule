"""Storage backends for vault mode."""

import json
import sqlite3
import os
from typing import Optional
from datetime import datetime
from .core import VaultBackend


class InMemoryBackend(VaultBackend):
    """Simple in-memory backend for testing."""
    
    def __init__(self):
        """Initialize in-memory storage."""
        self.store_dict: dict = {}
        self.counter = 0
    
    def store(self, text: str, checksum: str) -> str:
        """Store text and return a key."""
        self.counter += 1
        key = f"mem_{self.counter:08d}"
        self.store_dict[key] = {
            "text": text,
            "checksum": checksum,
            "timestamp": datetime.now().isoformat(),
        }
        return key
    
    def retrieve(self, key: str) -> str:
        """Retrieve text by key."""
        if key not in self.store_dict:
            raise KeyError(f"Key not found: {key}")
        return self.store_dict[key]["text"]


class SQLiteBackend(VaultBackend):
    """SQLite-based vault backend for local storage."""
    
    def __init__(self, db_path: str = "promptcapsule.db"):
        """Initialize SQLite backend."""
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS capsules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    text TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def store(self, text: str, checksum: str) -> str:
        """Store text and return a key."""
        # Generate a key based on timestamp and counter
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        counter = 0
        
        while True:
            key = f"sql_{timestamp}_{counter:04d}"
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        "INSERT INTO capsules (key, text, checksum) VALUES (?, ?, ?)",
                        (key, text, checksum),
                    )
                    conn.commit()
                return key
            except sqlite3.IntegrityError:
                counter += 1
                if counter > 9999:
                    raise RuntimeError("Failed to generate unique key")
    
    def retrieve(self, key: str) -> str:
        """Retrieve text by key."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT text FROM capsules WHERE key = ?",
                (key,),
            )
            row = cursor.fetchone()
            if row is None:
                raise KeyError(f"Key not found: {key}")
            return row[0]


class GitHubGistBackend(VaultBackend):
    """GitHub Gist-based vault backend (requires PyGithub)."""
    
    def __init__(self, token: str):
        """
        Initialize GitHub Gist backend.
        
        Args:
            token: GitHub personal access token
        """
        try:
            from github import Github
        except ImportError:
            raise ImportError(
                "PyGithub is required for GitHubGistBackend. "
                "Install with: pip install promptcapsule[vault]"
            )
        
        self.github = Github(token)
        self.user = self.github.get_user()
    
    def store(self, text: str, checksum: str) -> str:
        """Store text in a GitHub Gist."""
        timestamp = datetime.now().isoformat()
        description = f"PromptCapsule [{checksum[:8]}] - {timestamp}"
        
        files = {
            "prompt.txt": {
                "content": text,
            }
        }
        
        gist = self.user.create_gist(
            public=False,
            files=files,
            description=description,
        )
        
        return gist.id
    
    def retrieve(self, key: str) -> str:
        """Retrieve text from a GitHub Gist."""
        try:
            gist = self.github.get_gist(key)
            # Assume the content is in a file named "prompt.txt"
            if "prompt.txt" in gist.files:
                return gist.files["prompt.txt"].content
            else:
                # Try first file
                first_file = next(iter(gist.files.values()))
                return first_file.content
        except Exception as e:
            raise KeyError(f"Failed to retrieve gist {key}: {e}")


class S3Backend(VaultBackend):
    """AWS S3-based vault backend (requires boto3)."""
    
    def __init__(self, bucket: str, region: str = "us-east-1", prefix: str = "promptcapsule/"):
        """
        Initialize S3 backend.
        
        Args:
            bucket: S3 bucket name
            region: AWS region
            prefix: S3 prefix for all keys
        """
        try:
            import boto3
        except ImportError:
            raise ImportError(
                "boto3 is required for S3Backend. "
                "Install with: pip install promptcapsule[vault]"
            )
        
        self.s3_client = boto3.client("s3", region_name=region)
        self.bucket = bucket
        self.prefix = prefix
    
    def store(self, text: str, checksum: str) -> str:
        """Store text in S3."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        key = f"{self.prefix}{timestamp}_{checksum[:8]}.txt"
        
        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=text.encode('utf-8'),
            Metadata={
                "checksum": checksum,
                "timestamp": timestamp,
            },
        )
        
        return key
    
    def retrieve(self, key: str) -> str:
        """Retrieve text from S3."""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
            return response["Body"].read().decode('utf-8')
        except Exception as e:
            raise KeyError(f"Failed to retrieve from S3 {key}: {e}")
