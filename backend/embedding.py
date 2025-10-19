"""
Embedding generation module for distributed file transfer system.
Generates vector embeddings from file content or raw text using OpenAI API.
"""

import numpy as np
import os
from typing import Union
from pathlib import Path
from openai import OpenAI

_openai_client = None

def get_openai_client():
    """
    Get or initialize the OpenAI client.
    Requires OPENAI_API_KEY environment variable to be set.
    """
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable not set. "
                "Set it with: export OPENAI_API_KEY='your-key-here'"
            )
        _openai_client = OpenAI(api_key=api_key)
        print("OpenAI client initialized successfully")
    return _openai_client


def generate_embedding(input_data: Union[str, Path], is_file: bool = None) -> np.ndarray:
    """
    Generate embedding vector from file content or text string using OpenAI API.
    
    Args:
        input_data: Either a file path (str/Path) or text content (str)
        is_file: If True, treat input_data as file path. If False, treat as text.
                If None, auto-detect based on input type and file existence.
    
    Returns:
        numpy array of shape (1536,) containing the embedding vector
    
    Example:
        embedding = generate_embedding("document.txt", is_file=True)
        embedding = generate_embedding("This is my text content", is_file=False)
        embedding = generate_embedding(Path("document.txt"))
    """
    client = get_openai_client()
    
    if is_file is None:
        if isinstance(input_data, Path):
            is_file = True
        elif isinstance(input_data, str):
            is_file = os.path.isfile(input_data)
        else:
            raise ValueError("input_data must be a string or Path object")
    
    if is_file:
        file_path = Path(input_data)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
        except UnicodeDecodeError:
            with open(file_path, 'rb') as f:
                text_content = f"{file_path.name} (binary file, size: {file_path.stat().st_size} bytes)"
    else:
        text_content = str(input_data)
    
    if not text_content or not text_content.strip():
        raise ValueError("Cannot generate embedding from empty content")
    
    response = client.embeddings.create(
        model='text-embedding-3-small',
        input=text_content,
        encoding_format='float'
    )
    
    embedding = np.array(response.data[0].embedding, dtype=np.float32)
    
    if embedding.shape[0] != 1536:
        raise ValueError(f"Expected 1536 dimensions, got {embedding.shape[0]}")
    
    return embedding
