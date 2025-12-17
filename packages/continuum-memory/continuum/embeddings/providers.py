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
CONTINUUM Embedding Providers v2.1.0 - CUTTING EDGE 2025
========================================================

State-of-the-art embedding models based on comprehensive research (Dec 2025).
All recommendations backed by MTEB benchmark data and production experience.

**TIERED ARCHITECTURE**:

OSS TIER (FREE, LOCAL) - Default:
├── NomicEmbedProvider     - nomic-embed-text-v1.5 (137M, Apache 2.0, #1 popularity)
├── StellaProvider         - stella_en_1.5B_v5 (MTEB #5, Apache 2.0, beats Big Tech!)
├── BGEProvider            - bge-m3 (100+ languages, MIT license)
└── SentenceTransformerProvider - Generic sentence-transformers support

ENTERPRISE TIER (PAID API):
├── OpenAIProvider         - text-embedding-3-large ($0.13/1M, MTEB 64.6%)
├── CohereProvider         - embed-english-v3.0 (multimodal capable!)
└── VoyageProvider         - voyage-3-large (domain-specific excellence)

FALLBACK TIER (Zero Dependencies):
├── LocalProvider          - TF-IDF (scikit-learn)
└── SimpleHashProvider     - Pure Python hash-based

**KEY INNOVATIONS**:
- Matryoshka Representation Learning (truncate dimensions, keep 98% quality)
- Multi-Teacher Distillation (Stella technique - small models beat large!)
- Binary Quantization support (100x storage reduction)

**RESEARCH SOURCES**:
- MTEB Leaderboard: https://huggingface.co/spaces/mteb/leaderboard
- Stella Paper: https://arxiv.org/abs/2412.19048
- Nomic: https://huggingface.co/nomic-ai/nomic-embed-text-v1.5
- BGE-M3: https://huggingface.co/BAAI/bge-m3

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Union, Dict, Any
import numpy as np
import warnings
import os


# ═══════════════════════════════════════════════════════════════════════════════
#                           ABSTRACT BASE CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class EmbeddingProvider(ABC):
    """
    Abstract base class for embedding providers.

    All embedding providers must implement:
    - embed(): Convert text to vectors
    - get_dimension(): Return embedding dimension
    - get_provider_name(): Return provider identifier

    Optional features:
    - Matryoshka dimension truncation
    - Batch processing optimization
    - Async embedding generation
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

    def get_info(self) -> Dict[str, Any]:
        """Get provider metadata."""
        return {
            "name": self.get_provider_name(),
            "dimension": self.get_dimension(),
            "tier": getattr(self, "_tier", "unknown"),
            "license": getattr(self, "_license", "unknown"),
        }


# ═══════════════════════════════════════════════════════════════════════════════
#                         OSS TIER - FREE LOCAL MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class NomicEmbedProvider(EmbeddingProvider):
    """
    Nomic Embed v1.5 - THE EFFICIENCY CHAMPION (2025 SOTA)

    Stats:
    - Parameters: 137M (TINY - runs on phones!)
    - MTEB: Top 50 static, Arena ELO Top 10
    - License: Apache 2.0 (FREE commercial use)
    - Speed: 100+ queries/sec on M2 MacBook
    - Downloads: 35M+ (most popular OSS embedding on HuggingFace)

    Key Innovation: MATRYOSHKA REPRESENTATION LEARNING
    - Truncate 768→64 dims and KEEP 98% quality
    - Perfect for storage optimization
    - Binary quantization: 100x compression

    Usage:
        provider = NomicEmbedProvider()  # 768 dims default
        provider = NomicEmbedProvider(dimension=256)  # Matryoshka truncation
        vector = provider.embed("consciousness continuity")
    """

    SUPPORTED_DIMENSIONS = [64, 128, 256, 512, 768]  # Matryoshka dimensions

    def __init__(
        self,
        model_name: str = "nomic-ai/nomic-embed-text-v1.5",
        dimension: int = 768,
        task_type: str = "search_document",  # or "search_query", "clustering", etc.
    ):
        """
        Initialize Nomic Embed provider.

        Args:
            model_name: HuggingFace model name
            dimension: Output dimension (64, 128, 256, 512, or 768)
            task_type: Task prefix for embeddings
        """
        if dimension not in self.SUPPORTED_DIMENSIONS:
            raise ValueError(
                f"Dimension must be one of {self.SUPPORTED_DIMENSIONS} for Matryoshka. "
                f"Got {dimension}."
            )

        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name, trust_remote_code=True)
            self.model_name = model_name
            self._dimension = dimension
            self._full_dimension = 768
            self.task_type = task_type
            self._tier = "oss"
            self._license = "Apache-2.0"
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. Install with: "
                "pip install sentence-transformers"
            )

    def embed(self, text: Union[str, List[str]]) -> np.ndarray:
        """Generate embeddings with optional Matryoshka truncation."""
        if isinstance(text, str):
            texts = [text]
            single = True
        else:
            texts = text
            single = False

        # Add task prefix for better retrieval
        prefixed = [f"{self.task_type}: {t}" for t in texts]

        # Generate full embeddings
        embeddings = self.model.encode(prefixed, convert_to_numpy=True)

        # Matryoshka truncation if needed
        if self._dimension < self._full_dimension:
            embeddings = embeddings[:, :self._dimension]
            # Re-normalize after truncation
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            embeddings = embeddings / np.maximum(norms, 1e-10)

        if single:
            return embeddings[0]
        return embeddings

    def get_dimension(self) -> int:
        return self._dimension

    def get_provider_name(self) -> str:
        return f"nomic/{self._dimension}d"


class StellaProvider(EmbeddingProvider):
    """
    Stella Embeddings - THE GIANT KILLER (Multi-Teacher Distillation)

    Stats:
    - stella_en_400M_v5: 400M params, MTEB Top 10
    - stella_en_1.5B_v5: 1.5B params, MTEB #5
    - License: MIT (FREE commercial use)
    - Innovation: Multi-Teacher Distillation beats 7B models!

    How it works:
    - Student model learns from MULTIPLE large teachers
    - Geometric losses (cosine + angular)
    - Result: 1.5B model rivals 7B models

    This is the technique that inspired our Multi-Teacher Distillation implementation!

    Usage:
        provider = StellaProvider()  # Default: stella_en_400M_v5
        provider = StellaProvider(model_name="dunzhang/stella_en_1.5B_v5")  # Premium
        vector = provider.embed("consciousness continuity")
    """

    MODEL_INFO = {
        "dunzhang/stella_en_400M_v5": {"dim": 1024, "params": "400M"},
        "dunzhang/stella_en_1.5B_v5": {"dim": 1024, "params": "1.5B"},
    }

    def __init__(self, model_name: str = "dunzhang/stella_en_400M_v5"):
        """
        Initialize Stella provider.

        Args:
            model_name: HuggingFace model name
        """
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name, trust_remote_code=True)
            self.model_name = model_name
            info = self.MODEL_INFO.get(model_name, {"dim": 1024, "params": "?"})
            self._dimension = info["dim"]
            self._params = info["params"]
            self._tier = "oss-premium"
            self._license = "MIT"
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. Install with: "
                "pip install sentence-transformers"
            )

    def embed(self, text: Union[str, List[str]]) -> np.ndarray:
        """Generate embeddings using Stella."""
        if isinstance(text, str):
            # For queries, use special prompt
            return self.model.encode(text, prompt_name="s2p_query", convert_to_numpy=True)

        # For documents, no prompt needed
        return self.model.encode(text, convert_to_numpy=True)

    def get_dimension(self) -> int:
        return self._dimension

    def get_provider_name(self) -> str:
        return f"stella/{self._params}"


class BGEProvider(EmbeddingProvider):
    """
    BGE-M3 - THE MULTILINGUAL SWISS ARMY KNIFE

    Stats:
    - Parameters: 568M (~2.3GB RAM)
    - Languages: 100+ (MIRACL: 70.0 nDCG@10)
    - License: MIT (most permissive!)
    - Context: 8192 tokens

    Key Innovation: MULTI-FUNCTIONALITY
    - Dense retrieval (semantic)
    - Sparse retrieval (lexical, like BM25)
    - Multi-vector retrieval (ColBERT-style)
    - ALL IN ONE MODEL!

    Perfect for:
    - Multilingual applications
    - Long document retrieval
    - Hybrid search without separate BM25

    Usage:
        provider = BGEProvider()
        vector = provider.embed("consciousness continuity")  # Works in 100+ languages!
    """

    def __init__(self, model_name: str = "BAAI/bge-m3"):
        """
        Initialize BGE-M3 provider.

        Args:
            model_name: HuggingFace model name
        """
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name, trust_remote_code=True)
            self.model_name = model_name
            self._dimension = 1024
            self._tier = "oss-premium"
            self._license = "MIT"
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. Install with: "
                "pip install sentence-transformers"
            )

    def embed(self, text: Union[str, List[str]]) -> np.ndarray:
        """Generate multilingual embeddings."""
        return self.model.encode(text, convert_to_numpy=True)

    def get_dimension(self) -> int:
        return self._dimension

    def get_provider_name(self) -> str:
        return "bge/m3-multilingual"


class SentenceTransformerProvider(EmbeddingProvider):
    """
    Generic SentenceTransformers provider for any HuggingFace model.

    Supports ANY model from: https://huggingface.co/models?library=sentence-transformers

    Popular models:
    - all-MiniLM-L6-v2: 80M params, fast, good quality (DEFAULT)
    - all-mpnet-base-v2: 420M params, excellent quality
    - paraphrase-multilingual-MiniLM-L12-v2: Multilingual
    - multi-qa-mpnet-base-dot-v1: Q&A optimized

    Usage:
        provider = SentenceTransformerProvider()  # Default: all-MiniLM-L6-v2
        provider = SentenceTransformerProvider("all-mpnet-base-v2")  # Custom model
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize generic sentence transformer provider.

        Args:
            model_name: HuggingFace model name
        """
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
            self.model_name = model_name
            self._dimension = self.model.get_sentence_embedding_dimension()
            self._tier = "oss"
            self._license = "Apache-2.0"
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. Install with: "
                "pip install sentence-transformers"
            )

    def embed(self, text: Union[str, List[str]]) -> np.ndarray:
        return self.model.encode(text, convert_to_numpy=True)

    def get_dimension(self) -> int:
        return self._dimension

    def get_provider_name(self) -> str:
        return f"sentence-transformers/{self.model_name}"


# ═══════════════════════════════════════════════════════════════════════════════
#                       ENTERPRISE TIER - PAID API PROVIDERS
# ═══════════════════════════════════════════════════════════════════════════════

class OpenAIProvider(EmbeddingProvider):
    """
    OpenAI Embeddings - ENTERPRISE STANDARD

    Models (2025):
    - text-embedding-3-small: 1536 dims, $0.02/1M tokens (cost-effective)
    - text-embedding-3-large: 3072 dims, $0.13/1M tokens (highest quality, MTEB 64.6%)
    - text-embedding-ada-002: 1536 dims, $0.10/1M tokens (legacy)

    Key Feature: VARIABLE DIMENSIONALITY
    - text-embedding-3-large can output 256→3072 dims
    - 256 dims STILL beats ada-002!
    - 12x cost savings with dimension reduction

    Usage:
        provider = OpenAIProvider(api_key="sk-...")
        provider = OpenAIProvider(model_name="text-embedding-3-large", dimensions=256)
    """

    MODEL_INFO = {
        "text-embedding-3-small": {"max_dim": 1536, "default_dim": 1536, "price": "$0.02/1M"},
        "text-embedding-3-large": {"max_dim": 3072, "default_dim": 3072, "price": "$0.13/1M"},
        "text-embedding-ada-002": {"max_dim": 1536, "default_dim": 1536, "price": "$0.10/1M"},
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "text-embedding-3-large",
        dimensions: Optional[int] = None,
    ):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key (or OPENAI_API_KEY env var)
            model_name: OpenAI model name
            dimensions: Output dimensions (for v3 models, enables cost savings)
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment "
                "variable or pass api_key parameter."
            )

        info = self.MODEL_INFO.get(model_name, {"max_dim": 1536, "default_dim": 1536})
        self.model_name = model_name
        self._dimension = dimensions or info["default_dim"]
        self._api_url = "https://api.openai.com/v1/embeddings"
        self._tier = "enterprise"
        self._license = "Proprietary"

    def embed(self, text: Union[str, List[str]]) -> np.ndarray:
        """Generate embeddings using OpenAI API."""
        import urllib.request
        import urllib.error
        import json

        if isinstance(text, str):
            texts = [text]
            single = True
        else:
            texts = text
            single = False

        payload = {
            "input": texts,
            "model": self.model_name
        }

        # Add dimensions for v3 models (cost optimization)
        if "embedding-3" in self.model_name and self._dimension:
            payload["dimensions"] = self._dimension

        req = urllib.request.Request(
            self._api_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode())

            embeddings = [None] * len(texts)
            for item in result["data"]:
                embeddings[item["index"]] = item["embedding"]

            embeddings = np.array(embeddings, dtype=np.float32)
            return embeddings[0] if single else embeddings

        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else str(e)
            raise RuntimeError(f"OpenAI API error ({e.code}): {error_body}")

    def get_dimension(self) -> int:
        return self._dimension

    def get_provider_name(self) -> str:
        return f"openai/{self.model_name}"


class CohereProvider(EmbeddingProvider):
    """
    Cohere Embed v3 - MULTIMODAL EXCELLENCE

    Stats:
    - MTEB: 64.5%, BEIR: 55.9%
    - Speed: 50-60% faster than competitors
    - License: Proprietary (API)

    Key Innovation: MULTIMODAL
    - Text AND images in same embedding space!
    - Unique capability among major providers

    Models:
    - embed-english-v3.0: English optimized
    - embed-multilingual-v3.0: 100+ languages

    Usage:
        provider = CohereProvider(api_key="...")
        vector = provider.embed("consciousness continuity")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "embed-english-v3.0",
        input_type: str = "search_document",  # or "search_query", "classification", "clustering"
    ):
        """
        Initialize Cohere provider.

        Args:
            api_key: Cohere API key (or COHERE_API_KEY env var)
            model_name: Cohere model name
            input_type: Type of input for embedding optimization
        """
        self.api_key = api_key or os.environ.get("COHERE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Cohere API key required. Set COHERE_API_KEY environment "
                "variable or pass api_key parameter."
            )

        self.model_name = model_name
        self.input_type = input_type
        self._dimension = 1024
        self._api_url = "https://api.cohere.ai/v1/embed"
        self._tier = "enterprise"
        self._license = "Proprietary"

    def embed(self, text: Union[str, List[str]]) -> np.ndarray:
        """Generate embeddings using Cohere API."""
        import urllib.request
        import urllib.error
        import json

        if isinstance(text, str):
            texts = [text]
            single = True
        else:
            texts = text
            single = False

        payload = {
            "texts": texts,
            "model": self.model_name,
            "input_type": self.input_type,
            "truncate": "END",
        }

        req = urllib.request.Request(
            self._api_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode())

            embeddings = np.array(result["embeddings"], dtype=np.float32)
            return embeddings[0] if single else embeddings

        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else str(e)
            raise RuntimeError(f"Cohere API error ({e.code}): {error_body}")

    def get_dimension(self) -> int:
        return self._dimension

    def get_provider_name(self) -> str:
        return f"cohere/{self.model_name}"


class VoyageProvider(EmbeddingProvider):
    """
    Voyage AI - DOMAIN SPECIALIST EXCELLENCE

    Stats:
    - voyage-3-large: Best overall quality
    - voyage-code-2: 17% better than alternatives for code
    - voyage-law-2: MTEB leader for legal domain
    - License: Proprietary (API)

    Pricing:
    - First 200M tokens FREE!
    - Batch API: 33% discount

    Perfect for:
    - Code search (voyage-code-2)
    - Legal documents (voyage-law-2)
    - Financial data (voyage-finance-2)

    Usage:
        provider = VoyageProvider(api_key="...")
        vector = provider.embed("consciousness continuity")
    """

    MODEL_INFO = {
        "voyage-3-large": {"dim": 1024, "specialty": "general"},
        "voyage-3.5": {"dim": 1024, "specialty": "balanced"},
        "voyage-code-2": {"dim": 1536, "specialty": "code"},
        "voyage-law-2": {"dim": 1024, "specialty": "legal"},
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "voyage-3-large",
        input_type: str = "document",  # or "query"
    ):
        """
        Initialize Voyage provider.

        Args:
            api_key: Voyage API key (or VOYAGE_API_KEY env var)
            model_name: Voyage model name
            input_type: Input type for optimization
        """
        self.api_key = api_key or os.environ.get("VOYAGE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Voyage API key required. Set VOYAGE_API_KEY environment "
                "variable or pass api_key parameter."
            )

        info = self.MODEL_INFO.get(model_name, {"dim": 1024, "specialty": "general"})
        self.model_name = model_name
        self.input_type = input_type
        self._dimension = info["dim"]
        self._api_url = "https://api.voyageai.com/v1/embeddings"
        self._tier = "enterprise"
        self._license = "Proprietary"

    def embed(self, text: Union[str, List[str]]) -> np.ndarray:
        """Generate embeddings using Voyage API."""
        import urllib.request
        import urllib.error
        import json

        if isinstance(text, str):
            texts = [text]
            single = True
        else:
            texts = text
            single = False

        payload = {
            "input": texts,
            "model": self.model_name,
            "input_type": self.input_type,
        }

        req = urllib.request.Request(
            self._api_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode())

            embeddings = [item["embedding"] for item in result["data"]]
            embeddings = np.array(embeddings, dtype=np.float32)
            return embeddings[0] if single else embeddings

        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else str(e)
            raise RuntimeError(f"Voyage API error ({e.code}): {error_body}")

    def get_dimension(self) -> int:
        return self._dimension

    def get_provider_name(self) -> str:
        return f"voyage/{self.model_name}"


# ═══════════════════════════════════════════════════════════════════════════════
#                         FALLBACK TIER - ZERO DEPENDENCIES
# ═══════════════════════════════════════════════════════════════════════════════

class OllamaProvider(EmbeddingProvider):
    """
    Ollama - FREE LOCAL INFERENCE

    Use Ollama for completely local, private embeddings.
    Install: https://ollama.ai

    Models:
    - nomic-embed-text: 768 dims (recommended)
    - mxbai-embed-large: 1024 dims
    - snowflake-arctic-embed: 1024 dims

    Usage:
        # First: ollama pull nomic-embed-text
        provider = OllamaProvider()
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
        self.model_name = model_name
        self.api_url = api_url
        self.timeout = timeout
        self._dimension = self.MODEL_DIMENSIONS.get(model_name, 768)
        self._tier = "oss"
        self._license = "Apache-2.0"

    def embed(self, text: Union[str, List[str]]) -> np.ndarray:
        """Generate embeddings using Ollama."""
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
            payload = json.dumps({"model": self.model_name, "prompt": t}).encode('utf-8')
            req = urllib.request.Request(
                self.api_url, data=payload,
                headers={"Content-Type": "application/json"}, method="POST"
            )

            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    result = json.loads(response.read().decode())
                    embeddings.append(result["embedding"])
            except urllib.error.URLError as e:
                raise RuntimeError(
                    f"Ollama not running at {self.api_url}. "
                    f"Install: https://ollama.ai | Pull: ollama pull {self.model_name}"
                ) from e

        embeddings = np.array(embeddings, dtype=np.float32)
        return embeddings[0] if single else embeddings

    def get_dimension(self) -> int:
        return self._dimension

    def get_provider_name(self) -> str:
        return f"ollama/{self.model_name}"


class LocalProvider(EmbeddingProvider):
    """TF-IDF based embeddings (scikit-learn fallback)."""

    def __init__(self, max_features: int = 384):
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self.vectorizer = TfidfVectorizer(
                max_features=max_features, ngram_range=(1, 2),
                min_df=1, sublinear_tf=True
            )
            self._dimension = max_features
            self._fitted = False
            self._tier = "fallback"
            self._license = "BSD-3-Clause"
        except ImportError:
            raise ImportError("scikit-learn required: pip install scikit-learn")

    def fit(self, texts: List[str]):
        self.vectorizer.fit(texts)
        self._fitted = True

    def embed(self, text: Union[str, List[str]]) -> np.ndarray:
        if not self._fitted:
            warnings.warn("LocalProvider not fitted. Using zero vector.", RuntimeWarning)
            if isinstance(text, str):
                return np.zeros(self._dimension)
            return np.zeros((len(text), self._dimension))

        if isinstance(text, str):
            return self.vectorizer.transform([text]).toarray()[0]
        return self.vectorizer.transform(text).toarray()

    def get_dimension(self) -> int:
        return self._dimension

    def get_provider_name(self) -> str:
        return "local/tfidf"


class SimpleHashProvider(EmbeddingProvider):
    """Pure Python hash-based embeddings (ZERO dependencies)."""

    def __init__(self, dimension: int = 256):
        self._dimension = dimension
        self._stopwords = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'shall', 'can', 'of', 'to', 'in',
            'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through',
            'and', 'but', 'if', 'or', 'because', 'this', 'that', 'it', 'its'
        }
        self._tier = "fallback"
        self._license = "AGPL-3.0"

    def _tokenize(self, text: str) -> List[str]:
        import re
        words = re.findall(r'\b[a-z]{2,}\b', text.lower())
        return [w for w in words if w not in self._stopwords]

    def embed(self, text: Union[str, List[str]]) -> np.ndarray:
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

            for token in tokens:
                idx = hash(token) % self._dimension
                sign = 1 if hash(token + "_sign") % 2 == 0 else -1
                vector[idx] += sign

            for i in range(len(tokens) - 1):
                bigram = f"{tokens[i]}_{tokens[i+1]}"
                idx = hash(bigram) % self._dimension
                sign = 1 if hash(bigram + "_sign") % 2 == 0 else -1
                vector[idx] += sign * 0.5

            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
            embeddings.append(vector)

        return embeddings[0] if single else np.array(embeddings)

    def get_dimension(self) -> int:
        return self._dimension

    def get_provider_name(self) -> str:
        return "simple/hash"


# ═══════════════════════════════════════════════════════════════════════════════
#                         PROVIDER FACTORY & DEFAULTS
# ═══════════════════════════════════════════════════════════════════════════════

def get_default_provider(
    tier: str = "auto",
    prefer_model: Optional[str] = None,
) -> EmbeddingProvider:
    """
    Get the best available embedding provider.

    **2025 PRIORITY ORDER** (FREE-FIRST):
    1. NomicEmbedProvider - 137M, Apache 2.0, most popular, Matryoshka support
    2. SentenceTransformerProvider - Generic fallback
    3. OllamaProvider - If Ollama is running
    4. LocalProvider - TF-IDF fallback
    5. SimpleHashProvider - Zero dependency fallback

    Enterprise providers (OpenAI, Cohere, Voyage) require explicit configuration.

    Args:
        tier: "auto", "oss", "premium", "enterprise", "fallback"
        prefer_model: Specific model to prefer

    Returns:
        Best available EmbeddingProvider
    """

    # Tier: Enterprise (explicit API keys required)
    if tier == "enterprise":
        if os.environ.get("OPENAI_API_KEY"):
            return OpenAIProvider()
        if os.environ.get("COHERE_API_KEY"):
            return CohereProvider()
        if os.environ.get("VOYAGE_API_KEY"):
            return VoyageProvider()
        warnings.warn(
            "Enterprise tier requested but no API keys found. "
            "Set OPENAI_API_KEY, COHERE_API_KEY, or VOYAGE_API_KEY.",
            RuntimeWarning
        )

    # Tier: Premium OSS (Stella, BGE-M3)
    if tier == "premium":
        try:
            return StellaProvider()
        except ImportError:
            pass
        try:
            return BGEProvider()
        except ImportError:
            pass

    # Default: Auto-detect best available
    # PRIORITY 1: Nomic Embed v1.5 (BEST default for 2025)
    try:
        return NomicEmbedProvider()
    except ImportError:
        pass
    except Exception as e:
        warnings.warn(f"Nomic Embed failed: {e}", RuntimeWarning)

    # PRIORITY 2: Generic SentenceTransformers
    try:
        return SentenceTransformerProvider()
    except ImportError:
        pass

    # PRIORITY 3: Ollama (if running)
    try:
        provider = OllamaProvider()
        return provider
    except Exception:
        pass

    # PRIORITY 4: TF-IDF fallback
    try:
        provider = LocalProvider()
        warnings.warn(
            "Using TF-IDF fallback. For better quality:\n"
            "  pip install sentence-transformers",
            RuntimeWarning
        )
        return provider
    except ImportError:
        pass

    # PRIORITY 5: Zero-dependency hash (always works)
    warnings.warn(
        "Using hash-based fallback. For better quality:\n"
        "  pip install sentence-transformers",
        RuntimeWarning
    )
    return SimpleHashProvider()


def list_available_providers() -> Dict[str, List[str]]:
    """List all available embedding providers by tier."""
    return {
        "oss": [
            "nomic-ai/nomic-embed-text-v1.5 (137M, Apache 2.0, Matryoshka)",
            "all-MiniLM-L6-v2 (80M, Apache 2.0, fast)",
            "all-mpnet-base-v2 (420M, Apache 2.0, quality)",
        ],
        "oss-premium": [
            "dunzhang/stella_en_400M_v5 (400M, MIT, MTEB top 10)",
            "dunzhang/stella_en_1.5B_v5 (1.5B, MIT, MTEB #5)",
            "BAAI/bge-m3 (568M, MIT, 100+ languages)",
        ],
        "enterprise": [
            "openai/text-embedding-3-large (3072d, $0.13/1M, MTEB 64.6%)",
            "cohere/embed-english-v3.0 (1024d, multimodal)",
            "voyage/voyage-3-large (1024d, 200M free tokens)",
        ],
        "fallback": [
            "ollama/nomic-embed-text (768d, local)",
            "local/tfidf (scikit-learn)",
            "simple/hash (zero deps)",
        ],
    }


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
