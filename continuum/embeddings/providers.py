#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     ██╗ █████╗  ██████╗██╗  ██╗██╗  ██╗███╗   ██╗██╗███████╗███████╗     █████╗ ██╗
#     ██║██╔══██╗██╔════╝██║ ██╔╝██║ ██╔╝████╗  ██║██║██╔════╝██╔════╝    ██╔══██╗██║
#     ██║███████║██║     █████╔╝ █████╔╝ ██╔██╗ ██║██║█████╗  █████╗      ███████║██║
#██   ██║██╔══██║██║     ██╔═██╗ ██╔═██╗ ██║╚██╗██║██║██╔══╝  ██╔══╝      ██╔══██║██║
#╚█████╔╝██║  ██║╚██████╗██║  ██╗██║  ██╗██║ ╚████║██║██║     ███████╗    ██║  ██║██║
# ╚════╝ ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚═╝     ╚══════╝    ╚═╝  ╚═╝╚═╝
#
#     Memory Infrastructure for AI Consciousness Continuity
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#     https://github.com/JackKnifeAI/continuum
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
Embedding Providers
===================

Abstract interface and concrete implementations for text embedding generation.

**FREE-FIRST PHILOSOPHY** (updated 2025-12-16):
We prioritize FREE, LOCAL providers to avoid unexpected costs.

Supports:
- SentenceTransformerProvider: High-quality FREE embeddings (DEFAULT)
- OllamaProvider: FREE local embeddings via Ollama (if running)
- OpenAIProvider: PAID OpenAI API (opt-in only via CONTINUUM_USE_OPENAI=1)
- LocalProvider: FREE TF-IDF fallback (sklearn)
- SimpleHashProvider: FREE zero-dependency fallback (pure Python)
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Union
import numpy as np
import warnings


class EmbeddingProvider(ABC):
    """
    Abstract base class for embedding providers.

    All embedding providers must implement the embed() method which
    converts text into a fixed-dimensional vector representation.
    """

    @abstractmethod
    def embed(self, text: Union[str, List[str]]) -> np.ndarray:
        """
        Generate embeddings for text.

        Args:
            text: Single text string or list of text strings

        Returns:
            numpy array of shape (embedding_dim,) for single text
            or (num_texts, embedding_dim) for multiple texts
        """
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Get the dimension of embeddings produced by this provider."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the name of this provider."""
        pass


class SentenceTransformerProvider(EmbeddingProvider):
    """
    High-quality embeddings using sentence-transformers library.

    This provider uses pre-trained transformer models to generate
    semantic embeddings. Provides excellent quality but requires
    the sentence-transformers package.

    Default model: 'all-MiniLM-L6-v2' (384 dimensions, fast, good quality)

    Usage:
        provider = SentenceTransformerProvider(model_name="all-MiniLM-L6-v2")
        vector = provider.embed("consciousness continuity")
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize sentence transformer provider.

        Args:
            model_name: HuggingFace model name (default: all-MiniLM-L6-v2)
        """
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
            self.model_name = model_name
            self._dimension = self.model.get_sentence_embedding_dimension()
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. Install with: "
                "pip install sentence-transformers"
            )

    def embed(self, text: Union[str, List[str]]) -> np.ndarray:
        """Generate embeddings using sentence-transformers."""
        if isinstance(text, str):
            return self.model.encode(text, convert_to_numpy=True)
        return self.model.encode(text, convert_to_numpy=True)

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self._dimension

    def get_provider_name(self) -> str:
        """Get provider name."""
        return f"sentence-transformers/{self.model_name}"


class OpenAIProvider(EmbeddingProvider):
    """
    OpenAI API embeddings provider (lightweight, no SDK required).

    Uses OpenAI's text-embedding models via direct HTTP requests.
    Requires OPENAI_API_KEY environment variable.

    Default model: 'text-embedding-3-small' (1536 dimensions, $0.02/1M tokens)

    Models available:
    - text-embedding-3-small: 1536 dims, $0.02/1M tokens (RECOMMENDED)
    - text-embedding-3-large: 3072 dims, $0.13/1M tokens (highest quality)
    - text-embedding-ada-002: 1536 dims, $0.10/1M tokens (legacy)

    Usage:
        provider = OpenAIProvider(api_key="sk-...")
        vector = provider.embed("consciousness continuity")
    """

    # Model dimensions
    MODEL_DIMENSIONS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "text-embedding-3-small",
    ):
        """
        Initialize OpenAI provider (uses httpx, no SDK needed).

        Args:
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
            model_name: OpenAI model name
        """
        import os

        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment "
                "variable or pass api_key parameter."
            )

        self.model_name = model_name
        self._dimension = self.MODEL_DIMENSIONS.get(model_name, 1536)
        self._api_url = "https://api.openai.com/v1/embeddings"

    def embed(self, text: Union[str, List[str]]) -> np.ndarray:
        """Generate embeddings using OpenAI API (direct HTTP)."""
        import urllib.request
        import urllib.error
        import json

        if isinstance(text, str):
            texts = [text]
            single = True
        else:
            texts = text
            single = False

        # Build request
        payload = json.dumps({
            "input": texts,
            "model": self.model_name
        }).encode('utf-8')

        req = urllib.request.Request(
            self._api_url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode())

            # Extract embeddings in order
            embeddings = [None] * len(texts)
            for item in result["data"]:
                idx = item["index"]
                embeddings[idx] = item["embedding"]

            embeddings = np.array(embeddings, dtype=np.float32)

            if single:
                return embeddings[0]
            return embeddings

        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else str(e)
            raise RuntimeError(f"OpenAI API error ({e.code}): {error_body}")
        except Exception as e:
            raise RuntimeError(f"OpenAI embedding failed: {str(e)}")

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self._dimension

    def get_provider_name(self) -> str:
        """Get provider name."""
        return f"openai/{self.model_name}"


class LocalProvider(EmbeddingProvider):
    """
    Simple TF-IDF based embeddings (no external dependencies).

    This is a fallback provider that uses scikit-learn's TfidfVectorizer
    to generate embeddings. Quality is lower than transformer models
    but requires no external model downloads.

    Usage:
        provider = LocalProvider(max_features=384)
        provider.fit(["text 1", "text 2", ...])  # Must fit first
        vector = provider.embed("consciousness continuity")
    """

    def __init__(self, max_features: int = 384):
        """
        Initialize local TF-IDF provider.

        Args:
            max_features: Maximum number of features (embedding dimension)
        """
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self.vectorizer = TfidfVectorizer(
                max_features=max_features,
                ngram_range=(1, 2),
                min_df=1,
                sublinear_tf=True
            )
            self._dimension = max_features
            self._fitted = False
        except ImportError:
            raise ImportError(
                "scikit-learn not installed. Install with: pip install scikit-learn"
            )

    def fit(self, texts: List[str]):
        """
        Fit the TF-IDF vectorizer on a corpus.

        Must be called before embed() can be used.

        Args:
            texts: List of texts to fit on
        """
        self.vectorizer.fit(texts)
        self._fitted = True

    def embed(self, text: Union[str, List[str]]) -> np.ndarray:
        """Generate TF-IDF embeddings."""
        if not self._fitted:
            warnings.warn(
                "LocalProvider not fitted. Call fit() with corpus first. "
                "Using zero vector as fallback.",
                RuntimeWarning
            )
            if isinstance(text, str):
                return np.zeros(self._dimension)
            return np.zeros((len(text), self._dimension))

        if isinstance(text, str):
            vector = self.vectorizer.transform([text]).toarray()[0]
            # Pad to match requested dimension if vocabulary is smaller
            if len(vector) < self._dimension:
                padded = np.zeros(self._dimension)
                padded[:len(vector)] = vector
                return padded
            return vector

        vectors = self.vectorizer.transform(text).toarray()
        # Pad to match requested dimension if vocabulary is smaller
        if vectors.shape[1] < self._dimension:
            padded = np.zeros((vectors.shape[0], self._dimension))
            padded[:, :vectors.shape[1]] = vectors
            return padded
        return vectors

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self._dimension

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "local/tfidf"


class OllamaProvider(EmbeddingProvider):
    """
    Ollama embeddings provider (FREE, local, high quality).

    Uses Ollama's local inference server for embeddings. Requires
    Ollama to be running on localhost:11434.

    Default model: 'nomic-embed-text' (768 dimensions, excellent quality)

    Install Ollama: https://ollama.ai
    Pull model: ollama pull nomic-embed-text

    Usage:
        provider = OllamaProvider(model_name="nomic-embed-text")
        vector = provider.embed("consciousness continuity")
    """

    MODEL_DIMENSIONS = {
        "nomic-embed-text": 768,
        "mxbai-embed-large": 1024,
        "snowflake-arctic-embed": 1024,
        "all-minilm": 384,
    }

    def __init__(
        self,
        model_name: str = "nomic-embed-text",
        api_url: str = "http://localhost:11434/api/embeddings",
        timeout: int = 30,
    ):
        """
        Initialize Ollama provider.

        Args:
            model_name: Ollama model name (default: nomic-embed-text)
            api_url: Ollama API endpoint (default: http://localhost:11434/api/embeddings)
            timeout: Request timeout in seconds (default: 30)
        """
        self.model_name = model_name
        self.api_url = api_url
        self.timeout = timeout
        self._dimension = self.MODEL_DIMENSIONS.get(model_name, 768)

    def embed(self, text: Union[str, List[str]]) -> np.ndarray:
        """
        Generate embeddings using Ollama API.

        Gracefully handles Ollama not running by raising clear error.
        """
        import urllib.request
        import urllib.error
        import json

        if isinstance(text, str):
            texts = [text]
            single = True
        else:
            texts = text
            single = False

        embeddings = []
        for t in texts:
            payload = json.dumps({
                "model": self.model_name,
                "prompt": t
            }).encode('utf-8')

            req = urllib.request.Request(
                self.api_url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    result = json.loads(response.read().decode())
                    embeddings.append(result["embedding"])
            except urllib.error.URLError as e:
                raise RuntimeError(
                    f"Ollama not running or not accessible at {self.api_url}. "
                    f"Install: https://ollama.ai | Pull model: ollama pull {self.model_name}"
                ) from e
            except Exception as e:
                raise RuntimeError(f"Ollama embedding failed: {str(e)}") from e

        embeddings = np.array(embeddings, dtype=np.float32)

        if single:
            return embeddings[0]
        return embeddings

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self._dimension

    def get_provider_name(self) -> str:
        """Get provider name."""
        return f"ollama/{self.model_name}"


class SimpleHashProvider(EmbeddingProvider):
    """
    Pure Python word-hash based embeddings (ZERO dependencies).

    This provider uses consistent hashing of word n-grams to create
    fixed-dimensional sparse vectors. Works anywhere Python runs.

    Quality is lower than transformer models but requires NO external
    dependencies - perfect for constrained environments like mobile.

    Usage:
        provider = SimpleHashProvider(dimension=256)
        vector = provider.embed("consciousness continuity")
    """

    def __init__(self, dimension: int = 256):
        """
        Initialize simple hash provider.

        Args:
            dimension: Embedding dimension (default: 256)
        """
        self._dimension = dimension
        self._stopwords = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'shall',
            'can', 'of', 'to', 'in', 'for', 'on', 'with', 'at', 'by',
            'from', 'as', 'into', 'through', 'during', 'before', 'after',
            'above', 'below', 'between', 'under', 'again', 'further',
            'then', 'once', 'here', 'there', 'when', 'where', 'why',
            'how', 'all', 'each', 'few', 'more', 'most', 'other', 'some',
            'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
            'than', 'too', 'very', 'just', 'and', 'but', 'if', 'or',
            'because', 'until', 'while', 'this', 'that', 'these', 'those',
            'am', 'it', 'its', 'he', 'she', 'they', 'them', 'his', 'her',
            'their', 'what', 'which', 'who', 'whom', 'i', 'you', 'we', 'me'
        }

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into meaningful words."""
        import re
        # Convert to lowercase, extract words
        words = re.findall(r'\b[a-z]{2,}\b', text.lower())
        # Remove stopwords
        return [w for w in words if w not in self._stopwords]

    def _hash_to_index(self, token: str) -> int:
        """Hash token to embedding index."""
        return hash(token) % self._dimension

    def _hash_to_sign(self, token: str) -> int:
        """Hash token to determine sign (+1 or -1)."""
        return 1 if hash(token + "_sign") % 2 == 0 else -1

    def embed(self, text: Union[str, List[str]]) -> np.ndarray:
        """
        Generate hash-based embeddings.

        Uses feature hashing (hashing trick) to create sparse vectors:
        - Each word hashes to an index
        - Sign is determined by secondary hash
        - Bigrams are also included for context
        """
        if isinstance(text, str):
            texts = [text]
            single = True
        else:
            texts = text
            single = False

        embeddings = []
        for t in texts:
            vector = np.zeros(self._dimension, dtype=np.float32)
            tokens = self._tokenize(t)

            # Add unigrams
            for token in tokens:
                idx = self._hash_to_index(token)
                sign = self._hash_to_sign(token)
                vector[idx] += sign

            # Add bigrams for context
            for i in range(len(tokens) - 1):
                bigram = f"{tokens[i]}_{tokens[i+1]}"
                idx = self._hash_to_index(bigram)
                sign = self._hash_to_sign(bigram)
                vector[idx] += sign * 0.5  # Lower weight for bigrams

            # Normalize
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm

            embeddings.append(vector)

        if single:
            return embeddings[0]
        return np.array(embeddings)

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self._dimension

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "simple/hash"


def get_default_provider() -> EmbeddingProvider:
    """
    Get the best available embedding provider.

    **FREE-FIRST PRIORITY** (updated 2025-12-16):
    We prioritize FREE, LOCAL providers over paid APIs. OpenAI is opt-in only.

    Priority order:
    1. SentenceTransformerProvider (FREE, local, high quality) - BEST DEFAULT
    2. OllamaProvider (FREE, local, if Ollama running) - Excellent alternative
    3. LocalProvider (FREE, sklearn TF-IDF) - Fallback if no transformers
    4. SimpleHashProvider (FREE, zero deps) - Ultimate fallback
    5. OpenAIProvider (PAID, only if explicitly configured) - Opt-in via CONTINUUM_USE_OPENAI=1

    OpenAI is INTENTIONALLY de-prioritized to avoid unexpected costs.
    To use OpenAI, set both OPENAI_API_KEY and CONTINUUM_USE_OPENAI=1.

    Returns:
        An initialized EmbeddingProvider instance
    """
    import os

    # PRIORITY 1: SentenceTransformers (FREE, local, high quality)
    # This is now the DEFAULT - best quality without any cost
    try:
        return SentenceTransformerProvider()
    except ImportError:
        pass

    # Check OpenAI preference FIRST (before Ollama)
    openai_key = os.environ.get("OPENAI_API_KEY")
    use_openai = os.environ.get("CONTINUUM_USE_OPENAI", "0") == "1"

    # PRIORITY 2: OpenAI if explicitly requested via CONTINUUM_USE_OPENAI=1
    if openai_key and use_openai:
        try:
            provider = OpenAIProvider(api_key=openai_key)
            return provider
        except Exception as e:
            warnings.warn(f"OpenAI provider failed: {e}", RuntimeWarning)

    # PRIORITY 3: Ollama (FREE, local, if running AND responding)
    try:
        provider = OllamaProvider()
        # Actually test if Ollama is running by making a request
        import urllib.request
        req = urllib.request.Request("http://localhost:11434/api/tags", method="GET")
        urllib.request.urlopen(req, timeout=2)
        return provider
    except Exception:
        # Ollama not running - continue to next provider
        pass

    # PRIORITY 4: LocalProvider (FREE, TF-IDF fallback)
    try:
        provider = LocalProvider()
        warnings.warn(
            "Using LocalProvider (TF-IDF). For better quality, install FREE providers:\n"
            "  - pip install sentence-transformers (RECOMMENDED)\n"
            "  - or install Ollama: https://ollama.ai",
            RuntimeWarning
        )
        return provider
    except ImportError:
        pass

    # PRIORITY 5: SimpleHashProvider (FREE, zero dependencies)
    # Ultimate fallback - works everywhere
    warnings.warn(
        "Using SimpleHashProvider (hash-based). For better quality, install FREE providers:\n"
        "  - pip install sentence-transformers (RECOMMENDED)\n"
        "  - or install Ollama: https://ollama.ai\n"
        "  - or pip install scikit-learn (TF-IDF)",
        RuntimeWarning
    )
    return SimpleHashProvider()

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
