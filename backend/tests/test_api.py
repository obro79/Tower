import pytest
from datetime import datetime

from models import File
from database import add_file


pytestmark = pytest.mark.integration


class TestHealthCheck:
    """Test health check endpoint."""
    
    def test_get_root_returns_status(self, test_client):
        """GET / returns 200 with status."""
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "File Sync API is running"


class TestSearchFiles:
    """Test GET /files/search endpoint."""
    
    def test_search_files_success(self, test_client, populated_db):
        """Search returns matching files."""
        response = test_client.get("/files/search?query=report")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
    
    def test_search_files_wildcard_prefix(self, test_client):
        """Search with prefix wildcard matches correctly."""
        add_file("test_doc.pdf", "dev", "/test_doc.pdf", "user", 1000, "pdf")
        add_file("test_image.jpg", "dev", "/test_image.jpg", "user", 2000, "jpg")
        
        response = test_client.get("/files/search?query=test*")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
    
    def test_search_files_wildcard_suffix(self, test_client):
        """Search with suffix wildcard matches correctly."""
        add_file("document.pdf", "dev", "/document.pdf", "user", 1000, "pdf")
        add_file("report.pdf", "dev", "/report.pdf", "user", 2000, "pdf")
        add_file("image.jpg", "dev", "/image.jpg", "user", 3000, "jpg")
        
        response = test_client.get("/files/search?query=*.pdf")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(f["filename"].endswith(".pdf") for f in data)
    
    def test_search_files_wildcard_middle(self, test_client):
        """Search with middle wildcard matches correctly."""
        add_file("q1_report.pdf", "dev", "/q1_report.pdf", "user", 1000)
        add_file("q2_report.xlsx", "dev", "/q2_report.xlsx", "user", 2000)
        add_file("q3_summary.pdf", "dev", "/q3_summary.pdf", "user", 3000)
        
        response = test_client.get("/files/search?query=*report*")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all("report" in f["filename"] for f in data)
    
    def test_search_files_no_results_404(self, test_client):
        """No matches returns 404."""
        response = test_client.get("/files/search?query=nonexistent_pattern_xyz")
        assert response.status_code == 404
        data = response.json()
        assert "No files found" in data["detail"]
    
    def test_search_files_case_insensitive(self, test_client):
        """Search is case-insensitive."""
        add_file("MyDocument.PDF", "dev", "/MyDocument.PDF", "user", 1000)
        
        response_lower = test_client.get("/files/search?query=mydocument")
        response_upper = test_client.get("/files/search?query=MYDOCUMENT")
        response_mixed = test_client.get("/files/search?query=MyDoC*")
        
        assert response_lower.status_code == 200
        assert response_upper.status_code == 200
        assert response_mixed.status_code == 200
    
    def test_search_files_response_model(self, test_client):
        """Response matches File schema."""
        add_file("test.txt", "laptop", "/test.txt", "alice", 1024, "txt")
        
        response = test_client.get("/files/search?query=test")
        assert response.status_code == 200
        data = response.json()
        
        file_data = data[0]
        assert "id" in file_data
        assert "filename" in file_data
        assert "device" in file_data
        assert "path" in file_data
        assert "alias" in file_data
        assert "size" in file_data
        assert "uploaded_at" in file_data


class TestGetFileMetadata:
    """Test GET /files/{file_id} endpoint."""
    
    def test_get_file_metadata_success(self, test_client):
        """Returns correct file by ID."""
        file = add_file("test.pdf", "laptop", "/test.pdf", "user", 1024)
        
        response = test_client.get(f"/files/{file.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test.pdf"
        assert data["device"] == "laptop"
    
    def test_get_file_metadata_not_found_404(self, test_client):
        """Invalid ID returns 404."""
        response = test_client.get("/files/99999")
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]
    
    def test_get_file_metadata_response_model(self, test_client):
        """Response matches File schema."""
        file = add_file("test.txt", "dev", "/test.txt", "user", 1024)
        
        response = test_client.get(f"/files/{file.id}")
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert "filename" in data
        assert "device" in data
        assert "path" in data
        assert "alias" in data
        assert "size" in data
        assert "file_type" in data
        assert "uploaded_at" in data
    
    def test_get_file_metadata_contains_all_fields(self, test_client):
        """All File fields present in response."""
        file = add_file(
            "complete.pdf",
            "laptop",
            "/docs/complete.pdf",
            "alice",
            2048000,
            "pdf"
        )
        
        response = test_client.get(f"/files/{file.id}")
        data = response.json()
        
        assert data["filename"] == "complete.pdf"
        assert data["device"] == "laptop"
        assert data["path"] == "/docs/complete.pdf"
        assert data["alias"] == "alice"
        assert data["size"] == 2048000
        assert data["file_type"] == "pdf"


class TestRegisterFile:
    """Test POST /files/register endpoint."""
    
    def test_register_file_create_success(self, test_client):
        """File created with success response."""
        payload = {
            "filename": "new_file.txt",
            "path": "/documents/new_file.txt",
            "device": "laptop_1",
            "alias": "alice",
            "size": 1024,
            "file_type": "txt"
        }
        response = test_client.post("/files/register", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "File metadata registered successfully"
    
    def test_register_file_with_all_fields(self, test_client):
        """All fields stored correctly."""
        payload = {
            "filename": "complete_file.pdf",
            "path": "/storage/complete_file.pdf",
            "device": "server",
            "alias": "bob",
            "size": 5000000,
            "file_type": "pdf"
        }
        response = test_client.post("/files/register", json=payload)
        assert response.status_code == 200
        
        file_id = response.json()["file_id"]
        
        get_response = test_client.get(f"/files/{file_id}")
        file_data = get_response.json()
        
        assert file_data["filename"] == "complete_file.pdf"
        assert file_data["path"] == "/storage/complete_file.pdf"
        assert file_data["device"] == "server"
        assert file_data["alias"] == "bob"
        assert file_data["size"] == 5000000
        assert file_data["file_type"] == "pdf"
    
    def test_register_file_duplicate_updates(self, test_client):
        """Duplicate (same path + device) updates record."""
        payload1 = {
            "filename": "file_v1.txt",
            "path": "/docs/myfile.txt",
            "device": "laptop",
            "alias": "alice",
            "size": 1000,
            "file_type": "txt"
        }
        
        response1 = test_client.post("/files/register", json=payload1)
        assert response1.json()["action"] == "created"
        file_id = response1.json()["file_id"]
        
        payload2 = {
            "filename": "file_v2.txt",
            "path": "/docs/myfile.txt",
            "device": "laptop",
            "alias": "alice",
            "size": 2000,
            "file_type": "txt"
        }
        
        response2 = test_client.post("/files/register", json=payload2)
        assert response2.json()["action"] == "updated"
        assert response2.json()["file_id"] == file_id
    
    def test_register_file_modified_at_updated_on_duplicate(self, test_client):
        """modified_at updated on duplicate registration."""
        payload1 = {
            "filename": "file.txt",
            "path": "/file.txt",
            "device": "dev",
            "alias": "user",
            "size": 100,
            "file_type": "txt"
        }
        
        response1 = test_client.post("/files/register", json=payload1)
        get_response1 = test_client.get(f"/files/{response1.json()['file_id']}")
        first_modified = get_response1.json()["modified_at"]
        
        import time
        time.sleep(0.1)
        
        response2 = test_client.post("/files/register", json=payload1)
        get_response2 = test_client.get(f"/files/{response2.json()['file_id']}")
        second_modified = get_response2.json()["modified_at"]
        
        assert second_modified > first_modified
    
    def test_register_file_returns_file_id(self, test_client):
        """Response includes file_id."""
        payload = {
            "filename": "test.txt",
            "path": "/test.txt",
            "device": "dev",
            "alias": "user",
            "size": 100,
            "file_type": "txt"
        }
        response = test_client.post("/files/register", json=payload)
        data = response.json()
        
        assert "file_id" in data
        assert isinstance(data["file_id"], int)
    
    def test_register_file_returns_action_field(self, test_client):
        """Response includes action field (created/updated)."""
        payload = {
            "filename": "test.txt",
            "path": "/test.txt",
            "device": "dev",
            "alias": "user",
            "size": 100,
            "file_type": "txt"
        }
        response = test_client.post("/files/register", json=payload)
        data = response.json()
        
        assert "action" in data
        assert data["action"] in ["created", "updated"]
    
    def test_register_file_invalid_request_400(self, test_client):
        """Missing fields returns 400."""
        payload = {
            "filename": "test.txt"
        }
        response = test_client.post("/files/register", json=payload)
        assert response.status_code in [400, 422]
    
    def test_register_file_response_contains_metadata(self, test_client):
        """Response includes metadata fields."""
        payload = {
            "filename": "test.txt",
            "path": "/test.txt",
            "device": "dev",
            "alias": "user",
            "size": 100,
            "file_type": "txt"
        }
        response = test_client.post("/files/register", json=payload)
        data = response.json()
        
        assert "message" in data
        assert "file_id" in data
        assert "filename" in data
        assert "action" in data


class TestDeleteFileMetadata:
    """Test DELETE /files/{file_id} endpoint."""
    
    def test_delete_file_metadata_success(self, test_client):
        """File deleted returns 200."""
        file = add_file("delete_me.txt", "dev", "/delete_me.txt", "user", 100)
        
        response = test_client.delete(f"/files/{file.id}")
        assert response.status_code == 200
    
    def test_delete_file_metadata_not_found_404(self, test_client):
        """Invalid ID returns 404."""
        response = test_client.delete("/files/99999")
        assert response.status_code == 404
    
    def test_delete_file_metadata_removes_from_db(self, test_client):
        """File actually removed from database."""
        file = add_file("delete_me.txt", "dev", "/delete_me.txt", "user", 100)
        file_id = file.id
        
        test_client.delete(f"/files/{file_id}")
        
        get_response = test_client.get(f"/files/{file_id}")
        assert get_response.status_code == 404
    
    def test_delete_file_metadata_response_message(self, test_client):
        """Response has success message."""
        file = add_file("delete_me.txt", "dev", "/delete_me.txt", "user", 100)
        
        response = test_client.delete(f"/files/{file.id}")
        data = response.json()
        
        assert "message" in data
        assert "deleted" in data["message"].lower()
        assert "file_id" in data
        assert "filename" in data
        assert "device" in data


class TestEndpointIntegration:
    """Test full workflows across multiple endpoints."""
    
    def test_register_then_search_then_get(self, test_client):
        """Full workflow: register → search → get."""
        payload = {
            "filename": "workflow_test.pdf",
            "path": "/workflow_test.pdf",
            "device": "laptop",
            "alias": "alice",
            "size": 1024000,
            "file_type": "pdf"
        }
        
        register_response = test_client.post("/files/register", json=payload)
        file_id = register_response.json()["file_id"]
        
        search_response = test_client.get("/files/search?query=workflow_test")
        assert search_response.status_code == 200
        search_data = search_response.json()
        assert len(search_data) > 0
        
        get_response = test_client.get(f"/files/{file_id}")
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["filename"] == "workflow_test.pdf"
    
    def test_register_then_update_then_verify(self, test_client):
        """Full workflow: register → update → verify."""
        payload1 = {
            "filename": "v1.txt",
            "path": "/myfile.txt",
            "device": "laptop",
            "alias": "alice",
            "size": 1000,
            "file_type": "txt"
        }
        
        response1 = test_client.post("/files/register", json=payload1)
        file_id = response1.json()["file_id"]
        
        payload2 = {
            "filename": "v2.txt",
            "path": "/myfile.txt",
            "device": "laptop",
            "alias": "alice",
            "size": 2000,
            "file_type": "txt"
        }
        
        test_client.post("/files/register", json=payload2)
        
        get_response = test_client.get(f"/files/{file_id}")
        data = get_response.json()
        assert data["size"] == 2000
    
    def test_register_multiple_then_delete(self, test_client):
        """Multiple files: register → verify count → delete."""
        for i in range(3):
            payload = {
                "filename": f"file_{i}.txt",
                "path": f"/file_{i}.txt",
                "device": f"dev_{i}",
                "alias": "alice",
                "size": 1000 * (i + 1),
                "file_type": "txt"
            }
            test_client.post("/files/register", json=payload)
        
        search_response = test_client.get("/files/search?query=file_*")
        initial_count = len(search_response.json())
        assert initial_count == 3
        
        all_response = test_client.get("/files/search?query=*")
        all_files = all_response.json()
        first_file_id = all_files[0]["id"]
        
        test_client.delete(f"/files/{first_file_id}")
        
        search_after = test_client.get("/files/search?query=file_*")
        assert len(search_after.json()) == 2
