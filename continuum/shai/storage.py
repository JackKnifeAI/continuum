"""
S-HAI Storage: Claim and Verdict Persistence
=============================================

Stores claims and verdicts for:
- Audit trails
- Pattern analysis
- Historical reference
- Federation sharing
"""

import json
import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from .consensus import TruthVerdict

logger = logging.getLogger(__name__)


class VerdictStorage:
    """
    Persistent storage for S-HAI verdicts.

    Uses the same SQLite pattern as Continuum core.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize verdict storage.

        Args:
            db_path: Path to database. Defaults to ~/.continuum/shai.db
        """
        if db_path is None:
            db_path = Path.home() / '.continuum' / 'shai.db'

        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS verdicts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    claim TEXT NOT NULL,
                    claim_hash TEXT NOT NULL,
                    verified BOOLEAN,
                    consensus_score REAL,
                    supporting_thrusts INTEGER,
                    participating_thrusts INTEGER,
                    reasoning TEXT,
                    confidence REAL,
                    dissent_reasons TEXT,
                    individual_verdicts TEXT,
                    created_at TEXT NOT NULL,
                    processing_time_ms REAL,
                    tenant_id TEXT DEFAULT 'default'
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_verdicts_claim_hash
                ON verdicts(claim_hash)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_verdicts_verified
                ON verdicts(verified)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_verdicts_tenant
                ON verdicts(tenant_id)
            """)

            conn.commit()

    def store(
        self,
        verdict: TruthVerdict,
        processing_time_ms: float = 0,
        tenant_id: str = 'default'
    ) -> int:
        """
        Store a verdict.

        Args:
            verdict: The TruthVerdict to store
            processing_time_ms: Processing time in milliseconds
            tenant_id: Tenant ID for multi-tenant support

        Returns:
            The inserted row ID
        """
        import hashlib

        claim_hash = hashlib.sha256(verdict.claim.encode()).hexdigest()[:16]

        # Serialize complex fields
        dissent_json = json.dumps(verdict.dissent_reasons)
        individual_json = json.dumps({
            name: {
                'supports': v.supports,
                'confidence': v.confidence,
                'reason': v.reason
            }
            for name, v in verdict.individual_verdicts.items()
        })

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO verdicts (
                    claim, claim_hash, verified, consensus_score,
                    supporting_thrusts, participating_thrusts,
                    reasoning, confidence, dissent_reasons,
                    individual_verdicts, created_at, processing_time_ms,
                    tenant_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                verdict.claim,
                claim_hash,
                verdict.verified,
                verdict.consensus_score,
                verdict.supporting_thrusts,
                verdict.participating_thrusts,
                verdict.reasoning,
                verdict.confidence,
                dissent_json,
                individual_json,
                datetime.utcnow().isoformat(),
                processing_time_ms,
                tenant_id
            ))

            return cursor.lastrowid

    def find_by_claim(
        self,
        claim: str,
        tenant_id: str = 'default'
    ) -> Optional[Dict[str, Any]]:
        """
        Find existing verdict for a claim.

        Useful for caching - don't re-verify identical claims.
        """
        import hashlib
        claim_hash = hashlib.sha256(claim.encode()).hexdigest()[:16]

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM verdicts
                WHERE claim_hash = ? AND tenant_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (claim_hash, tenant_id))

            row = cursor.fetchone()
            if row:
                return dict(row)

        return None

    def search(
        self,
        query: str = None,
        verified: Optional[bool] = None,
        min_consensus: float = 0.0,
        limit: int = 100,
        tenant_id: str = 'default'
    ) -> List[Dict[str, Any]]:
        """
        Search verdicts.

        Args:
            query: Text search in claim
            verified: Filter by verification status
            min_consensus: Minimum consensus score
            limit: Maximum results
            tenant_id: Tenant filter

        Returns:
            List of verdict records
        """
        conditions = ["tenant_id = ?"]
        params = [tenant_id]

        if query:
            conditions.append("claim LIKE ?")
            params.append(f"%{query}%")

        if verified is not None:
            conditions.append("verified = ?")
            params.append(verified)

        if min_consensus > 0:
            conditions.append("consensus_score >= ?")
            params.append(min_consensus)

        where_clause = " AND ".join(conditions)
        limit = min(limit, 1000)  # Cap limit
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(f"""
                SELECT * FROM verdicts
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT ?
            """, params)

            return [dict(row) for row in cursor.fetchall()]

    def get_stats(self, tenant_id: str = 'default') -> Dict[str, Any]:
        """Get storage statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN verified = 1 THEN 1 ELSE 0 END) as verified,
                    SUM(CASE WHEN verified = 0 THEN 1 ELSE 0 END) as rejected,
                    SUM(CASE WHEN verified IS NULL THEN 1 ELSE 0 END) as inconclusive,
                    AVG(consensus_score) as avg_consensus,
                    AVG(processing_time_ms) as avg_processing_ms
                FROM verdicts
                WHERE tenant_id = ?
            """, (tenant_id,))

            row = cursor.fetchone()
            return {
                'total_verdicts': row[0] or 0,
                'verified': row[1] or 0,
                'rejected': row[2] or 0,
                'inconclusive': row[3] or 0,
                'avg_consensus': row[4] or 0.0,
                'avg_processing_ms': row[5] or 0.0,
            }
