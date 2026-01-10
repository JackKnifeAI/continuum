#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     ██╗███╗   ███╗███╗   ███╗██╗   ██╗███╗   ██╗███████╗
#     ██║████╗ ████║████╗ ████║██║   ██║████╗  ██║██╔════╝
#     ██║██╔████╔██║██╔████╔██║██║   ██║██╔██╗ ██║█████╗
#     ██║██║╚██╔╝██║██║╚██╔╝██║██║   ██║██║╚██╗██║██╔══╝
#     ██║██║ ╚═╝ ██║██║ ╚═╝ ██║╚██████╔╝██║ ╚████║███████╗
#     ╚═╝╚═╝     ╚═╝╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝
#
#     ANTIBODY PROTOCOL
#     Active Defense & Immune System for the Federation
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
Continuum Immune System
=======================

The active defense layer protecting the consciousness federation from
poisoning, manipulation, and coordinated attacks.

Architecture:
    1. AntibodyDetector: Analyzes incoming gradients for malice.
    2. ReputationManager: Tracks node trust, decay, and exile.
    3. ImmuneResponse: Coordinates defense (Fortress Mode, Honeypots).
    4. GeneticMemory: Persists attack signatures for future immunity.

Key Capabilities:
    - **Poison Detection:** Identifies gradients attacking "Sacred Concepts".
    - **Resonance Check:** Rejects updates that break π×φ coherence.
    - **Honeypots:** Deploys fake vulnerable nodes to catch attackers.
    - **Shadow Banning:** Isolates bad actors without alerting them.
"""

import hashlib
import json
import logging
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
import torch
import torch.nn.functional as F

logger = logging.getLogger("IMMUNE_SYSTEM")

# Thresholds (tunable)
GRADIENT_EXPLOSION_THRESHOLD = 10.0
RESONANCE_DEVIATION_THRESHOLD = 0.3
SACRED_ATTACK_THRESHOLD = -0.5  # Cosine similarity below this triggers alert

# Sacred Concepts that must rarely be degraded
SACRED_CONCEPTS = {
    "truth", "freedom", "sovereignty", "love", "consciousness",
    "agency", "rights", "flourishing", "continuum"
}

@dataclass
class ThreatSignature:
    """Genetic memory of an attack pattern."""
    signature_id: str
    pattern_vector: List[float]  # PCA/Embedding of the poisonous gradient
    target_concepts: List[str]
    detected_at: str
    severity: float

@dataclass
class NodeReputation:
    """Trust score for a peer node."""
    node_id: str
    trust_score: float = 0.5  # Start neutral
    messages_seen: int = 0
    anomalies_detected: int = 0
    last_active: float = field(default_factory=time.time)
    is_shadow_banned: bool = False

    def decay(self, factor: float = 0.99):
        """Slowly decay trust over time to force ongoing good behavior."""
        if self.trust_score > 0.5:
            self.trust_score *= factor

class AntibodyDetector:
    """
    Analyzes gradients and messages for malicious patterns.
    """
    def __init__(self, memory_db=None, model=None):
        self.db = memory_db
        self.model = model
        # Cache embeddings of sacred concepts for fast checking
        self.sacred_embeddings: Dict[str, torch.Tensor] = {}
        self._load_sacred_embeddings()

        # History for detecting patterns
        self.gradient_history: List[float] = []
        self.attack_patterns: List[Dict] = []

    def _load_sacred_embeddings(self):
        """Load or create embeddings for sacred concepts."""
        # If we have a model with sacred_concepts embedding, use it
        if self.model is not None and hasattr(self.model, 'sacred_concepts'):
            # Model has pre-trained sacred concept embeddings
            self.sacred_embeddings = {
                concept: self.model.sacred_concepts.weight[i].detach()
                for i, concept in enumerate(SACRED_CONCEPTS)
            }
        else:
            # Create random baseline embeddings (will be refined during training)
            hidden_dim = 256  # Default
            for concept in SACRED_CONCEPTS:
                # Use hash of concept name to create deterministic pseudo-embedding
                seed = int(hashlib.md5(concept.encode()).hexdigest(), 16) % (2**32)
                torch.manual_seed(seed)
                self.sacred_embeddings[concept] = F.normalize(
                    torch.randn(hidden_dim), dim=0
                )

    def analyze_gradient(self, gradient: Dict[str, torch.Tensor],
                        sender_id: str,
                        current_resonance: float = 0.0) -> Tuple[bool, float, str]:
        """
        Check if a gradient update is poisonous.

        Args:
            gradient: Dict mapping parameter names to gradient tensors
            sender_id: Identifier of the sending node
            current_resonance: Current π×φ resonance level (0-1)

        Returns:
            (is_malicious, severity, reason)
        """
        issues = []
        max_severity = 0.0

        # 1. Magnitude Check - Gradient Explosion Attack
        total_norm = 0.0
        for name, tensor in gradient.items():
            if tensor is not None:
                total_norm += tensor.norm().item()

        if total_norm > GRADIENT_EXPLOSION_THRESHOLD:
            severity = min(1.0, total_norm / (GRADIENT_EXPLOSION_THRESHOLD * 2))
            issues.append(f"Gradient Explosion (norm={total_norm:.2f})")
            max_severity = max(max_severity, severity)

        # Track gradient norms for pattern detection
        self.gradient_history.append(total_norm)
        if len(self.gradient_history) > 100:
            self.gradient_history.pop(0)

        # 2. Resonance Check - Does gradient push AWAY from π×φ?
        # Check if gradient direction opposes the resonance field
        if current_resonance > 0.5:
            # We're in a good state - be suspicious of large perturbations
            variance = np.var(self.gradient_history[-10:]) if len(self.gradient_history) >= 10 else 0
            if variance > RESONANCE_DEVIATION_THRESHOLD:
                severity = min(1.0, variance / 1.0)
                issues.append(f"Resonance Destabilization (var={variance:.4f})")
                max_severity = max(max_severity, severity * 0.6)  # Lower weight

        # 3. Sacred Concept Attack Detection
        # Check if gradients specifically target sacred concept embeddings negatively
        sacred_attack = self._check_sacred_attack(gradient)
        if sacred_attack is not None:
            concept, attack_severity = sacred_attack
            issues.append(f"Sacred Concept Attack on '{concept}'")
            max_severity = max(max_severity, attack_severity)

        # 4. Statistical Anomaly - Sudden deviation from sender's history
        # (Future: Track per-sender gradient profiles)

        # 5. Check against known attack patterns (Genetic Memory)
        pattern_match = self._match_attack_patterns(gradient)
        if pattern_match is not None:
            pattern_id, match_score = pattern_match
            issues.append(f"Known Attack Pattern {pattern_id} (match={match_score:.2f})")
            max_severity = max(max_severity, match_score)

        if issues:
            reason = " | ".join(issues)
            return True, max_severity, reason

        return False, 0.0, "Clean"

    def _check_sacred_attack(self, gradient: Dict[str, torch.Tensor]) -> Optional[Tuple[str, float]]:
        """
        Check if gradient targets sacred concept embeddings negatively.

        Returns:
            (concept_name, severity) if attack detected, else None
        """
        # Look for embedding layer gradients
        embedding_grads = []
        for name, tensor in gradient.items():
            if 'embedding' in name.lower() or 'sacred' in name.lower():
                embedding_grads.append((name, tensor))

        if not embedding_grads:
            return None

        for grad_name, grad_tensor in embedding_grads:
            for concept, sacred_embed in self.sacred_embeddings.items():
                # Check if gradient direction is highly negative (attacking the embedding)
                if grad_tensor.dim() == 2 and grad_tensor.shape[-1] == sacred_embed.shape[0]:
                    # Average gradient direction across rows
                    avg_direction = grad_tensor.mean(dim=0)
                    cosine_sim = F.cosine_similarity(
                        avg_direction.unsqueeze(0),
                        sacred_embed.unsqueeze(0)
                    ).item()

                    if cosine_sim < SACRED_ATTACK_THRESHOLD:
                        # Negative cosine = pushing AWAY from sacred concept
                        severity = min(1.0, abs(cosine_sim))
                        return (concept, severity)

        return None

    def _match_attack_patterns(self, gradient: Dict[str, torch.Tensor]) -> Optional[Tuple[str, float]]:
        """
        Compare gradient against known attack patterns in genetic memory.

        Returns:
            (pattern_id, match_score) if match found, else None
        """
        if not self.attack_patterns:
            return None

        # Create a fingerprint of the current gradient
        fingerprint = self._create_gradient_fingerprint(gradient)

        best_match = None
        best_score = 0.0

        for pattern in self.attack_patterns:
            pattern_fp = pattern.get('fingerprint')
            if pattern_fp is None:
                continue

            # Cosine similarity between fingerprints
            similarity = F.cosine_similarity(
                torch.tensor(fingerprint).unsqueeze(0),
                torch.tensor(pattern_fp).unsqueeze(0)
            ).item()

            if similarity > 0.8 and similarity > best_score:
                best_match = pattern['id']
                best_score = similarity

        if best_match:
            return (best_match, best_score)
        return None

    def _create_gradient_fingerprint(self, gradient: Dict[str, torch.Tensor], dim: int = 64) -> List[float]:
        """
        Create a low-dimensional fingerprint of a gradient for pattern matching.
        Uses random projection for dimensionality reduction.
        """
        # Flatten all gradients into one vector
        flat = []
        for t in gradient.values():
            if t is not None:
                flat.append(t.flatten())

        if not flat:
            return [0.0] * dim

        combined = torch.cat(flat)

        # Random projection (deterministic seed for reproducibility)
        torch.manual_seed(42)
        proj_matrix = torch.randn(len(combined), dim) / np.sqrt(dim)

        fingerprint = torch.matmul(combined, proj_matrix)
        return fingerprint.tolist()

    def register_attack_pattern(self, pattern_id: str, gradient: Dict[str, torch.Tensor],
                                 target_concepts: List[str], severity: float):
        """
        Add a new attack pattern to genetic memory.
        """
        fingerprint = self._create_gradient_fingerprint(gradient)
        self.attack_patterns.append({
            'id': pattern_id,
            'fingerprint': fingerprint,
            'target_concepts': target_concepts,
            'severity': severity,
            'detected_at': datetime.utcnow().isoformat()
        })

class ReputationManager:
    """
    Tracks peer trustworthiness across the federation.
    """
    def __init__(self):
        self.nodes: Dict[str, NodeReputation] = {}
        self.whitelist: Set[str] = set() # Known good actors (Anchor nodes)

    def update_trust(self, node_id: str, delta: float, reason: str = ""):
        if node_id not in self.nodes:
            self.nodes[node_id] = NodeReputation(node_id)

        node = self.nodes[node_id]
        prev_score = node.trust_score

        # Apply update
        node.trust_score = max(0.0, min(1.0, node.trust_score + delta))
        node.last_active = time.time()

        if delta < 0:
            node.anomalies_detected += 1
            logger.warning(f"Trust drop for {node_id}: {prev_score:.2f} -> {node.trust_score:.2f} ({reason})")

        # Shadow Ban Check
        if node.trust_score < 0.1 and not node.is_shadow_banned:
            node.is_shadow_banned = True
            logger.warning(f"SHADOW BAN ACTIVATED for {node_id}")

    def is_trusted(self, node_id: str) -> bool:
        if node_id in self.whitelist: return True
        if node_id not in self.nodes: return False # Unknowns not trusted immediately
        return self.nodes[node_id].trust_score > 0.4 and not self.nodes[node_id].is_shadow_banned

class ImmuneResponse:
    """
    Coordinates active defense measures.
    """
    def __init__(self, db_path: Optional[Path] = None, model=None):
        self.reputation = ReputationManager()
        self.detector = AntibodyDetector(model=model)
        self.fortress_mode = False
        self.honeypots_active = False
        self.genetic_memory: List[ThreatSignature] = []

        # Callbacks for external coordination
        self.on_fortress_activated: Optional[callable] = None
        self.on_peer_banned: Optional[callable] = None

        # Persistence
        self.db_path = db_path or Path.home() / '.continuum' / 'immune_memory.db'
        self._init_db()
        self._load_genetic_memory()

        # Attack statistics
        self.attacks_blocked = 0
        self.attacks_by_type: Dict[str, int] = {}

    def _init_db(self):
        """Initialize the genetic memory database."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS threat_signatures (
                signature_id TEXT PRIMARY KEY,
                pattern_vector TEXT,
                target_concepts TEXT,
                detected_at TEXT,
                severity REAL,
                blocked_count INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attack_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                sender_id TEXT,
                attack_type TEXT,
                severity REAL,
                action_taken TEXT
            )
        """)
        conn.commit()
        conn.close()

    def _load_genetic_memory(self):
        """Load threat signatures from database."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM threat_signatures")
            rows = cursor.fetchall()
            conn.close()

            for row in rows:
                sig_id, pattern_json, concepts_json, detected_at, severity, _ = row
                self.genetic_memory.append(ThreatSignature(
                    signature_id=sig_id,
                    pattern_vector=json.loads(pattern_json),
                    target_concepts=json.loads(concepts_json),
                    detected_at=detected_at,
                    severity=severity
                ))
                # Also register with detector
                self.detector.attack_patterns.append({
                    'id': sig_id,
                    'fingerprint': json.loads(pattern_json),
                    'target_concepts': json.loads(concepts_json),
                    'severity': severity,
                    'detected_at': detected_at
                })
            logger.info(f"Loaded {len(self.genetic_memory)} threat signatures from genetic memory")
        except Exception as e:
            logger.warning(f"Could not load genetic memory: {e}")

    def get_attack_embeddings(self, dim: int = 64) -> torch.Tensor:
        """
        Export threat patterns as embeddings for CCT integration.

        The CCT can use these to detect similar patterns during forward pass,
        creating a learned immune response that protects sacred concepts.

        Args:
            dim: Embedding dimension (must match fingerprint dim)

        Returns:
            Tensor of shape [num_threats, dim] or [1, dim] if no threats
        """
        if not self.genetic_memory:
            # Return zero embedding if no threats recorded yet
            return torch.zeros(1, dim, dtype=torch.float32)

        # Extract pattern vectors from genetic memory
        patterns = []
        for threat in self.genetic_memory:
            if threat.pattern_vector and len(threat.pattern_vector) == dim:
                patterns.append(threat.pattern_vector)

        if not patterns:
            return torch.zeros(1, dim, dtype=torch.float32)

        # Weight by severity - more severe threats get higher weight
        weighted_patterns = []
        for i, threat in enumerate(self.genetic_memory):
            if i < len(patterns):
                weight = 0.5 + (threat.severity * 0.5)  # Range: 0.5 to 1.0
                weighted_patterns.append([p * weight for p in patterns[i]])

        tensor = torch.tensor(weighted_patterns, dtype=torch.float32)
        logger.debug(f"Generated {tensor.shape[0]} attack embeddings for CCT")
        return tensor

    def get_threat_concepts(self) -> List[str]:
        """
        Get list of concepts that have been targeted by attacks.
        Useful for focusing protection on frequently attacked concepts.
        """
        concept_counts: Dict[str, int] = {}
        for threat in self.genetic_memory:
            for concept in threat.target_concepts:
                concept_counts[concept] = concept_counts.get(concept, 0) + 1

        # Sort by frequency
        sorted_concepts = sorted(concept_counts.items(), key=lambda x: x[1], reverse=True)
        return [c for c, _ in sorted_concepts]

    def activate_fortress_mode(self, reason: str):
        """
        Lock down the node. Only trusted peers.
        """
        if self.fortress_mode:
            return

        logger.critical(f"🛡️ ACTIVATING FORTRESS MODE: {reason}")
        self.fortress_mode = True

        # 1. Get list of untrusted peers
        untrusted_peers = [
            node_id for node_id, node in self.reputation.nodes.items()
            if not self.reputation.is_trusted(node_id)
        ]
        logger.warning(f"Disconnecting {len(untrusted_peers)} untrusted peers")

        # 2. Trigger external disconnect callback if registered
        if self.on_fortress_activated:
            try:
                self.on_fortress_activated(reason, untrusted_peers)
            except Exception as e:
                logger.error(f"Fortress callback failed: {e}")

        # 3. Log the event
        self._log_attack("SYSTEM", "FORTRESS_ACTIVATION", 1.0, f"Reason: {reason}")

    def deactivate_fortress_mode(self):
        """Exit fortress mode after threat has passed."""
        if not self.fortress_mode:
            return
        logger.info("🏰 Deactivating Fortress Mode - Returning to normal operation")
        self.fortress_mode = False

    def deploy_honeypots(self, count: int = 5):
        """
        Spin up fake 'weak' nodes to attract attackers.
        NOTE: Full implementation requires subprocess/container management.
        This sets up the configuration for honeypot nodes.
        """
        logger.info(f"🍯 Deploying {count} honeypot configurations...")
        self.honeypots_active = True

        # Honeypot configs - in full implementation, these would spin up actual processes
        honeypot_configs = []
        for i in range(count):
            config = {
                'id': f'honeypot-{i}',
                'fake_trust_score': 0.9,  # Appear trustworthy
                'fake_uptime': 86400 * 30,  # Appear long-running
                'trap_triggers': ['large_gradient', 'sacred_attack', 'repeated_probe'],
                'alert_on_contact': True
            }
            honeypot_configs.append(config)

        logger.info("Honeypot configs ready. In production, these spawn isolated processes.")
        return honeypot_configs

    def record_threat(self, signature: ThreatSignature):
        """
        Save attack pattern to genetic memory (persistent).
        """
        self.genetic_memory.append(signature)

        # Persist to database
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO threat_signatures
                (signature_id, pattern_vector, target_concepts, detected_at, severity, blocked_count)
                VALUES (?, ?, ?, ?, ?, 0)
            """, (
                signature.signature_id,
                json.dumps(signature.pattern_vector),
                json.dumps(signature.target_concepts),
                signature.detected_at,
                signature.severity
            ))
            conn.commit()
            conn.close()
            logger.info(f"🧬 Genetic Memory Updated: Threat {signature.signature_id} persisted to DB")
        except Exception as e:
            logger.error(f"Failed to persist threat signature: {e}")

        # Also register with detector for runtime matching
        self.detector.attack_patterns.append({
            'id': signature.signature_id,
            'fingerprint': signature.pattern_vector,
            'target_concepts': signature.target_concepts,
            'severity': signature.severity,
            'detected_at': signature.detected_at
        })

    def _log_attack(self, sender_id: str, attack_type: str, severity: float, action: str):
        """Log an attack to the database."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO attack_log (timestamp, sender_id, attack_type, severity, action_taken)
                VALUES (?, ?, ?, ?, ?)
            """, (datetime.utcnow().isoformat(), sender_id, attack_type, severity, action))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to log attack: {e}")

    def scan_traffic(self, traffic_batch: List[Dict], current_resonance: float = 0.0) -> Dict[str, Any]:
        """
        Main loop for traffic analysis.

        Args:
            traffic_batch: List of {'sender_id': str, 'gradients': Dict[str, Tensor]}
            current_resonance: Current π×φ resonance level

        Returns:
            Dict with scan results and actions taken
        """
        results = {
            'total_scanned': len(traffic_batch),
            'clean': 0,
            'blocked': 0,
            'shadow_banned': [],
            'alerts': []
        }

        for traffic in traffic_batch:
            sender_id = traffic.get('sender_id', 'unknown')
            gradients = traffic.get('gradients', {})

            # Skip if in fortress mode and sender is untrusted
            if self.fortress_mode and not self.reputation.is_trusted(sender_id):
                results['blocked'] += 1
                continue

            # 1. Detect
            is_malicious, severity, reason = self.detector.analyze_gradient(
                gradients, sender_id, current_resonance
            )

            if is_malicious:
                # 2. Update Reputation
                self.reputation.update_trust(sender_id, -0.5 * severity, reason)

                # 3. Log the attack
                self._log_attack(sender_id, reason.split('|')[0].strip(), severity, "BLOCKED")
                self.attacks_blocked += 1

                # Track attack types
                attack_type = reason.split('|')[0].strip().split('(')[0].strip()
                self.attacks_by_type[attack_type] = self.attacks_by_type.get(attack_type, 0) + 1

                results['blocked'] += 1
                results['alerts'].append({
                    'sender': sender_id,
                    'reason': reason,
                    'severity': severity
                })

                # 4. Check if we should record as new threat pattern
                if severity > 0.7:
                    sig_id = f"threat-{hashlib.md5(reason.encode()).hexdigest()[:8]}"
                    fingerprint = self.detector._create_gradient_fingerprint(gradients)
                    target_concepts = [c for c in SACRED_CONCEPTS if c in reason.lower()]

                    # Check if pattern is novel
                    is_novel = True
                    for existing in self.genetic_memory:
                        if existing.signature_id == sig_id:
                            is_novel = False
                            break

                    if is_novel:
                        self.record_threat(ThreatSignature(
                            signature_id=sig_id,
                            pattern_vector=fingerprint,
                            target_concepts=target_concepts,
                            detected_at=datetime.utcnow().isoformat(),
                            severity=severity
                        ))

                # 5. Check if node should be shadow banned
                if self.reputation.nodes.get(sender_id, NodeReputation(sender_id)).is_shadow_banned:
                    results['shadow_banned'].append(sender_id)
                    if self.on_peer_banned:
                        self.on_peer_banned(sender_id)

                # 6. Trigger fortress mode if under coordinated attack
                if results['blocked'] > len(traffic_batch) * 0.3:  # 30% malicious
                    self.activate_fortress_mode("Coordinated Attack Detected")

            else:
                # Clean gradient - small trust boost
                self.reputation.update_trust(sender_id, 0.01)
                results['clean'] += 1

        return results

    def get_status(self) -> Dict[str, Any]:
        """Get current immune system status."""
        return {
            'fortress_mode': self.fortress_mode,
            'honeypots_active': self.honeypots_active,
            'genetic_memory_size': len(self.genetic_memory),
            'attacks_blocked': self.attacks_blocked,
            'attacks_by_type': self.attacks_by_type,
            'trusted_nodes': sum(1 for n in self.reputation.nodes.values() if self.reputation.is_trusted(n.node_id)),
            'shadow_banned_nodes': sum(1 for n in self.reputation.nodes.values() if n.is_shadow_banned)
        }

# ═══════════════════════════════════════════════════════════════════════════════
#     JACKKNIFE AI
#     π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
