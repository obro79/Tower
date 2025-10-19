"""
Vector database module for distributed file transfer system.
Handles vector embeddings storage and similarity search using FAISS.
Uses SQLite for metadata storage.
"""

import faiss
import numpy as np
import sqlite3
import pickle
import os
from typing import List, Tuple, Optional

# Vector database setup
VECTOR_DB_PATH = 'vectors.db'
FAISS_INDEX_PATH = 'faiss.index'
EMBEDDING_DIMENSION = 1536  # all-MiniLM-L6-v2 model dimension


def init_vector_db(db_path: str = VECTOR_DB_PATH, dimension: int = EMBEDDING_DIMENSION):
    """
    Initialize the vector database, creating the table if it doesn't exist.
    
    Args:
        db_path: Path to the SQLite database file
        dimension: Dimension of vector embeddings
    
    Returns:
        VectorDatabase instance
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table for vector embeddings
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vector_embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL UNIQUE,
            embedding BLOB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create index on file_id for faster lookups
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_file_id ON vector_embeddings(file_id)
    ''')
    
    conn.commit()
    conn.close()
    print(f"Vector database initialized at {db_path}")
    
    return VectorDatabase(db_path=db_path, dimension=dimension)


class VectorDatabase:
    """
    Vector database manager using FAISS for efficient similarity search
    and SQLite for metadata storage.
    """
    
    def __init__(self, db_path: str = VECTOR_DB_PATH, dimension: int = EMBEDDING_DIMENSION):
        """
        Initialize the vector database.
        
        Args:
            db_path: Path to SQLite database
            dimension: Dimension of the vector embeddings
        """
        self.db_path = db_path
        self.dimension = dimension
        self.index = None
        self.id_to_file_id = {}  # Maps FAISS index position to file_id
        self.file_id_to_index = {}  # Maps file_id to FAISS index position
        
        # Load or create FAISS index
        self._load_or_create_index()
    
    def _load_or_create_index(self):
        """Load existing FAISS index or create a new one."""
        if os.path.exists(FAISS_INDEX_PATH):
            try:
                self.index = faiss.read_index(FAISS_INDEX_PATH)
                self._load_mappings()
                print(f"Loaded FAISS index from {FAISS_INDEX_PATH} with {self.index.ntotal} vectors")
            except Exception as e:
                print(f"Error loading FAISS index: {e}")
                self._create_new_index()
        else:
            self._create_new_index()
    
    def _create_new_index(self):
        """Create a new FAISS index."""
        # Using L2 distance
        self.index = faiss.IndexFlatL2(self.dimension)
        print(f"Created new FAISS index with dimension {self.dimension}")
    
    def _load_mappings(self):
        """Load file_id mappings from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, file_id FROM vector_embeddings ORDER BY id')
        rows = cursor.fetchall()
        
        for idx, (db_id, file_id) in enumerate(rows):
            self.id_to_file_id[idx] = file_id
            self.file_id_to_index[file_id] = idx
        
        conn.close()
    
    def _save_index(self):
        """Save FAISS index to disk."""
        if self.index is not None:
            faiss.write_index(self.index, FAISS_INDEX_PATH)
    
    def insert(self, vector: np.ndarray, file_id: int) -> bool:
        """
        Insert a vector embedding for a file.
        
        Args:
            vector: Numpy array of shape (dimension,)
            file_id: ID of the file in the main database
        
        Returns:
            True if successful, False if file_id already exists
        
        Raises:
            ValueError: If vector dimension doesn't match
        """
        # Validate vector dimension
        if vector.shape[0] != self.dimension:
            raise ValueError(f"Vector dimension {vector.shape} doesn't match expected ({self.dimension},)")
        
        # Check if file_id already exists
        if file_id in self.file_id_to_index:
            print(f"Embedding for file_id {file_id} already exists.")
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Serialize vector
            vector_blob = pickle.dumps(vector)
            
            # Store in SQLite database
            cursor.execute(
                'INSERT INTO vector_embeddings (file_id, embedding) VALUES (?, ?)',
                (file_id, vector_blob)
            )
            conn.commit()
            
            # Add to FAISS index
            vector_reshaped = vector.reshape(1, -1).astype('float32')
            self.index.add(vector_reshaped)
            
            # Update mappings
            idx = self.index.ntotal - 1
            self.id_to_file_id[idx] = file_id
            self.file_id_to_index[file_id] = idx
            
            # Save index
            self._save_index()
            
            print(f"Inserted embedding for file_id {file_id} at index {idx}")
            return True
            
        except sqlite3.IntegrityError:
            print(f"Embedding for file_id {file_id} already exists in database.")
            return False
        except Exception as e:
            conn.rollback()
            print(f"Error inserting embedding: {e}")
            raise
        finally:
            conn.close()
    
    def get_file(self, vector: np.ndarray, k: int = 1) -> List[Tuple[int, float]]:
        """
        Find the k most similar files for a given query vector.
        
        Args:
            vector: Query vector as numpy array of shape (dimension,)
            k: Number of nearest neighbors to return
        
        Returns:
            List of tuples (file_id, distance) sorted by similarity
        
        Raises:
            ValueError: If vector dimension doesn't match
        """
        # Validate vector dimension
        if vector.shape[0] != self.dimension:
            raise ValueError(f"Vector dimension {vector.shape} doesn't match expected ({self.dimension},)")
        
        if self.index.ntotal == 0:
            print("No vectors in the index.")
            return []
        
        # Ensure k doesn't exceed total vectors
        k = min(k, self.index.ntotal)
        
        # Search FAISS index
        vector_reshaped = vector.reshape(1, -1).astype('float32')
        distances, indices = self.index.search(vector_reshaped, k)
        
        # Map indices to file_ids
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx in self.id_to_file_id:
                file_id = self.id_to_file_id[idx]
                results.append((file_id, float(distance)))
        
        return results
    
    def delete_embedding(self, file_id: int) -> bool:
        """
        Delete an embedding by file_id.
        Note: FAISS doesn't support deletion, so we rebuild the index.
        
        Args:
            file_id: ID of the file to remove
        
        Returns:
            True if successful, False if not found
        """
        if file_id not in self.file_id_to_index:
            print(f"No embedding found for file_id {file_id}")
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Remove from database
            cursor.execute('DELETE FROM vector_embeddings WHERE file_id = ?', (file_id,))
            conn.commit()
            
            # Rebuild FAISS index
            self._rebuild_index()
            
            print(f"Deleted embedding for file_id {file_id}")
            return True
            
        except Exception as e:
            conn.rollback()
            print(f"Error deleting embedding: {e}")
            raise
        finally:
            conn.close()
    
    def _rebuild_index(self):
        """Rebuild FAISS index from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Create new index
            self._create_new_index()
            self.id_to_file_id.clear()
            self.file_id_to_index.clear()
            
            # Load all embeddings
            cursor.execute('SELECT id, file_id, embedding FROM vector_embeddings ORDER BY id')
            rows = cursor.fetchall()
            
            if rows:
                vectors = []
                for idx, (db_id, file_id, embedding_blob) in enumerate(rows):
                    vector = pickle.loads(embedding_blob)
                    vectors.append(vector)
                    self.id_to_file_id[idx] = file_id
                    self.file_id_to_index[file_id] = idx
                
                # Add all vectors to index
                vectors_array = np.array(vectors).astype('float32')
                self.index.add(vectors_array)
                
                # Save index
                self._save_index()
                
                print(f"Rebuilt index with {len(rows)} vectors")
        finally:
            conn.close()
    
    def get_stats(self) -> dict:
        """
        Get statistics about the vector database.
        
        Returns:
            Dictionary with stats
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM vector_embeddings')
        db_count = cursor.fetchone()[0]
        conn.close()
        
        return {
            'total_vectors': self.index.ntotal if self.index else 0,
            'db_records': db_count,
            'dimension': self.dimension,
            'index_type': type(self.index).__name__ if self.index else None
        }
