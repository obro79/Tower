"""
Test script for the embedding generation function.
Demonstrates usage with both files and raw text using Google's Gemini API.
"""

import os
import numpy as np
from embedding import generate_embedding
from dotenv import load_dotenv
load_dotenv()


def test_embedding():
    """Test the embedding generation function."""
    
    # Check if API key is set
    if not os.getenv('GOOGLE_API_KEY'):
        print("ERROR: GOOGLE_API_KEY environment variable not set!")
        print("Set it with: export GOOGLE_API_KEY='your-key-here'")
        print("Get your free key from: https://makersuite.google.com/app/apikey")
        return
    
    print("=" * 60)
    print("Testing Embedding Generation with Google Gemini API")
    print("=" * 60)
    print()
    
    # Test 1: Generate embedding from raw text
    print("1. Testing with raw text...")
    text1 = "This is a sample document about machine learning."
    embedding1 = generate_embedding(text1, is_file=False)
    print(f"Generated embedding: shape={embedding1.shape}, dtype={embedding1.dtype}")
    print()
    
    # Test 2: Generate embedding from the same text (should be identical)
    print("2. Testing with identical text...")
    text2 = "This is a sample document about machine learning."
    embedding2 = generate_embedding(text2, is_file=False)
    
    # Check if embeddings are the same
    are_same = np.allclose(embedding1, embedding2)
    print(f"Embeddings are identical: {are_same}")
    print(f"Distance between embeddings: {np.linalg.norm(embedding1 - embedding2):.10f}")
    print()
    
    # Test 3: Generate embedding from different text
    print("3. Testing with different text...")
    text3 = "A completely different topic about cooking recipes."
    embedding3 = generate_embedding(text3, is_file=False)
    
    distance_similar = np.linalg.norm(embedding1 - embedding2)
    distance_different = np.linalg.norm(embedding1 - embedding3)
    print(f"Distance between same texts: {distance_similar:.6f}")
    print(f"Distance between different texts: {distance_different:.6f}")
    print()
    
    # Test 4: Create a test file and generate embedding from it
    print("4. Testing with file...")
    test_file = "test_content.txt"
    test_content = "This is a sample document about machine learning."
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    embedding4 = generate_embedding(test_file, is_file=True)
    
    # Check if file embedding matches text embedding
    file_matches_text = np.allclose(embedding1, embedding4)
    print(f"File embedding matches text embedding: {file_matches_text}")
    print(f"Distance: {np.linalg.norm(embedding1 - embedding4):.10f}")
    
    # Clean up
    os.remove(test_file)
    print()
    
    # Test 5: Auto-detect mode
    print("5. Testing auto-detect mode...")
    
    # Create test file
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("Auto-detect test content")
    
    # Should detect as file
    embedding5 = generate_embedding(test_file)  # Auto-detect
    print(f"Auto-detected as file: shape={embedding5.shape}")
    
    # Should detect as text
    embedding6 = generate_embedding("This is obviously text, not a file path")
    print(f"Auto-detected as text: shape={embedding6.shape}")
    
    # Clean up
    os.remove(test_file)
    print()
    
    print("=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    test_embedding()
