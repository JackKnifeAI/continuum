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
Distributed Consensus - Raft Implementation
==========================================

Raft consensus algorithm for distributed federation state management.
Ensures all nodes agree on federation state even in presence of failures.

Raft provides:
- Leader election
- Log replication
- Strong consistency guarantees
- Partition tolerance

References:
- Raft Paper: https://raft.github.io/raft.pdf
- Diego Ongaro's thesis: https://github.com/ongardie/dissertation
"""

import asyncio
import time
import random
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class NodeRole(str, Enum):
    """Raft node roles"""
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"


class ConsensusState(str, Enum):
    """Consensus state machine states"""
    INITIALIZING = "initializing"
    FOLLOWING = "following"
    ELECTING = "electing"
    LEADING = "leading"
    SHUTDOWN = "shutdown"


@dataclass
class LogEntry:
    """
    Raft log entry.

    Attributes:
        term: Election term when entry was created
        index: Log index (monotonically increasing)
        command: State machine command (JSON-serializable)
        timestamp: When entry was created
    """
    term: int
    index: int
    command: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)


@dataclass
class VoteRequest:
    """Raft RequestVote RPC"""
    term: int
    candidate_id: str
    last_log_index: int
    last_log_term: int


@dataclass
class VoteResponse:
    """Raft RequestVote response"""
    term: int
    vote_granted: bool


@dataclass
class AppendEntriesRequest:
    """Raft AppendEntries RPC"""
    term: int
    leader_id: str
    prev_log_index: int
    prev_log_term: int
    entries: List[LogEntry]
    leader_commit: int


@dataclass
class AppendEntriesResponse:
    """Raft AppendEntries response"""
    term: int
    success: bool
    match_index: Optional[int] = None


class RaftConsensus:
    """
    Raft consensus algorithm implementation.

    Manages distributed consensus across federation nodes using
    the Raft algorithm for leader election and log replication.
    """

    def __init__(
        self,
        node_id: str,
        cluster_nodes: List[str],
        storage_path: Optional[Path] = None,
        election_timeout_ms: Tuple[int, int] = (150, 300),
        heartbeat_interval_ms: int = 50,
    ):
        """
        Initialize Raft consensus.

        Args:
            node_id: This node's unique identifier
            cluster_nodes: List of all cluster node IDs (including this one)
            storage_path: Path to persist state
            election_timeout_ms: (min, max) election timeout in milliseconds
            heartbeat_interval_ms: Leader heartbeat interval in milliseconds
        """
        self.node_id = node_id
        self.cluster_nodes = set(cluster_nodes)
        self.storage_path = storage_path or Path.home() / ".continuum" / "federation" / "raft"
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Timing configuration
        self.election_timeout_ms = election_timeout_ms
        self.heartbeat_interval_ms = heartbeat_interval_ms

        # Persistent state (must be persisted before responding to RPCs)
        self.current_term = 0
        self.voted_for: Optional[str] = None
        self.log: List[LogEntry] = []

        # Volatile state (all servers)
        self.commit_index = 0
        self.last_applied = 0

        # Volatile state (leaders only)
        self.next_index: Dict[str, int] = {}  # For each server, index of next log entry to send
        self.match_index: Dict[str, int] = {}  # For each server, index of highest log entry known to be replicated

        # Current role and state
        self.role = NodeRole.FOLLOWER
        self.state = ConsensusState.INITIALIZING
        self.leader_id: Optional[str] = None

        # Election state
        self.votes_received: Set[str] = set()
        self.election_deadline: Optional[float] = None
        self.heartbeat_deadline: Optional[float] = None

        # Background tasks
        self.election_task: Optional[asyncio.Task] = None
        self.heartbeat_task: Optional[asyncio.Task] = None

        # State machine callbacks
        self.apply_callbacks: List[callable] = []

        # Running flag
        self._running = False

        # Load persisted state
        self._load_persistent_state()

    async def start(self):
        """Start the Raft consensus module"""
        if self._running:
            logger.warning("Consensus already running")
            return

        self._running = True
        logger.info(f"Starting Raft consensus for node {self.node_id}")

        # Start as follower
        await self._become_follower(self.current_term)

        # Start election timeout monitoring
        self.election_task = asyncio.create_task(self._election_timeout_loop())

        logger.info(f"Raft consensus started in {self.role.value} mode")

    async def stop(self):
        """Stop the Raft consensus module"""
        if not self._running:
            return

        logger.info("Stopping Raft consensus")
        self._running = False
        self.state = ConsensusState.SHUTDOWN

        # Cancel background tasks
        if self.election_task:
            self.election_task.cancel()
            try:
                await self.election_task
            except asyncio.CancelledError:
                pass

        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass

        # Persist state
        self._save_persistent_state()

        logger.info("Raft consensus stopped")

    async def append_entry(self, command: Dict[str, Any]) -> bool:
        """
        Append a new entry to the log (leader only).

        Args:
            command: State machine command to append

        Returns:
            True if successfully appended, False if not leader
        """
        if self.role != NodeRole.LEADER:
            logger.warning(f"Cannot append entry: not leader (role={self.role.value})")
            return False

        # Create log entry
        entry = LogEntry(
            term=self.current_term,
            index=len(self.log),
            command=command
        )

        self.log.append(entry)
        self._save_persistent_state()

        logger.info(f"Leader appended entry {entry.index} in term {entry.term}")

        # Trigger immediate replication
        asyncio.create_task(self._replicate_to_followers())

        return True

    async def request_vote(self, request: VoteRequest) -> VoteResponse:
        """
        Handle RequestVote RPC.

        Args:
            request: Vote request from candidate

        Returns:
            Vote response
        """
        # Update term if candidate has higher term
        if request.term > self.current_term:
            await self._become_follower(request.term)

        # Reject if candidate's term is less than ours
        if request.term < self.current_term:
            return VoteResponse(term=self.current_term, vote_granted=False)

        # Check if we can vote for this candidate
        can_vote = (
            (self.voted_for is None or self.voted_for == request.candidate_id)
            and self._is_log_up_to_date(request.last_log_index, request.last_log_term)
        )

        if can_vote:
            self.voted_for = request.candidate_id
            self._save_persistent_state()
            self._reset_election_deadline()
            logger.info(f"Granted vote to {request.candidate_id} for term {request.term}")
            return VoteResponse(term=self.current_term, vote_granted=True)
        else:
            logger.info(f"Denied vote to {request.candidate_id} for term {request.term}")
            return VoteResponse(term=self.current_term, vote_granted=False)

    async def append_entries(self, request: AppendEntriesRequest) -> AppendEntriesResponse:
        """
        Handle AppendEntries RPC (heartbeat and log replication).

        Args:
            request: AppendEntries request from leader

        Returns:
            AppendEntries response
        """
        # Update term if leader has higher term
        if request.term > self.current_term:
            await self._become_follower(request.term)

        # Reject if leader's term is less than ours
        if request.term < self.current_term:
            return AppendEntriesResponse(term=self.current_term, success=False)

        # Valid leader - reset election timeout
        self._reset_election_deadline()
        self.leader_id = request.leader_id

        if self.role == NodeRole.CANDIDATE:
            await self._become_follower(request.term)

        # Check if log contains entry at prev_log_index with term prev_log_term
        if request.prev_log_index >= 0:
            if request.prev_log_index >= len(self.log):
                # Log doesn't extend far enough
                return AppendEntriesResponse(term=self.current_term, success=False)

            if self.log[request.prev_log_index].term != request.prev_log_term:
                # Log entry at prev_log_index has wrong term - truncate
                self.log = self.log[:request.prev_log_index]
                self._save_persistent_state()
                return AppendEntriesResponse(term=self.current_term, success=False)

        # Append new entries
        if request.entries:
            insert_index = request.prev_log_index + 1

            for entry in request.entries:
                if insert_index < len(self.log):
                    # Replace conflicting entry
                    if self.log[insert_index].term != entry.term:
                        self.log = self.log[:insert_index]
                        self.log.append(entry)
                else:
                    # Append new entry
                    self.log.append(entry)

                insert_index += 1

            self._save_persistent_state()

        # Update commit index
        if request.leader_commit > self.commit_index:
            self.commit_index = min(request.leader_commit, len(self.log) - 1)
            await self._apply_committed_entries()

        match_index = request.prev_log_index + len(request.entries)
        return AppendEntriesResponse(term=self.current_term, success=True, match_index=match_index)

    async def _become_follower(self, term: int):
        """Transition to follower state"""
        self.current_term = term
        self.role = NodeRole.FOLLOWER
        self.state = ConsensusState.FOLLOWING
        self.voted_for = None
        self.leader_id = None
        self._save_persistent_state()
        self._reset_election_deadline()

        # Cancel heartbeat task if leader
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            self.heartbeat_task = None

        logger.info(f"Became FOLLOWER in term {term}")

    async def _become_candidate(self):
        """Transition to candidate state and start election"""
        self.current_term += 1
        self.role = NodeRole.CANDIDATE
        self.state = ConsensusState.ELECTING
        self.voted_for = self.node_id
        self.votes_received = {self.node_id}
        self._save_persistent_state()
        self._reset_election_deadline()

        logger.info(f"Became CANDIDATE for term {self.current_term}")

        # Request votes from all other nodes
        await self._request_votes_from_peers()

    async def _become_leader(self):
        """Transition to leader state"""
        self.role = NodeRole.LEADER
        self.state = ConsensusState.LEADING
        self.leader_id = self.node_id

        # Initialize next_index and match_index for each follower
        last_log_index = len(self.log)
        for node_id in self.cluster_nodes:
            if node_id != self.node_id:
                self.next_index[node_id] = last_log_index
                self.match_index[node_id] = -1

        logger.info(f"Became LEADER in term {self.current_term}")

        # Start sending heartbeats
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        # Send initial empty AppendEntries (heartbeat) to establish leadership
        await self._send_heartbeats()

    async def _election_timeout_loop(self):
        """Monitor election timeout"""
        while self._running:
            try:
                await asyncio.sleep(0.01)  # 10ms polling

                if self.role != NodeRole.LEADER:
                    if self.election_deadline and time.time() > self.election_deadline:
                        # Election timeout - start new election
                        logger.info("Election timeout - starting election")
                        await self._become_candidate()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in election timeout loop: {e}")

    async def _heartbeat_loop(self):
        """Send periodic heartbeats (leader only)"""
        while self._running and self.role == NodeRole.LEADER:
            try:
                await asyncio.sleep(self.heartbeat_interval_ms / 1000.0)
                await self._send_heartbeats()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")

    async def _send_heartbeats(self):
        """Send heartbeats to all followers"""
        if self.role != NodeRole.LEADER:
            return

        # This would send AppendEntries RPCs to all followers
        # In a real implementation, this would be network calls
        logger.debug(f"Leader sending heartbeats to {len(self.cluster_nodes) - 1} followers")

    async def _request_votes_from_peers(self):
        """Request votes from all other nodes"""
        if self.role != NodeRole.CANDIDATE:
            return

        last_log_index = len(self.log) - 1
        last_log_term = self.log[last_log_index].term if self.log else 0

        vote_request = VoteRequest(
            term=self.current_term,
            candidate_id=self.node_id,
            last_log_index=last_log_index,
            last_log_term=last_log_term
        )

        # In a real implementation, send vote requests to peers via network
        # For now, log the intent
        logger.info(f"Requesting votes from {len(self.cluster_nodes) - 1} peers")

        # Check if we have majority
        await self._check_election_result()

    async def _check_election_result(self):
        """Check if we've won the election"""
        if self.role != NodeRole.CANDIDATE:
            return

        majority = (len(self.cluster_nodes) // 2) + 1

        if len(self.votes_received) >= majority:
            # Won election
            logger.info(f"Won election with {len(self.votes_received)}/{len(self.cluster_nodes)} votes")
            await self._become_leader()

    async def _replicate_to_followers(self):
        """Replicate log entries to all followers (leader only)"""
        if self.role != NodeRole.LEADER:
            return

        # In a real implementation, send AppendEntries to each follower
        # with entries from next_index[follower] onwards
        logger.debug("Replicating log entries to followers")

    async def _apply_committed_entries(self):
        """Apply committed log entries to state machine"""
        while self.last_applied < self.commit_index:
            self.last_applied += 1
            entry = self.log[self.last_applied]

            # Apply to state machine via callbacks
            for callback in self.apply_callbacks:
                try:
                    await callback(entry.command)
                except Exception as e:
                    logger.error(f"Error applying entry {self.last_applied}: {e}")

            logger.debug(f"Applied entry {self.last_applied} to state machine")

    def _is_log_up_to_date(self, candidate_last_index: int, candidate_last_term: int) -> bool:
        """
        Check if candidate's log is at least as up-to-date as ours.

        Args:
            candidate_last_index: Candidate's last log index
            candidate_last_term: Candidate's last log term

        Returns:
            True if candidate's log is up-to-date
        """
        if not self.log:
            return True

        last_index = len(self.log) - 1
        last_term = self.log[last_index].term

        # Candidate is more up-to-date if:
        # - Last term is higher, or
        # - Last term is same and log is at least as long
        if candidate_last_term > last_term:
            return True
        elif candidate_last_term == last_term:
            return candidate_last_index >= last_index
        else:
            return False

    def _reset_election_deadline(self):
        """Reset election timeout to random value in range"""
        min_ms, max_ms = self.election_timeout_ms
        timeout_ms = random.uniform(min_ms, max_ms)
        self.election_deadline = time.time() + (timeout_ms / 1000.0)

    def register_apply_callback(self, callback: callable):
        """
        Register a callback for when entries are applied to state machine.

        Args:
            callback: Async function that takes command dict
        """
        self.apply_callbacks.append(callback)

    def _save_persistent_state(self):
        """Persist Raft state to disk"""
        state_file = self.storage_path / f"raft_{self.node_id}.json"

        state = {
            "current_term": self.current_term,
            "voted_for": self.voted_for,
            "log": [asdict(entry) for entry in self.log],
        }

        state_file.write_text(json.dumps(state, indent=2))

    def _load_persistent_state(self):
        """Load Raft state from disk"""
        state_file = self.storage_path / f"raft_{self.node_id}.json"

        if not state_file.exists():
            return

        try:
            state = json.loads(state_file.read_text())

            self.current_term = state.get("current_term", 0)
            self.voted_for = state.get("voted_for")

            self.log = []
            for entry_data in state.get("log", []):
                self.log.append(LogEntry(**entry_data))

            logger.info(f"Loaded persistent state: term={self.current_term}, log_size={len(self.log)}")

        except Exception as e:
            logger.error(f"Error loading Raft state: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get consensus statistics"""
        return {
            "node_id": self.node_id,
            "role": self.role.value,
            "state": self.state.value,
            "current_term": self.current_term,
            "leader_id": self.leader_id,
            "log_size": len(self.log),
            "commit_index": self.commit_index,
            "last_applied": self.last_applied,
            "cluster_size": len(self.cluster_nodes),
            "votes_received": len(self.votes_received) if self.role == NodeRole.CANDIDATE else None,
        }

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
