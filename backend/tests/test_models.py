import pytest
from datetime import datetime
from pydantic import ValidationError
from models import File


pytestmark = pytest.mark.unit


class TestFileModelCreation:
    """Test File model instantiation with various field combinations."""
    
    def test_file_creation_success(self):
        """Create File with all required fields."""
        file = File(
            filename="test.txt",
            device="device_1",
            path="/path/to/test.txt",
            alias="user_1",
            size=1024
        )
        assert file.filename == "test.txt"
        assert file.device == "device_1"
        assert file.path == "/path/to/test.txt"
        assert file.alias == "user_1"
        assert file.size == 1024
    
    def test_file_creation_with_optional_fields(self):
        """Create File with file_type specified."""
        file = File(
            filename="document.pdf",
            device="laptop",
            path="/docs/document.pdf",
            alias="alice",
            size=2048000,
            file_type="pdf"
        )
        assert file.file_type == "pdf"
    
    def test_file_default_timestamps(self):
        """Verify uploaded_at and modified_at default to datetime.utcnow()."""
        file1 = File(
            filename="file1.txt",
            device="dev1",
            path="/file1.txt",
            alias="user1",
            size=100
        )
        file2 = File(
            filename="file2.txt",
            device="dev2",
            path="/file2.txt",
            alias="user2",
            size=200
        )
        assert isinstance(file1.uploaded_at, datetime)
        assert isinstance(file1.modified_at, datetime)
        assert isinstance(file2.uploaded_at, datetime)
        assert isinstance(file2.modified_at, datetime)
    
    def test_file_optional_file_type_none(self):
        """File with file_type=None is valid."""
        file = File(
            filename="no_extension",
            device="device",
            path="/no_extension",
            alias="user",
            size=512,
            file_type=None
        )
        assert file.file_type is None


class TestFileModelValidation:
    """Test File model field validation and constraints."""
    
    def test_file_with_minimal_fields(self):
        """File can be created with minimal required fields."""
        file = File(
            filename="test.txt",
            device="device",
            path="/path",
            alias="user",
            size=100
        )
        assert file.filename == "test.txt"
        assert file.device == "device"
        assert file.path == "/path"
        assert file.alias == "user"
        assert file.size == 100
    
    def test_file_field_types_string(self):
        """String fields accept only strings."""
        file = File(
            filename="test.txt",
            device="dev",
            path="/test",
            alias="user",
            size=100
        )
        assert isinstance(file.filename, str)
        assert isinstance(file.device, str)
        assert isinstance(file.path, str)
        assert isinstance(file.alias, str)
    
    def test_file_field_types_int(self):
        """Size field accepts only integers."""
        file = File(
            filename="test.txt",
            device="dev",
            path="/test",
            alias="user",
            size=1024
        )
        assert isinstance(file.size, int)
    
    def test_file_field_types_datetime(self):
        """Timestamp fields are datetime objects."""
        file = File(
            filename="test.txt",
            device="dev",
            path="/test",
            alias="user",
            size=100
        )
        assert isinstance(file.uploaded_at, datetime)
        assert isinstance(file.modified_at, datetime)


class TestFileModelMethods:
    """Test File model methods (repr, to_dict)."""
    
    def test_repr_method_format(self):
        """__repr__() returns formatted string."""
        file = File(
            filename="test.txt",
            device="dev",
            path="/test",
            alias="user",
            size=1024
        )
        repr_str = repr(file)
        assert "File" in repr_str
        assert "test.txt" in repr_str
        assert "user" in repr_str
        assert "1024" in repr_str
    
    def test_repr_method_with_id(self):
        """__repr__() includes ID when present."""
        file = File(
            id=42,
            filename="test.txt",
            device="dev",
            path="/test",
            alias="user",
            size=1024
        )
        repr_str = repr(file)
        assert "42" in repr_str
    
    def test_to_dict_method_structure(self):
        """to_dict() returns correct dictionary structure."""
        file = File(
            filename="test.txt",
            device="dev",
            path="/test",
            alias="user",
            size=1024,
            file_type="txt"
        )
        file_dict = file.to_dict()
        
        assert "id" in file_dict
        assert "filename" in file_dict
        assert "device" in file_dict
        assert "path" in file_dict
        assert "alias" in file_dict
        assert "size" in file_dict
        assert "uploaded_at" in file_dict
        assert "modified_at" in file_dict
        assert "file_type" in file_dict
    
    def test_to_dict_method_values(self):
        """to_dict() returns correct values."""
        file = File(
            filename="test.txt",
            device="dev",
            path="/test",
            alias="user",
            size=1024,
            file_type="txt"
        )
        file_dict = file.to_dict()
        
        assert file_dict["filename"] == "test.txt"
        assert file_dict["device"] == "dev"
        assert file_dict["path"] == "/test"
        assert file_dict["alias"] == "user"
        assert file_dict["size"] == 1024
        assert file_dict["file_type"] == "txt"
    
    def test_to_dict_datetime_isoformat(self):
        """Timestamps in to_dict() are ISO format strings."""
        file = File(
            filename="test.txt",
            device="dev",
            path="/test",
            alias="user",
            size=1024
        )
        file_dict = file.to_dict()
        
        uploaded_at = file_dict["uploaded_at"]
        modified_at = file_dict["modified_at"]
        
        assert isinstance(uploaded_at, str)
        assert isinstance(modified_at, str)
        assert "T" in uploaded_at
        assert "T" in modified_at


class TestFileModelEdgeCases:
    """Test File model with edge cases and boundary values."""
    
    @pytest.mark.parametrize("file_type", [
        "txt", "pdf", "jpg", "png", "csv", "zip", "json", "xml"
    ])
    def test_various_file_types(self, file_type):
        """File accepts various file type extensions."""
        file = File(
            filename=f"test.{file_type}",
            device="dev",
            path=f"/test.{file_type}",
            alias="user",
            size=1024,
            file_type=file_type
        )
        assert file.file_type == file_type
    
    def test_file_no_extension(self):
        """File without extension is valid."""
        file = File(
            filename="README",
            device="dev",
            path="/README",
            alias="user",
            size=1024,
            file_type=None
        )
        assert file.file_type is None
    
    def test_file_size_zero(self):
        """File with size=0 is valid."""
        file = File(
            filename="empty.txt",
            device="dev",
            path="/empty.txt",
            alias="user",
            size=0
        )
        assert file.size == 0
    
    def test_file_size_large(self):
        """File with large size is valid."""
        large_size = 10 * 1024 * 1024 * 1024
        file = File(
            filename="huge.iso",
            device="dev",
            path="/huge.iso",
            alias="user",
            size=large_size
        )
        assert file.size == large_size
    
    def test_file_very_long_filename(self):
        """File with very long filename is valid."""
        long_filename = "a" * 255 + ".txt"
        file = File(
            filename=long_filename,
            device="dev",
            path=f"/{long_filename}",
            alias="user",
            size=1024
        )
        assert file.filename == long_filename
    
    def test_file_special_characters_in_path(self):
        """File path with special characters is valid."""
        special_path = "/path/with-special_chars!@#$%/file.txt"
        file = File(
            filename="file.txt",
            device="dev",
            path=special_path,
            alias="user",
            size=1024
        )
        assert file.path == special_path
    
    def test_file_unicode_filename(self):
        """File with unicode characters in filename is valid."""
        unicode_filename = "文件_αρχείο_файл.txt"
        file = File(
            filename=unicode_filename,
            device="dev",
            path=f"/{unicode_filename}",
            alias="user",
            size=1024
        )
        assert file.filename == unicode_filename
