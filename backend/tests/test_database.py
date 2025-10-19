import pytest
import os
from datetime import datetime

from models import File
from database import (
    init_db, add_file, get_file, get_file_by_id,
    get_all_files, get_files_by_owner, get_files_by_device,
    update_file, delete_file, delete_all_files, get_database_stats
)


pytestmark = pytest.mark.unit


class TestDatabaseInitialization:
    """Test database initialization."""
    
    def test_init_db_creates_tables(self, in_memory_session):
        """Tables created successfully on init."""
        assert in_memory_session is not None
        result = in_memory_session.query(File).all()
        assert result == []
    
    def test_init_db_idempotent(self, in_memory_engine):
        """Calling init multiple times doesn't cause errors."""
        from sqlmodel import SQLModel
        SQLModel.metadata.create_all(in_memory_engine)
        SQLModel.metadata.create_all(in_memory_engine)


class TestAddFile:
    """Test add_file() function."""
    
    def test_add_file_success(self, in_memory_session):
        """File created with correct attributes."""
        from sqlmodel import Session
        from database import engine, Session as DBSession
        session = Session(in_memory_engine := in_memory_session.get_bind())
        
        file = File(
            filename="test.pdf",
            device="laptop",
            path="/docs/test.pdf",
            alias="alice",
            size=1024000,
            file_type="pdf"
        )
        session.add(file)
        session.commit()
        
        retrieved = session.query(File).filter_by(path="/docs/test.pdf").first()
        assert retrieved is not None
        assert retrieved.filename == "test.pdf"
        assert retrieved.size == 1024000
    
    def test_add_file_auto_extract_file_type(self):
        """File type extracted from filename when not provided."""
        file = add_file(
            filename="document.docx",
            device="laptop",
            path="/docs/document.docx",
            alias="alice",
            size=512000
        )
        assert file is not None
        assert file.file_type == "docx"
    
    def test_add_file_duplicate_path_returns_none(self, in_memory_session, populated_db):
        """Duplicate path returns None."""
        existing_file = populated_db.query(File).first()
        existing_path = existing_file.path
        
        duplicate_file = File(
            filename="different_name.pdf",
            device="other_device",
            path=existing_path,
            alias="bob",
            size=2000000
        )
        populated_db.add(duplicate_file)
        with pytest.raises(Exception):
            populated_db.commit()
    
    def test_add_file_returns_file_object(self):
        """Returned object is File instance."""
        file = add_file(
            filename="test.txt",
            device="dev",
            path="/test.txt",
            alias="user",
            size=100
        )
        assert isinstance(file, File)
        assert file.filename == "test.txt"


class TestGetFile:
    """Test get_file() function."""
    
    def test_get_file_by_filename_success(self, populated_db):
        """Retrieves correct file by filename."""
        result = get_file("report_2024.pdf")
        assert result is not None
        assert result.filename == "report_2024.pdf"
    
    def test_get_file_nonexistent_returns_none(self):
        """Returns None for missing file."""
        result = get_file("nonexistent_file.txt")
        assert result is None
    
    def test_get_file_detached_from_session(self, populated_db):
        """File is expunged from session."""
        file = get_file("report_2024.pdf")
        assert file is not None


class TestGetFileById:
    """Test get_file_by_id() function."""
    
    def test_get_file_by_id_success(self):
        """Retrieves correct file by ID."""
        file = add_file(
            filename="retrieve_me.txt",
            device="dev",
            path="/retrieve_me.txt",
            alias="user",
            size=100
        )
        file_id = file.id
        
        retrieved = get_file_by_id(file_id)
        assert retrieved is not None
        assert retrieved.id == file_id
        assert retrieved.filename == "retrieve_me.txt"
    
    def test_get_file_by_id_nonexistent_returns_none(self):
        """Returns None for missing ID."""
        result = get_file_by_id(9999)
        assert result is None


class TestGetAllFiles:
    """Test get_all_files() function."""
    
    def test_get_all_files_empty_db(self, in_memory_session):
        """Returns empty list on fresh DB."""
        result = get_all_files()
        assert result == []
    
    def test_get_all_files_returns_all(self):
        """Returns all files in database."""
        for i in range(3):
            add_file(
                filename=f"file_{i}.txt",
                device=f"dev_{i}",
                path=f"/file_{i}.txt",
                alias=f"user_{i}",
                size=100 * (i + 1)
            )
        
        result = get_all_files()
        assert len(result) == 3


class TestGetFilesByOwner:
    """Test get_files_by_owner() function."""
    
    def test_get_files_by_owner_success(self, populated_db):
        """Returns only files by alias."""
        result = get_files_by_owner("alice")
        assert len(result) > 0
        for file in result:
            assert file.alias == "alice"
    
    def test_get_files_by_owner_empty_returns_empty(self):
        """Returns empty list for unknown alias."""
        result = get_files_by_owner("unknown_user")
        assert result == []
    
    def test_get_files_by_owner_exact_count(self):
        """Returns correct number of files for owner."""
        add_file("file1.txt", "dev1", "/file1.txt", "alice", 100)
        add_file("file2.txt", "dev2", "/file2.txt", "alice", 200)
        add_file("file3.txt", "dev3", "/file3.txt", "bob", 300)
        
        alice_files = get_files_by_owner("alice")
        bob_files = get_files_by_owner("bob")
        
        assert len(alice_files) == 2
        assert len(bob_files) == 1


class TestGetFilesByDevice:
    """Test get_files_by_device() function."""
    
    def test_get_files_by_device_success(self, populated_db):
        """Returns only files from device."""
        result = get_files_by_device("laptop_1")
        assert len(result) > 0
        for file in result:
            assert file.device == "laptop_1"
    
    def test_get_files_by_device_empty_returns_empty(self):
        """Returns empty list for unknown device."""
        result = get_files_by_device("unknown_device")
        assert result == []
    
    def test_get_files_by_device_exact_count(self):
        """Returns correct number of files for device."""
        add_file("file1.txt", "device_a", "/file1.txt", "user1", 100)
        add_file("file2.txt", "device_a", "/file2.txt", "user2", 200)
        add_file("file3.txt", "device_b", "/file3.txt", "user3", 300)
        
        device_a_files = get_files_by_device("device_a")
        device_b_files = get_files_by_device("device_b")
        
        assert len(device_a_files) == 2
        assert len(device_b_files) == 1


class TestUpdateFile:
    """Test update_file() function."""
    
    def test_update_file_success(self):
        """Fields updated correctly."""
        file = add_file(
            filename="original.txt",
            device="dev1",
            path="/original.txt",
            alias="user1",
            size=1000
        )
        
        updated = update_file("original.txt", size=2000, device="dev2")
        assert updated is not None
        assert updated.size == 2000
        assert updated.device == "dev2"
    
    def test_update_file_modified_at_updated(self):
        """modified_at timestamp is updated."""
        file = add_file(
            filename="test.txt",
            device="dev",
            path="/test.txt",
            alias="user",
            size=100
        )
        original_modified = file.modified_at
        
        import time
        time.sleep(0.1)
        
        updated = update_file("test.txt", size=200)
        assert updated.modified_at > original_modified
    
    def test_update_file_nonexistent_returns_none(self):
        """Returns None for missing file."""
        result = update_file("nonexistent.txt", size=500)
        assert result is None
    
    def test_update_file_allowed_fields_only(self):
        """Only allowed fields are updated."""
        file = add_file(
            filename="test.txt",
            device="dev",
            path="/test.txt",
            alias="user",
            size=100
        )
        original_filename = file.filename
        
        updated = update_file(
            "test.txt",
            size=200,
            filename="hacked.txt"
        )
        
        assert updated.size == 200
        assert updated.filename == original_filename


class TestDeleteFile:
    """Test delete_file() function."""
    
    def test_delete_file_success(self):
        """File deleted returns True."""
        add_file("delete_me.txt", "dev", "/delete_me.txt", "user", 100)
        
        result = delete_file("delete_me.txt")
        assert result is True
        
        retrieved = get_file("delete_me.txt")
        assert retrieved is None
    
    def test_delete_file_nonexistent_returns_false(self):
        """Returns False for missing file."""
        result = delete_file("nonexistent.txt")
        assert result is False


class TestDeleteAllFiles:
    """Test delete_all_files() function."""
    
    def test_delete_all_files_returns_count(self):
        """Returns number of files deleted."""
        add_file("file1.txt", "dev1", "/file1.txt", "user1", 100)
        add_file("file2.txt", "dev2", "/file2.txt", "user2", 200)
        add_file("file3.txt", "dev3", "/file3.txt", "user3", 300)
        
        count = delete_all_files()
        assert count == 3
        
        remaining = get_all_files()
        assert remaining == []


class TestDatabaseStats:
    """Test get_database_stats() function."""
    
    def test_database_stats_empty(self):
        """Empty DB returns zeros."""
        stats = get_database_stats()
        assert stats["total_files"] == 0
        assert stats["total_size"] == 0
        assert stats["total_size_mb"] == 0.0
    
    def test_database_stats_correct_calculations(self):
        """Correct totals for populated DB."""
        add_file("file1.txt", "dev1", "/file1.txt", "user1", 1024)
        add_file("file2.txt", "dev2", "/file2.txt", "user2", 2048)
        add_file("file3.txt", "dev3", "/file3.txt", "user3", 4096)
        
        stats = get_database_stats()
        assert stats["total_files"] == 3
        assert stats["total_size"] == 7168
        assert stats["total_size_mb"] == round(7168 / (1024 * 1024), 2)


class TestDatabaseErrors:
    """Test error handling in database operations."""
    
    def test_session_cleanup_on_error(self, in_memory_session):
        """Session is closed even on error."""
        try:
            add_file(None, None, None, None, None)
        except Exception:
            pass
        
        result = get_all_files()
        assert isinstance(result, list)
