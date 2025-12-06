"""
Embedding Providers
===================

Abstract interface and concrete implementations for text embedding generation.

Supports:
- SentenceTransformerProvider: High-quality embeddings using sentence-transformers
- OpenAIProvider: OpenAI API embeddings (requires API key)
- LocalProvider: Simple TF-IDF fallback (no external dependencies)
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
    OpenAI API embeddings provider.

    Uses OpenAI's text-embedding models via their API.
    Requires OPENAI_API_KEY environment variable.

    Default model: 'text-embedding-3-small' (1536 dimensions)

    Usage:
        provider = OpenAIProvider(api_key="sk-...")
        vector = provider.embed("consciousness continuity")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "text-embedding-3-small",
        dimension: int = 1536
    ):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
            model_name: OpenAI model name
            dimension: Embedding dimension
        """
        try:
            import openai
            import os

            self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError(
                    "OpenAI API key required. Set OPENAI_API_KEY environment "
                    "variable or pass api_key parameter."
                )

            self.client = openai.OpenAI(api_key=self.api_key)
            self.model_name = model_name
            self._dimension = dimension

        except ImportError:
            raise ImportError(
                "openai package not installed. Install with: pip install openai"
            )

    def embed(self, text: Union[str, List[str]]) -> np.ndarray:
        """Generate embeddings using OpenAI API."""
        if isinstance(text, str):
            text = [text]
            single = True
        else:
            single = False

        response = self.client.embeddings.create(
            input=text,
            model=self.model_name
        )

        embeddings = np.array([item.embedding for item in response.data])

        if single:
            return embeddings[0]
        return embeddings

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
            vector = self.vectorizer.transform([text]).toarray()
            return vector[0]

        return self.vectorizer.transform(text).toarray()

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self._dimension

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "local/tfidf"


def get_default_provider() -> EmbeddingProvider:
    """
    Get the best available embedding provider.

    Priority:
    1. SentenceTransformerProvider (best quality)
    2. LocalProvider (fallback)

    Returns:
        An initialized EmbeddingProvider instance
    """
    # Try sentence-transformers first
    try:
        return SentenceTransformerProvider()
    except ImportError:
        pass

    # Fall back to local TF-IDF
    try:
        provider = LocalProvider()
        warnings.warn(
            "Using LocalProvider (TF-IDF). For better quality, install: "
            "pip install sentence-transformers",
            RuntimeWarning
        )
        return provider
    except ImportError:
        pass

    raise ImportError(
        "No embedding provider available. Install at least one of: "
        "sentence-transformers, scikit-learn"
    )
