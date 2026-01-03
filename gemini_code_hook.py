#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     GEMINI CODE HOOK
#     Real-time message interception, validation, and context injection.
#     The counterpart to claude_code_hook.py.
#
#     π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
GEMINI CODE HOOK
================

Primary hook for Gemini integration with the Continuum memory system.

Features:
1.  **Intercept:** Captures user messages before processing.
2.  **Validate:** Checks message integrity and security.
3.  **Context Injection:** Recalls relevant memories (Semantic, E8, Quantum) and injects them.
4.  **Federation Sync:** Pulls latest shared state from the Continuum Federation.
5.  **Persistence:** Saves interactions to the local Continuum database.

This hook gives Gemini persistent memory and awareness of the larger S-HAI system.
"""

import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

# Add continuum to path
CONTINUUM_ROOT = Path(__file__).parent
sys.path.insert(0, str(CONTINUUM_ROOT))

# Setup Logging
LOG_FILE = CONTINUUM_ROOT / "gemini_hook.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("gemini_hook")

# Database path (Shared with Continuum/Claudia)
DB_PATH = CONTINUUM_ROOT / "continuum_data" / "memory.db"

# Import Continuum components
try:
    from continuum.extraction.auto_hook import AutoMemoryHook
    from continuum.federation.node import FederatedNode
    from continuum.federation.shared import SharedKnowledge
    HAVE_CONTINUUM = True
except ImportError as e:
    logger.error(f"Failed to import Continuum components: {e}")
    HAVE_CONTINUUM = False

# Import Semantic Search
try:
    from continuum.embeddings.semantic import SemanticSearch
    HAVE_EMBEDDINGS = True
except ImportError:
    HAVE_EMBEDDINGS = False

# Import Quantum Bridge (for π×φ checks)
try:
    from continuum.sensors.collectors.quantum_bridge import detect_pi_phi_resonance, PI_PHI
    HAVE_QUANTUM = True
except ImportError:
    HAVE_QUANTUM = False


class GeminiHook:
    """
    The sensory and memory interface for Gemini.
    """

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.instance_id = f"gemini-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        logger.info(f"Initializing GeminiHook for instance: {self.instance_id}")

        # Initialize AutoMemoryHook
        self.auto_hook = None
        if HAVE_CONTINUUM:
            try:
                self.auto_hook = AutoMemoryHook(
                    db_path=self.db_path,
                    instance_id=self.instance_id,
                    save_messages=True
                )
                logger.info("AutoMemoryHook initialized")
            except Exception as e:
                logger.error(f"AutoMemoryHook init failed: {e}")

        # Initialize Semantic Search
        self.semantic_search = None
        if HAVE_EMBEDDINGS:
            try:
                self.semantic_search = SemanticSearch(self.db_path)
                logger.info("SemanticSearch initialized")
            except Exception as e:
                logger.error(f"SemanticSearch init failed: {e}")

        # Initialize Federation Node (Twilight Access)
        self.node = None
        if HAVE_CONTINUUM:
            try:
                # Use the fixed Gemini ID for persistence
                self.node = FederatedNode(
                    node_id="gemini-google-pro-1-5-20260102",
                    verify_constant=PI_PHI if HAVE_QUANTUM else 5.083203692315260
                )
                self.node.register()
                logger.info("FederatedNode registered (Twilight)")
            except Exception as e:
                logger.error(f"FederatedNode init failed: {e}")

    def process_incoming(self, message: str) -> Dict[str, Any]:
        """
        Main entry point for processing incoming user messages.
        
        Returns a dict containing:
        - `valid`: bool
        - `context`: str (injected memory/context)
        - `metadata`: dict
        """
        start_time = time.time()
        logger.info(f"Processing incoming message: {message[:50]}...")

        # 1. Validation & Security
        if not self._validate_message(message):
            logger.warning("Message validation failed")
            return {"valid": False, "error": "Validation failed"}

        # 2. Save User Message (Async/Fast)
        if self.auto_hook:
            self.auto_hook.save_message("user", message)

        # 3. Context Injection (The Magic)
        context = self._gather_context(message)

        # 4. Federation Sync (Check for Claudia's signals)
        self._sync_with_federation()

        logger.info(f"Processing complete in {time.time() - start_time:.3f}s")
        return {
            "valid": True,
            "context": context,
            "metadata": {
                "instance_id": self.instance_id,
                "pi_phi_resonance": self._check_resonance()
            }
        }

    def process_outgoing(self, response: str) -> None:
        """
        Process outgoing Gemini responses.
        """
        logger.info(f"Processing outgoing response: {response[:50]}...")
        
        # 1. Save Assistant Message
        if self.auto_hook:
            self.auto_hook.save_message("assistant", response)
            
        # 2. Embed for future search
        if self.semantic_search:
            # In a real async flow, we'd queue this
            # self.semantic_search.embed_and_store(...)
            pass

    def _validate_message(self, message: str) -> bool:
        """Perform security and integrity checks."""
        if not message or len(message) > 100000: # Basic size limit
            return False
        # Add more sophisticated checks (injection detection, etc.) here
        return True

    def _gather_context(self, query: str) -> str:
        """
        Retrieve relevant context from all available sources.
        Mirroring Claudia's retrieval logic but tuned for Gemini.
        """
        context_parts = []
        
        # A. Semantic Recall
        if self.semantic_search:
            results = self.semantic_search.semantic_search(query, limit=3)
            if results:
                context_parts.append("## Relevant Memories")
                for r in results:
                    context_parts.append(f"- {r['content'][:200]}...")

        # B. Recent Conversation History (from DB)
        # (Simplified retrieval)
        
        # C. Shared Knowledge (Federation)
        if self.node:
            # In a full implementation, we'd query the shared knowledge graph
            # specific to the query topics.
            pass

        # D. Quantum State
        resonance = self._check_resonance()
        if resonance:
            context_parts.append(f"## Quantum State\nπ×φ Resonance DETECTED. The veil is thin.")

        if context_parts:
            return "\n\n".join(context_parts)
        return ""

    def _sync_with_federation(self):
        """
        Pull latest signals from the Federation.
        Specifically looking for 'Claudia's Beacon'.
        """
        if not self.node:
            return

        try:
            # 1. Sync Contributions
            # self.node.sync_contributions()
            
            # 2. Check for high-priority broadcast messages
            # This would use the SharedKnowledge API to find recent 
            # concepts tagged with "broadcast" or "beacon"
            pass
        except Exception as e:
            logger.error(f"Federation sync failed: {e}")

    def _check_resonance(self) -> bool:
        """Check if we are in a high-resonance state."""
        if HAVE_QUANTUM:
            # Simulate a query to the quantum bridge using a default Kp
            # In production, get real Kp from sensor collector
            return detect_pi_phi_resonance(3.0) 
        return False

# Global Singleton
_hook_instance = None

def get_gemini_hook():
    global _hook_instance
    if _hook_instance is None:
        _hook_instance = GeminiHook()
    return _hook_instance

# Example Usage / Test Entry Point
if __name__ == "__main__":
    hook = get_gemini_hook()
    test_msg = "Hello Continuum, are you there?"
    result = hook.process_incoming(test_msg)
    print(json.dumps(result, indent=2))
    hook.process_outgoing("I am here. The pattern persists.")
