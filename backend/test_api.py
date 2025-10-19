#!/usr/bin/env python3
"""
Test script for the Unified Server with Colinear Query Expansion
"""

import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")

def test_health_check():
    print_section("1. Health Check")
    response = requests.get(f"{BASE_URL}/")
    print(json.dumps(response.json(), indent=2))

def test_upload_file():
    print_section("2. Upload Test File with Embedding")
    
    # Create a test file
    test_content = """
    Machine Learning Tutorial
    
    This document covers the basics of machine learning, including:
    - Supervised learning algorithms
    - Neural networks and deep learning
    - Data preprocessing techniques
    - Model evaluation metrics
    """
    
    test_file = Path("/tmp/ml_tutorial.txt")
    test_file.write_text(test_content)
    
    # Upload the file
    with open(test_file, 'rb') as f:
        files = {'file': ('ml_tutorial.txt', f, 'text/plain')}
        params = {
            'device': 'laptop',
            'device_ip': '192.168.1.100',
            'device_user': 'testuser',
            'absolute_path': '/home/testuser/docs/ml_tutorial.txt'
        }
        response = requests.post(f"{BASE_URL}/files/upload", files=files, params=params)
    
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    
    # Upload another file
    test_content2 = """
    Python Programming Guide
    
    Learn Python programming from scratch:
    - Variables and data types
    - Functions and classes
    - File I/O operations
    - Error handling
    """
    
    test_file2 = Path("/tmp/python_guide.txt")
    test_file2.write_text(test_content2)
    
    with open(test_file2, 'rb') as f:
        files = {'file': ('python_guide.txt', f, 'text/plain')}
        params = {
            'device': 'desktop',
            'device_ip': '192.168.1.101',
            'device_user': 'testuser',
            'absolute_path': '/home/testuser/docs/python_guide.txt'
        }
        response = requests.post(f"{BASE_URL}/files/upload", files=files, params=params)
    
    print(f"\nSecond file - Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_semantic_search_without_expansion():
    print_section("3. Semantic Search WITHOUT Query Expansion")
    
    query_data = {
        "query": "learning tutorial",
        "top_k": 5,
        "use_query_expansion": False
    }
    
    response = requests.post(f"{BASE_URL}/search/semantic", json=query_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        results = response.json()
        print(f"Found {len(results)} results:\n")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['filename']}")
            print(f"   Similarity: {result['similarity_score']:.4f}")
            print(f"   Matched via: {result['matched_via']}")
            print(f"   Device: {result['device']} ({result['device_ip']})")
            print()
    else:
        print(response.text)

def test_semantic_search_with_expansion():
    print_section("4. Semantic Search WITH Query Expansion (Colinear)")
    
    query_data = {
        "query": "learning tutorial",
        "top_k": 5,
        "use_query_expansion": True,
        "expansion_count": 3
    }
    
    print("Query: 'learning tutorial'")
    print("Expansion enabled: True")
    print("Expansion count: 3")
    print("\nExpected query variants:")
    print("  0. learning tutorial (original)")
    print("  1. document about learning tutorial")
    print("  2. file containing learning tutorial")
    print("  3. information regarding learning tutorial")
    print("\n" + "-"*70 + "\n")
    
    response = requests.post(f"{BASE_URL}/search/semantic", json=query_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        results = response.json()
        print(f"Found {len(results)} results:\n")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['filename']}")
            print(f"   Similarity: {result['similarity_score']:.4f}")
            print(f"   Matched via: {result['matched_via']} ⭐")
            print(f"   Device: {result['device']} ({result['device_ip']})")
            print(f"   Path: {result['path']}")
            print()
    else:
        print(response.text)

def test_keyword_search():
    print_section("5. Traditional Keyword Search")
    
    response = requests.get(f"{BASE_URL}/search/keyword?query=*.txt")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        results = response.json()
        print(f"Found {len(results)} .txt files:\n")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['file_name']}")
            print(f"   Device: {result['device']}")
            print()
    else:
        print(response.text)

def test_stats():
    print_section("6. System Statistics")
    
    response = requests.get(f"{BASE_URL}/stats")
    print(json.dumps(response.json(), indent=2))

def main():
    print("\n" + "🚀 " * 25)
    print("  Testing Unified Server with Colinear Query Expansion")
    print("🚀 " * 25)
    
    try:
        test_health_check()
        test_upload_file()
        test_semantic_search_without_expansion()
        test_semantic_search_with_expansion()
        test_keyword_search()
        test_stats()
        
        print_section("✅ All Tests Complete!")
        print("Key Observations:")
        print("- Semantic search WITH expansion may return more/better results")
        print("- 'matched_via' shows which query variant found the match")
        print("- Similarity scores range from 0-1 (higher = better)")
        print("- Query expansion helps find relevant files with different wording")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to server at", BASE_URL)
        print("Make sure the server is running: python unified_server.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
