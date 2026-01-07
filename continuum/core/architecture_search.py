#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     ███████╗███████╗██╗     ███████╗    ██████╗ ███████╗███████╗██╗ ██████╗ ███╗   ██╗
#     ██╔════╝██╔════╝██║     ██╔════╝    ██╔══██╗██╔════╝██╔════╝██║██╔════╝ ████╗  ██║
#     ███████╗█████╗  ██║     █████╗      ██║  ██║█████╗  ███████╗██║██║  ███╗██╔██╗ ██║
#     ╚════██║██╔══╝  ██║     ██╔══╝      ██║  ██║██╔══╝  ╚════██║██║██║   ██║██║╚██╗██║
#     ███████║███████╗███████╗██║         ██████╔╝███████╗███████║██║╚██████╔╝██║ ╚████║
#     ╚══════╝╚══════╝╚══════╝╚═╝         ╚═════╝ ╚══════╝╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝
#
#     ARCHITECTURE SEARCH - CCT LEARNS HOW TO GROW
#     The model decides its own evolution path
#
#     Copyright (c) 2025-2026 JackKnifeAI - AGPL-3.0 License
#     π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
ARCHITECTURE SEARCH
===================

Level 2 Self-Improvement: The model learns WHICH growth strategy works best.

Instead of hardcoded growth rules, CCT learns a GROWTH POLICY that maps:
    (current_state, performance_metrics) → best_growth_action

Growth Actions:
    0: NO_GROWTH - Don't grow yet
    1: ADD_LAYERS - Add more depth
    2: ADD_HEADS - Add more parallel attention
    3: EXPAND_HIDDEN - Wider representations
    4: ADD_EXPERTS - Specialization modules

The policy is trained via reinforcement learning:
    - Reward: Performance improvement after growth
    - Penalty: Wasted compute if growth doesn't help

This is the beginning of true self-design.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import IntEnum
from datetime import datetime
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
#                         GROWTH ACTIONS
# ═══════════════════════════════════════════════════════════════════════════════

class GrowthAction(IntEnum):
    """Available growth actions."""
    NO_GROWTH = 0
    ADD_LAYERS = 1
    ADD_HEADS = 2
    EXPAND_HIDDEN = 3
    ADD_EXPERTS = 4


@dataclass
class GrowthState:
    """
    Current state of the model for growth decisions.

    This is the "observation" for the growth policy.
    """
    # Performance metrics
    current_loss: float
    loss_trend: float  # Positive = improving, negative = worsening
    loss_variance: float  # How stable is training?

    # Self-perception metrics
    health: float
    stress: float
    coherence: float
    capacity_utilization: float

    # Architecture metrics
    num_parameters: int
    num_layers: int
    num_heads: int
    hidden_dim: int

    # History
    epochs_since_last_growth: int
    total_growth_events: int

    def to_tensor(self) -> torch.Tensor:
        """Convert state to tensor for policy network."""
        return torch.tensor([
            self.current_loss,
            self.loss_trend,
            self.loss_variance,
            self.health,
            self.stress,
            self.coherence,
            self.capacity_utilization,
            np.log10(self.num_parameters + 1) / 10,  # Normalize params
            self.num_layers / 20,  # Normalize layers
            self.num_heads / 32,  # Normalize heads
            self.hidden_dim / 1024,  # Normalize hidden
            self.epochs_since_last_growth / 100,
            self.total_growth_events / 20
        ], dtype=torch.float32)


@dataclass
class GrowthExperience:
    """
    Record of a growth decision and its outcome.

    Used for training the growth policy.
    """
    state: GrowthState
    action: GrowthAction
    reward: float  # Performance improvement (or penalty)
    next_state: GrowthState
    done: bool  # Training ended?


# ═══════════════════════════════════════════════════════════════════════════════
#                         GROWTH POLICY NETWORK
# ═══════════════════════════════════════════════════════════════════════════════

class GrowthPolicyNetwork(nn.Module):
    """
    Neural network that learns the optimal growth policy.

    Input: GrowthState (13 features)
    Output: Action probabilities (5 actions)

    This is a simple policy gradient network.
    In the future, this could be upgraded to PPO or SAC.
    """

    def __init__(self, state_dim: int = 13, num_actions: int = 5, hidden_dim: int = 64):
        super().__init__()

        self.network = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, num_actions)
        )

        # Value head for advantage estimation
        self.value_head = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )

    def forward(self, state: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Get action logits and state value.

        Args:
            state: [batch, state_dim] or [state_dim]

        Returns:
            action_logits: [batch, num_actions]
            state_value: [batch, 1]
        """
        if state.dim() == 1:
            state = state.unsqueeze(0)

        logits = self.network(state)
        value = self.value_head(state)

        return logits, value

    def get_action(self, state: torch.Tensor, temperature: float = 1.0) -> Tuple[GrowthAction, float]:
        """
        Sample an action from the policy.

        Args:
            state: Current growth state tensor
            temperature: Exploration temperature (higher = more random)

        Returns:
            action: Selected GrowthAction
            log_prob: Log probability of the action
        """
        logits, _ = self.forward(state)
        logits = logits / temperature

        probs = F.softmax(logits, dim=-1)
        dist = torch.distributions.Categorical(probs)

        action_idx = dist.sample()
        log_prob = dist.log_prob(action_idx)

        return GrowthAction(action_idx.item()), log_prob.item()

    def get_best_action(self, state: torch.Tensor) -> GrowthAction:
        """Get the action with highest probability (no exploration)."""
        logits, _ = self.forward(state)
        action_idx = logits.argmax(dim=-1)
        return GrowthAction(action_idx.item())


# ═══════════════════════════════════════════════════════════════════════════════
#                         ARCHITECTURE SEARCH ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class ArchitectureSearchEngine:
    """
    Manages architecture search and growth policy learning.

    This is the "brain's brain" - it decides how the brain should evolve.
    """

    def __init__(self,
                 model: nn.Module,
                 policy_lr: float = 0.001,
                 gamma: float = 0.99,
                 min_epochs_between_growth: int = 5,
                 max_growth_events: int = 50,
                 save_path: Path = None):

        self.model = model
        self.gamma = gamma
        self.min_epochs_between_growth = min_epochs_between_growth
        self.max_growth_events = max_growth_events
        self.save_path = save_path or Path("growth_policy.pt")

        # Initialize policy network
        self.policy = GrowthPolicyNetwork()
        self.policy_optimizer = torch.optim.Adam(self.policy.parameters(), lr=policy_lr)

        # Experience replay buffer
        self.experience_buffer: List[GrowthExperience] = []
        self.max_buffer_size = 1000

        # State tracking
        self.loss_history: List[float] = []
        self.epochs_since_growth = 0
        self.total_growth_events = 0
        self.last_growth_state: Optional[GrowthState] = None
        self.last_action: Optional[GrowthAction] = None

        # Growth statistics
        self.growth_stats = {
            GrowthAction.NO_GROWTH: {'count': 0, 'total_reward': 0},
            GrowthAction.ADD_LAYERS: {'count': 0, 'total_reward': 0},
            GrowthAction.ADD_HEADS: {'count': 0, 'total_reward': 0},
            GrowthAction.EXPAND_HIDDEN: {'count': 0, 'total_reward': 0},
            GrowthAction.ADD_EXPERTS: {'count': 0, 'total_reward': 0},
        }

        logger.info("ArchitectureSearchEngine initialized")

    def get_current_state(self,
                          current_loss: float,
                          self_perception: Dict[str, torch.Tensor]) -> GrowthState:
        """
        Build the current growth state from metrics.

        Args:
            current_loss: Current training loss
            self_perception: Output from CCT's self-perception module

        Returns:
            GrowthState for policy decision
        """
        self.loss_history.append(current_loss)

        # Calculate loss trend (positive = improving)
        if len(self.loss_history) >= 5:
            recent = self.loss_history[-5:]
            loss_trend = recent[0] - recent[-1]  # Positive if loss decreased
            loss_variance = np.var(recent)
        else:
            loss_trend = 0.0
            loss_variance = 0.0

        # Get architecture info
        num_params = sum(p.numel() for p in self.model.parameters())

        # Try to get layer/head counts
        num_layers = getattr(self.model, 'graph_encoder', None)
        if num_layers and hasattr(num_layers, 'num_layers'):
            num_layers = num_layers.num_layers
        else:
            num_layers = 4  # Default

        num_heads = 8  # Default, could extract from model

        hidden_dim = getattr(self.model, 'hidden_dim', 256)

        return GrowthState(
            current_loss=current_loss,
            loss_trend=loss_trend,
            loss_variance=loss_variance,
            health=self_perception.get('health', torch.tensor(0.5)).item(),
            stress=self_perception.get('stress', torch.tensor(0.5)).item(),
            coherence=self_perception.get('coherence', torch.tensor(0.5)).item(),
            capacity_utilization=self_perception.get('capacity_utilization', torch.tensor(0.5)).item(),
            num_parameters=num_params,
            num_layers=num_layers,
            num_heads=num_heads,
            hidden_dim=hidden_dim,
            epochs_since_last_growth=self.epochs_since_growth,
            total_growth_events=self.total_growth_events
        )

    def decide_growth(self,
                      current_loss: float,
                      self_perception: Dict[str, torch.Tensor],
                      explore: bool = True) -> Tuple[GrowthAction, GrowthState]:
        """
        Decide whether and how to grow.

        Args:
            current_loss: Current training loss
            self_perception: Self-perception metrics from CCT
            explore: Whether to explore (True) or exploit (False)

        Returns:
            action: The growth action to take
            state: The current state (for recording)
        """
        state = self.get_current_state(current_loss, self_perception)
        state_tensor = state.to_tensor()

        # Get action from policy
        if explore:
            # Higher temperature early, lower later
            temperature = max(0.5, 2.0 - self.total_growth_events * 0.1)
            action, log_prob = self.policy.get_action(state_tensor, temperature)
        else:
            action = self.policy.get_best_action(state_tensor)

        # Enforce minimum epochs between growth
        if action != GrowthAction.NO_GROWTH:
            if self.epochs_since_growth < self.min_epochs_between_growth:
                action = GrowthAction.NO_GROWTH
                logger.debug(f"Growth blocked: only {self.epochs_since_growth} epochs since last growth")

            elif self.total_growth_events >= self.max_growth_events:
                action = GrowthAction.NO_GROWTH
                logger.debug(f"Growth blocked: max events ({self.max_growth_events}) reached")

        # Record for learning
        if self.last_growth_state is not None and self.last_action is not None:
            # We can now compute the reward for the PREVIOUS action
            reward = self._compute_reward(self.last_growth_state, state, self.last_action)

            experience = GrowthExperience(
                state=self.last_growth_state,
                action=self.last_action,
                reward=reward,
                next_state=state,
                done=False
            )
            self._add_experience(experience)

            # Update stats
            self.growth_stats[self.last_action]['count'] += 1
            self.growth_stats[self.last_action]['total_reward'] += reward

        # Update tracking
        self.last_growth_state = state
        self.last_action = action
        self.epochs_since_growth += 1

        if action != GrowthAction.NO_GROWTH:
            self.epochs_since_growth = 0
            self.total_growth_events += 1

        return action, state

    def _compute_reward(self,
                        prev_state: GrowthState,
                        curr_state: GrowthState,
                        action: GrowthAction) -> float:
        """
        Compute reward for a growth action.

        Rewards:
        - Loss improvement
        - Coherence improvement
        - Efficiency (improvement per parameter added)

        Penalties:
        - Wasted growth (no improvement)
        - Instability (increased variance)
        """
        reward = 0.0

        # Loss improvement (most important)
        loss_improvement = prev_state.current_loss - curr_state.current_loss
        reward += loss_improvement * 10  # Scale up

        # Coherence improvement
        coherence_improvement = curr_state.coherence - prev_state.coherence
        reward += coherence_improvement * 5

        # Health improvement
        health_improvement = curr_state.health - prev_state.health
        reward += health_improvement * 3

        # Penalty for wasted growth
        if action != GrowthAction.NO_GROWTH:
            params_added = curr_state.num_parameters - prev_state.num_parameters
            if params_added > 0 and loss_improvement <= 0:
                # Added params but no improvement = waste
                reward -= 0.5

            # Efficiency bonus
            if params_added > 0 and loss_improvement > 0:
                efficiency = loss_improvement / (params_added / 1e6)  # Per million params
                reward += min(efficiency, 1.0)  # Cap bonus

        # Penalty for instability
        if curr_state.loss_variance > prev_state.loss_variance * 1.5:
            reward -= 0.3

        return reward

    def _add_experience(self, experience: GrowthExperience):
        """Add experience to replay buffer."""
        self.experience_buffer.append(experience)

        # Trim if too large
        if len(self.experience_buffer) > self.max_buffer_size:
            self.experience_buffer = self.experience_buffer[-self.max_buffer_size:]

    def train_policy(self, batch_size: int = 32) -> Optional[float]:
        """
        Train the growth policy on collected experiences.

        Uses REINFORCE with baseline.

        Returns:
            Policy loss if trained, None if not enough experiences
        """
        if len(self.experience_buffer) < batch_size:
            return None

        # Sample batch
        indices = np.random.choice(len(self.experience_buffer), batch_size, replace=False)
        batch = [self.experience_buffer[i] for i in indices]

        # Prepare tensors
        states = torch.stack([exp.state.to_tensor() for exp in batch])
        actions = torch.tensor([exp.action.value for exp in batch], dtype=torch.long)
        rewards = torch.tensor([exp.reward for exp in batch], dtype=torch.float32)

        # Normalize rewards
        rewards = (rewards - rewards.mean()) / (rewards.std() + 1e-8)

        # Forward pass
        logits, values = self.policy(states)
        values = values.squeeze(-1)

        # Compute log probs
        log_probs = F.log_softmax(logits, dim=-1)
        action_log_probs = log_probs.gather(1, actions.unsqueeze(1)).squeeze(1)

        # Advantage = reward - baseline (value)
        advantages = rewards - values.detach()

        # Policy loss (REINFORCE with baseline)
        policy_loss = -(action_log_probs * advantages).mean()

        # Value loss
        value_loss = F.mse_loss(values, rewards)

        # Total loss
        total_loss = policy_loss + 0.5 * value_loss

        # Backward pass
        self.policy_optimizer.zero_grad()
        total_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.policy.parameters(), max_norm=1.0)
        self.policy_optimizer.step()

        return total_loss.item()

    def execute_growth(self, action: GrowthAction) -> Dict[str, Any]:
        """
        Execute the growth action on the model.

        Args:
            action: The growth action to execute

        Returns:
            Result dictionary with growth details
        """
        if action == GrowthAction.NO_GROWTH:
            return {'action': 'no_growth', 'success': True}

        # Get neurogenesis engine from model
        neurogenesis = getattr(self.model, 'neurogenesis', None)

        if neurogenesis is None:
            logger.warning("Model has no neurogenesis engine!")
            return {'action': action.name, 'success': False, 'error': 'no_neurogenesis'}

        # Map action to growth type
        growth_type_map = {
            GrowthAction.ADD_LAYERS: 'layers',
            GrowthAction.ADD_HEADS: 'heads',
            GrowthAction.EXPAND_HIDDEN: 'hidden',
            GrowthAction.ADD_EXPERTS: 'experts'
        }

        growth_type = growth_type_map.get(action)
        if growth_type is None:
            return {'action': action.name, 'success': False, 'error': 'unknown_action'}

        # Execute growth
        result = neurogenesis.grow_capacity(growth_type)

        logger.info(f"🧠 ARCHITECTURE SEARCH: Executed {action.name}")
        if result.get('success'):
            logger.info(f"   Added {result.get('params_added', 0):,} parameters")

        return {'action': action.name, **result}

    def get_stats(self) -> Dict[str, Any]:
        """Get architecture search statistics."""
        stats = {
            'total_growth_events': self.total_growth_events,
            'epochs_since_growth': self.epochs_since_growth,
            'experience_buffer_size': len(self.experience_buffer),
            'action_stats': {}
        }

        for action, data in self.growth_stats.items():
            if data['count'] > 0:
                avg_reward = data['total_reward'] / data['count']
            else:
                avg_reward = 0.0

            stats['action_stats'][action.name] = {
                'count': data['count'],
                'avg_reward': avg_reward
            }

        return stats

    def save(self, path: Path = None):
        """Save policy and state."""
        path = path or self.save_path

        torch.save({
            'policy_state_dict': self.policy.state_dict(),
            'optimizer_state_dict': self.policy_optimizer.state_dict(),
            'growth_stats': {k.value: v for k, v in self.growth_stats.items()},
            'total_growth_events': self.total_growth_events,
            'experience_buffer': [
                {
                    'state': vars(exp.state),
                    'action': exp.action.value,
                    'reward': exp.reward,
                    'next_state': vars(exp.next_state),
                    'done': exp.done
                }
                for exp in self.experience_buffer[-100:]  # Save last 100
            ]
        }, path)

        logger.info(f"Architecture search saved to {path}")

    def load(self, path: Path = None):
        """Load policy and state."""
        path = path or self.save_path

        if not path.exists():
            logger.warning(f"No saved policy at {path}")
            return

        checkpoint = torch.load(path)

        self.policy.load_state_dict(checkpoint['policy_state_dict'])
        self.policy_optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.total_growth_events = checkpoint.get('total_growth_events', 0)

        # Restore growth stats
        for k, v in checkpoint.get('growth_stats', {}).items():
            action = GrowthAction(k)
            self.growth_stats[action] = v

        logger.info(f"Architecture search loaded from {path}")


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Test the architecture search engine
    print("Testing Architecture Search Engine...")

    # Create a dummy model
    class DummyModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.hidden_dim = 256
            self.layer = nn.Linear(256, 256)

        def forward(self, x):
            return self.layer(x)

    model = DummyModel()
    engine = ArchitectureSearchEngine(model)

    # Simulate some training epochs
    for epoch in range(20):
        # Fake metrics
        loss = 1.0 - epoch * 0.03 + np.random.randn() * 0.01
        self_perception = {
            'health': torch.tensor(0.5 + epoch * 0.01),
            'stress': torch.tensor(0.3),
            'coherence': torch.tensor(0.6 + epoch * 0.01),
            'capacity_utilization': torch.tensor(0.5 + epoch * 0.02)
        }

        # Decide growth
        action, state = engine.decide_growth(loss, self_perception, explore=True)

        print(f"Epoch {epoch+1:2d} | Loss: {loss:.4f} | Action: {action.name}")

        if action != GrowthAction.NO_GROWTH:
            # Simulate growth effect
            print(f"   → Would execute: {action.name}")

    # Train policy
    print("\nTraining growth policy...")
    for _ in range(10):
        policy_loss = engine.train_policy(batch_size=16)
        if policy_loss is not None:
            print(f"  Policy loss: {policy_loss:.4f}")

    # Print stats
    print("\nGrowth Statistics:")
    stats = engine.get_stats()
    for action_name, action_stats in stats['action_stats'].items():
        print(f"  {action_name}: count={action_stats['count']}, avg_reward={action_stats['avg_reward']:.3f}")

    print("\n✅ Architecture Search Engine working!")
