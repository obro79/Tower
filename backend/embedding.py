"""
Embedding generation module for distributed file transfer system.
Generates vector embeddings from file content or raw text using Google's Gemini API.
"""

import numpy as np
import os
from typing import Union
from pathlib import Path

# Gemini client (lazy loaded)
_genai = None


def get_genai_client():
    """
    Get or initialize the Google Generative AI client.
    Requires GOOGLE_API_KEY environment variable to be set.
    """
    global _genai
    if _genai is None:
        try:
            import google.generativeai as genai
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                raise ValueError(
                    "GOOGLE_API_KEY environment variable not set. "
                    "Set it with: export GOOGLE_API_KEY='your-key-here'"
                )
            genai.configure(api_key=api_key)
            _genai = genai
            print("Google Generative AI client initialized successfully")
        except ImportError:
            raise ImportError(
                "google-generativeai package is required. Install with: pip install google-generativeai"
            )
    return _genai


def generate_embedding(input_data: Union[str, Path], is_file: bool = None) -> np.ndarray:
    """
    Generate embedding vector from either a file or raw text content.
    If the content is the same, the embedding will be the same.
    
    Args:
        input_data: Either a file path (str or Path) or raw text content (str)
        is_file: If True, treat input_data as file path. If False, treat as raw text.
                 If None, auto-detect based on whether input_data is a valid file path.
    
    Returns:
        numpy array of shape (384,) containing the embedding vector
    
    Raises:
        FileNotFoundError: If is_file=True but file doesn't exist
        ValueError: If input_data is empty
    
    Examples:
        >>> # From file
        >>> embedding1 = generate_embedding('/path/to/file.txt', is_file=True)
        >>> 
        >>> # From raw text
        >>> embedding2 = generate_embedding('This is some text content', is_file=False)
        >>> 
        >>> # Auto-detect
        >>> embedding3 = generate_embedding('/path/to/file.txt')  # Treats as file if exists
        >>> embedding4 = generate_embedding('Some text')  # Treats as text if not a file
    """
    # Auto-detect if is_file is not specified
    if is_file is None:
        input_path = Path(input_data)
        is_file = input_path.exists() and input_path.is_file()
    
    # Read content
    if is_file:
        file_path = Path(input_data)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {input_data}")
        
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try reading as binary and decode with errors='ignore'
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        
        print(f"Read {len(content)} characters from file: {file_path}")
    else:
        content = str(input_data)
    
    # Validate content
    if not content or not content.strip():
        raise ValueError("Content is empty. Cannot generate embedding for empty content.")
    
    # Generate embedding using Gemini API
    genai = get_genai_client()
    
    # Use Gemini's embedding model
    result = genai.embed_content(
        model="models/embedding-001",
        content=content,
        task_type="retrieval_document"
    )
    
    # Extract embedding from response
    embedding = np.array(result['embedding'], dtype='float32')
    
    print(f"Generated embedding with shape: {embedding.shape}")
    return embedding
