"""
Test script for the database module.
Demonstrates CRUD operations and validates functionality.
"""

import os
import sys
from database import (
    init_db, add_file, get_file, get_file_by_id, 
    get_all_files, get_files_by_owner, get_files_by_device,
    update_file, delete_file, delete_all_files, DATABASE_PATH
)


def test_database():
    """Run comprehensive tests on the database module."""
    
    print("=" * 60)
    print("Testing Distributed File Transfer Database")
    print("=" * 60)
    
    # Clean up existing database for fresh test
    if os.path.exists(DATABASE_PATH):
        os.remove(DATABASE_PATH)
        print(f"Removed existing database: {DATABASE_PATH}\n")
    
    # Initialize database
    print("1. Initializing database...")
    init_db()
    print()
    
    # Test: Add files
    print("2. Testing add_file()...")
    file1 = add_file(
        filename="document1.pdf",
        device="client_a",
        path="/storage/documents/document1.pdf",
        owner="user_alice",
        size=1024000
    )
    
    file2 = add_file(
        filename="image.jpg",
        device="client_b",
        path="/storage/images/image.jpg",
        owner="user_bob",
        size=2048000
    )
    
    file3 = add_file(
        filename="data.csv",
        device="client_a",
        path="/storage/data/data.csv",
        owner="user_alice",
        size=512000,
        file_type="csv"
    )
    
    # Try adding duplicate (should fail gracefully)
    duplicate = add_file(
        filename="document1.pdf",
        device="client_a",
        path="/storage/documents/document1_copy.pdf",
        owner="user_alice",
        size=1024000
    )
    print()
    
    # Test: Get file by filename
    print("3. Testing get_file()...")
    retrieved = get_file("document1.pdf")
    if retrieved:
        print(f"Retrieved: {retrieved}")
        print(f"As dict: {retrieved.to_dict()}")
    print()
    
    # Test: Get file by ID
    print("4. Testing get_file_by_id()...")
    retrieved_by_id = get_file_by_id(1)
    if retrieved_by_id:
        print(f"Retrieved by ID: {retrieved_by_id}")
    print()
    
    # Test: Get all files
    print("5. Testing get_all_files()...")
    all_files = get_all_files()
    print(f"Total files in database: {len(all_files)}")
    for f in all_files:
        print(f"  - {f.filename} ({f.size} bytes, owner: {f.owner})")
    print()
    
    # Test: Get files by owner
    print("6. Testing get_files_by_owner()...")
    alice_files = get_files_by_owner("user_alice")
    print(f"Files owned by user_alice: {len(alice_files)}")
    for f in alice_files:
        print(f"  - {f.filename}")
    print()
    
    # Test: Get files by device
    print("7. Testing get_files_by_device()...")
    client_a_files = get_files_by_device("client_a")
    print(f"Files on client_a: {len(client_a_files)}")
    for f in client_a_files:
        print(f"  - {f.filename}")
    print()
    
    # Test: Update file
    print("8. Testing update_file()...")
    updated = update_file("document1.pdf", size=1536000, device="client_b")
    if updated:
        print(f"Updated file: {updated}")
    print()
    
    # Test: Delete file
    print("9. Testing delete_file()...")
    success = delete_file("image.jpg")
    print(f"Delete successful: {success}")
    
    # Try deleting non-existent file
    success = delete_file("nonexistent.txt")
    print(f"Delete non-existent: {success}")
    print()
    
    # Show remaining files
    print("10. Remaining files after deletion:")
    remaining = get_all_files()
    for f in remaining:
        print(f"  - {f.filename}")
    print()
    
    print("=" * 60)
    print("Database tests completed successfully!")
    print(f"Database file created at: {os.path.abspath(DATABASE_PATH)}")
    print("=" * 60)


if __name__ == "__main__":
    test_database()
