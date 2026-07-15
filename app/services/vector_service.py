import math
import json
import time
from typing import List, Optional
from langchain_core.embeddings import Embeddings
from langchain_ollama import OllamaEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.logger import logger

_ollama_available = True

class DynamicFallbackEmbeddings(Embeddings):
    """
    Attempts Ollama embeddings first; falls back to Google GenAI embeddings
    using the user's API key if Ollama is unavailable.
    """
    def __init__(self, google_api_key: Optional[str] = None):
        self.google_api_key = google_api_key
        self.ollama_model = "nomic-embed-text-v2-moe:latest"
        self.google_model = "models/text-embedding-004"

    def _get_ollama(self) -> OllamaEmbeddings:
        return OllamaEmbeddings(model=self.ollama_model)

    def _get_google(self) -> GoogleGenerativeAIEmbeddings:
        if not self.google_api_key:
            raise ValueError("Google API key is missing. Cannot initialize GoogleGenerativeAIEmbeddings fallback.")
        return GoogleGenerativeAIEmbeddings(
            model=self.google_model,
            google_api_key=self.google_api_key
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        global _ollama_available
        if _ollama_available:
            try:
                # Attempt Ollama
                embedder = self._get_ollama()
                return embedder.embed_documents(texts)
            except Exception as e:
                logger.log_error(f"Ollama document embedding failed ({str(e)}). Falling back to Google GenAI...")
                _ollama_available = False
                
        try:
            embedder = self._get_google()
            return embedder.embed_documents(texts)
        except Exception as e_inner:
            logger.log_error(f"Fallback Google GenAI embedding also failed: {str(e_inner)}")
            raise e_inner

    def embed_query(self, text: str) -> List[float]:
        global _ollama_available
        if _ollama_available:
            try:
                # Attempt Ollama
                embedder = self._get_ollama()
                return embedder.embed_query(text)
            except Exception as e:
                logger.log_error(f"Ollama query embedding failed ({str(e)}). Falling back to Google GenAI...")
                _ollama_available = False
                
        try:
            embedder = self._get_google()
            return embedder.embed_query(text)
        except Exception as e_inner:
            logger.log_error(f"Fallback Google GenAI embedding also failed: {str(e_inner)}")
            raise e_inner

def get_embeddings_model(google_api_key: Optional[str] = None) -> Embeddings:
    """Returns the unified dynamic fallback embedding model."""
    return DynamicFallbackEmbeddings(google_api_key=google_api_key)

def calculate_cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculates the standard mathematical cosine similarity coefficient between two vector dimensions."""
    dot_product = sum(a * b for a, b in zip(v1, v2))
    mag1 = math.sqrt(sum(a * a for a in v1))
    mag2 = math.sqrt(sum(b * b for b in v2))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot_product / (mag1 * mag2)

def semantic_search_logs(query: str, logs_with_vectors: List[dict], top_k: int = 3, google_api_key: Optional[str] = None) -> str:
    """
    Performs standard, lightweight vector comparisons against all historical logs.
    Utilizes DynamicFallbackEmbeddings to obtain query representations.
    """
    logger.log_process_start("Semantic Vector Search", f"Searching past memories for: '{query}'")
    start_time = time.time()
    
    try:
        embedder = get_embeddings_model(google_api_key=google_api_key)
        query_vector = embedder.embed_query(query)
        
        scored_logs = []
        for log in logs_with_vectors:
            if not log.get('vector'):
                continue
            similarity = calculate_cosine_similarity(query_vector, log['vector'])
            scored_logs.append((similarity, log))
            
        # Sort descending (most relevant first)
        scored_logs.sort(key=lambda x: x[0], reverse=True)
        top_logs = scored_logs[:top_k]
        
        context_str = ""
        logger.log_info("--- Top Semantic Memory Results ---")
        for idx, (score, log) in enumerate(top_logs):
            logger.log_info(f"Memory {idx+1} [Score: {score:.3f}]: {log['title']}")
            if score > 0.65:  # Similarity threshold to filter out irrelevant history
                context_str += f"- Past Session '{log['title']}': {log['text']}\n"
                
        logger.log_process_end("Semantic Vector Search", time.time() - start_time)
        return context_str if context_str else "No highly relevant past memories found."
    except Exception as e:
        logger.log_error(f"Semantic Search Failed: {str(e)}")
        return "Memory retrieval unavailable."
