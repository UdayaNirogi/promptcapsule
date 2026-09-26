"""Tests for backends."""

import os
import tempfile

import pytest

from promptcapsule.backends import InMemoryBackend, SQLiteBackend


class TestInMemoryBackend:
    """Test InMemoryBackend."""
    
    def test_store_and_retrieve(self):
        """Test basic store and retrieve."""
        backend = InMemoryBackend()
        key = backend.store("test content", "checksum123")
        
        assert backend.retrieve(key) == "test content"
    
    def test_unique_keys(self):
        """Test that keys are unique."""
        backend = InMemoryBackend()
        
        key1 = backend.store("content1", "check1")
        key2 = backend.store("content2", "check2")
        
        assert key1 != key2
        assert backend.retrieve(key1) == "content1"
        assert backend.retrieve(key2) == "content2"
    
    def test_key_not_found(self):
        """Test KeyError on missing key."""
        backend = InMemoryBackend()
        
        with pytest.raises(KeyError):
            backend.retrieve("nonexistent")


class TestSQLiteBackend:
    """Test SQLiteBackend."""
    
    def test_store_and_retrieve(self):
        """Test basic store and retrieve."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            backend = SQLiteBackend(db_path)
            
            key = backend.store("test content", "checksum123")
            retrieved = backend.retrieve(key)
            
            assert retrieved == "test content"
    
    def test_persistence(self):
        """Test that data persists across instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            
            # Store with first instance
            backend1 = SQLiteBackend(db_path)
            key = backend1.store("persistent content", "checksum123")
            
            # Retrieve with second instance
            backend2 = SQLiteBackend(db_path)
            retrieved = backend2.retrieve(key)
            
            assert retrieved == "persistent content"
    
    def test_key_not_found(self):
        """Test KeyError on missing key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            backend = SQLiteBackend(db_path)
            
            with pytest.raises(KeyError):
                backend.retrieve("nonexistent")
    
    def test_multiple_stores(self):
        """Test storing multiple items."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            backend = SQLiteBackend(db_path)
            
            keys = []
            for i in range(5):
                key = backend.store(f"content{i}", f"checksum{i}")
                keys.append(key)
            
            # Verify all keys are unique and retrievable
            assert len(set(keys)) == 5
            
            for i, key in enumerate(keys):
                assert backend.retrieve(key) == f"content{i}"
    
    def test_unicode_content(self):
        """Test storing unicode content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            backend = SQLiteBackend(db_path)
            
            content = "Unicode test: 你好 🌍 مرحبا"
            key = backend.store(content, "checksum123")
            
            assert backend.retrieve(key) == content
    
    def test_large_content(self):
        """Test storing large content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            backend = SQLiteBackend(db_path)
            
            # 10MB of content
            large_content = "X" * (10 * 1024 * 1024)
            key = backend.store(large_content, "checksum123")
            
            assert backend.retrieve(key) == large_content


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
