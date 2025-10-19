"""
Embedding generation module for distributed file transfer system.
Generates vector embeddings from file content or raw text using sentence-transformers.
NO API KEY REQUIRED - runs locally!
"""

import numpy as np
import os
from typing import Union
from pathlib import Path

# Sentence transformer model (lazy loaded)
_embedding_model = None


def get_embeddings_model():
    """
    Get or initialize the sentence transformer model.
    No API key needed - runs locally!
    """
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            # Use a small, fast model that runs locally
            _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("Loaded local sentence transformer model: all-MiniLM-L6-v2 (no API key needed)")
        except ImportError:
            raise ImportError(
                "sentence-transformers package is required. Install with: pip install sentence-transformers"
            )
    return _embedding_model

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
    Generate embedding vector from file content or text string.
    Uses local sentence transformer model - no API key needed!
    
    Args:
        input_data: Either a file path (str/Path) or text content (str)
        is_file: If True, treat input_data as file path. If False, treat as text.
                If None, auto-detect based on input type and file existence.
    
    Returns:
        numpy array of shape (384,) containing the embedding vector
    
    Example:
        # From file
        embedding = generate_embedding("document.txt", is_file=True)
        
        # From text
        embedding = generate_embedding("This is my text content", is_file=False)
        
        # Auto-detect
        embedding = generate_embedding(Path("document.txt"))
    """
    model = get_embeddings_model()
    
    # Auto-detect if is_file not specified
    if is_file is None:
        if isinstance(input_data, Path):
            is_file = True
        elif isinstance(input_data, str):
            # Check if it's a valid file path
            is_file = os.path.isfile(input_data)
        else:
            raise ValueError("input_data must be a string or Path object")
    
    # Read file content if needed
    if is_file:
        file_path = Path(input_data)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            # Try reading as text
            with open(file_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
        except UnicodeDecodeError:
            # If binary file, convert to string representation
            with open(file_path, 'rb') as f:
                # For binary files, use filename + size as content
                text_content = f"{file_path.name} (binary file, size: {file_path.stat().st_size} bytes)"
    else:
        text_content = str(input_data)
    
    if not text_content or not text_content.strip():
        raise ValueError("Cannot generate embedding from empty content")
    
    # Generate embedding using local model
    embedding = model.encode(text_content, convert_to_numpy=True)
    
    # Ensure it's a 1D numpy array of float32
    return embedding.astype(np.float32)
