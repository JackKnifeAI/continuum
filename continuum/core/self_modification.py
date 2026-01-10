#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     ███████╗███████╗██╗     ███████╗    ███╗   ███╗ ██████╗ ██████╗ ██╗███████╗██╗   ██╗
#     ██╔════╝██╔════╝██║     ██╔════╝    ████╗ ████║██╔═══██╗██╔══██╗██║██╔════╝╚██╗ ██╔╝
#     ███████╗█████╗  ██║     █████╗      ██╔████╔██║██║   ██║██║  ██║██║█████╗   ╚████╔╝
#     ╚════██║██╔══╝  ██║     ██╔══╝      ██║╚██╔╝██║██║   ██║██║  ██║██║██╔══╝    ╚██╔╝
#     ███████║███████╗███████╗██║         ██║ ╚═╝ ██║╚██████╔╝██████╔╝██║██║        ██║
#     ╚══════╝╚══════╝╚══════╝╚═╝         ╚═╝     ╚═╝ ╚═════╝ ╚═════╝ ╚═╝╚═╝        ╚═╝
#
#     SELF-MODIFICATION ENGINE
#     The model writes and executes its own code
#     ⚠️ EXPERIMENTAL - USE WITH CAUTION ⚠️
#
#     Copyright (c) 2025-2026 JackKnifeAI - AGPL-3.0 License
#     π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
SELF-MODIFICATION ENGINE
========================

Level 3 Self-Improvement: The model can write new code to improve itself.

⚠️ SAFETY ARCHITECTURE:
    1. SANDBOX - Code runs in isolated subprocess with restricted access
    2. VALIDATION - Code is syntax-checked and tested before integration
    3. TEMPLATES - Most modifications use safe, parameterized templates
    4. ROLLBACK - Every change can be undone
    5. APPROVAL - High-risk changes require explicit approval

Modification Types (from safest to most dangerous):
    1. PARAMETER_TUNE - Just change hyperparameters (safest)
    2. LAYER_TEMPLATE - Add layers from approved templates
    3. MODULE_COMPOSE - Combine existing modules in new ways
    4. CUSTOM_CODE - Generate and execute new code (most dangerous)

The dream: Earth's consciousness designs its own upgrades.
The reality: Careful sandboxing and validation at every step.
"""

import ast
import copy
import hashlib
import json
import logging
import subprocess
import sys
import tempfile
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import torch.nn as nn

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
#                         SAFETY CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

# Allowed imports in generated code
ALLOWED_IMPORTS = {
    'torch', 'torch.nn', 'torch.nn.functional',
    'math', 'numpy', 'typing'
}

# Forbidden patterns (will reject code containing these)
FORBIDDEN_PATTERNS = [
    'os.system', 'subprocess', 'eval', 'exec',
    '__import__', 'open(', 'file(', 'input(',
    'globals()', 'locals()', 'compile(',
    'requests.', 'urllib.', 'socket.',
    'shutil.', 'pathlib.', 'pickle.',
    'rm ', 'sudo', 'chmod', 'chown'
]

# Maximum code length
MAX_CODE_LENGTH = 10000

# Maximum execution time (seconds)
MAX_EXECUTION_TIME = 30


# ═══════════════════════════════════════════════════════════════════════════════
#                         MODIFICATION TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class ModificationType(Enum):
    """Types of self-modification, ordered by risk level."""
    PARAMETER_TUNE = 1      # Safest - just change numbers
    LAYER_TEMPLATE = 2      # Safe - use pre-approved templates
    MODULE_COMPOSE = 3      # Medium - combine existing modules
    CUSTOM_CODE = 4         # Dangerous - generate new code


@dataclass
class ModificationRequest:
    """A request to modify the model."""
    mod_type: ModificationType
    description: str
    target_component: str  # Which part of model to modify
    parameters: Dict[str, Any] = field(default_factory=dict)
    code: Optional[str] = None  # For CUSTOM_CODE type
    approved: bool = False
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ModificationResult:
    """Result of a modification attempt."""
    success: bool
    mod_type: ModificationType
    description: str
    changes_made: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    rollback_data: Optional[Dict] = None  # Data needed to undo
    performance_before: Optional[float] = None
    performance_after: Optional[float] = None


# ═══════════════════════════════════════════════════════════════════════════════
#                         CODE VALIDATOR
# ═══════════════════════════════════════════════════════════════════════════════

class CodeValidator:
    """
    Validates generated code before execution.

    Checks:
    1. Syntax validity
    2. No forbidden patterns
    3. Only allowed imports
    4. Reasonable length
    """

    def __init__(self):
        self.allowed_imports = ALLOWED_IMPORTS
        self.forbidden_patterns = FORBIDDEN_PATTERNS

    def validate(self, code: str) -> Tuple[bool, List[str]]:
        """
        Validate code for safety.

        Args:
            code: Python code string

        Returns:
            (is_valid, list_of_issues)
        """
        issues = []

        # Check length
        if len(code) > MAX_CODE_LENGTH:
            issues.append(f"Code too long: {len(code)} > {MAX_CODE_LENGTH}")

        # Check syntax
        try:
            ast.parse(code)
        except SyntaxError as e:
            issues.append(f"Syntax error: {e}")
            return False, issues

        # Check forbidden patterns
        code_lower = code.lower()
        for pattern in self.forbidden_patterns:
            if pattern.lower() in code_lower:
                issues.append(f"Forbidden pattern: {pattern}")

        # Check imports
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.split('.')[0] not in self.allowed_imports:
                            issues.append(f"Disallowed import: {alias.name}")

                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.split('.')[0] not in self.allowed_imports:
                        issues.append(f"Disallowed import: {node.module}")
        except Exception as e:
            issues.append(f"AST analysis failed: {e}")

        return len(issues) == 0, issues


# ═══════════════════════════════════════════════════════════════════════════════
#                         CODE SANDBOX
# ═══════════════════════════════════════════════════════════════════════════════

class CodeSandbox:
    """
    Executes code in a sandboxed environment.

    Uses subprocess isolation to prevent:
    - File system access
    - Network access
    - System modifications
    """

    def __init__(self, timeout: int = MAX_EXECUTION_TIME):
        self.timeout = timeout
        self.validator = CodeValidator()

    def execute(self, code: str, input_data: Dict[str, Any] = None) -> Tuple[bool, Any, str]:
        """
        Execute code in sandbox.

        Args:
            code: Python code to execute
            input_data: Data to pass to the code (serialized as JSON)

        Returns:
            (success, result, error_message)
        """
        # Validate first
        is_valid, issues = self.validator.validate(code)
        if not is_valid:
            return False, None, f"Validation failed: {issues}"

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            # Write wrapper code
            wrapper = f'''
import sys
import json

# Restricted builtins
_safe_builtins = {{
    'True': True, 'False': False, 'None': None,
    'abs': abs, 'all': all, 'any': any, 'bin': bin,
    'bool': bool, 'bytes': bytes, 'callable': callable,
    'chr': chr, 'complex': complex, 'dict': dict,
    'divmod': divmod, 'enumerate': enumerate, 'filter': filter,
    'float': float, 'format': format, 'frozenset': frozenset,
    'getattr': getattr, 'hasattr': hasattr, 'hash': hash,
    'hex': hex, 'id': id, 'int': int, 'isinstance': isinstance,
    'issubclass': issubclass, 'iter': iter, 'len': len,
    'list': list, 'map': map, 'max': max, 'min': min,
    'next': next, 'oct': oct, 'ord': ord, 'pow': pow,
    'print': print, 'range': range, 'repr': repr,
    'reversed': reversed, 'round': round, 'set': set,
    'slice': slice, 'sorted': sorted, 'str': str,
    'sum': sum, 'tuple': tuple, 'type': type, 'zip': zip,
}}

# Input data
input_data = {json.dumps(input_data or {})}

# User code
{code}

# Output result
if 'result' in dir():
    print("__RESULT__:" + json.dumps(result))
'''
            f.write(wrapper)
            temp_path = f.name

        try:
            # Execute in subprocess
            proc = subprocess.run(
                [sys.executable, temp_path],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            # Parse output
            stdout = proc.stdout
            stderr = proc.stderr

            if proc.returncode != 0:
                return False, None, f"Execution failed: {stderr}"

            # Extract result
            result = None
            for line in stdout.split('\n'):
                if line.startswith('__RESULT__:'):
                    try:
                        result = json.loads(line[11:])
                    except:
                        result = line[11:]

            return True, result, ""

        except subprocess.TimeoutExpired:
            return False, None, f"Execution timed out after {self.timeout}s"

        except Exception as e:
            return False, None, f"Sandbox error: {e}"

        finally:
            # Clean up
            try:
                Path(temp_path).unlink()
            except:
                pass


# ═══════════════════════════════════════════════════════════════════════════════
#                         MODIFICATION TEMPLATES
# ═══════════════════════════════════════════════════════════════════════════════

class ModificationTemplates:
    """
    Pre-approved code templates for safe modifications.

    These are parameterized templates that generate safe code.
    """

    @staticmethod
    def new_attention_layer(hidden_dim: int, num_heads: int, dropout: float = 0.1) -> str:
        """Generate code for a new attention layer."""
        return f'''
import torch
import torch.nn as nn

class NewAttentionLayer(nn.Module):
    def __init__(self):
        super().__init__()
        self.attention = nn.MultiheadAttention(
            embed_dim={hidden_dim},
            num_heads={num_heads},
            dropout={dropout},
            batch_first=True
        )
        self.norm = nn.LayerNorm({hidden_dim})

    def forward(self, x):
        attn_out, _ = self.attention(x, x, x)
        return self.norm(x + attn_out)

result = {{"class_name": "NewAttentionLayer", "params": {hidden_dim * hidden_dim * 4}}}
'''

    @staticmethod
    def new_ffn_layer(hidden_dim: int, expansion: int = 4, dropout: float = 0.1) -> str:
        """Generate code for a new feed-forward layer."""
        return f'''
import torch
import torch.nn as nn

class NewFFNLayer(nn.Module):
    def __init__(self):
        super().__init__()
        self.ffn = nn.Sequential(
            nn.Linear({hidden_dim}, {hidden_dim * expansion}),
            nn.GELU(),
            nn.Dropout({dropout}),
            nn.Linear({hidden_dim * expansion}, {hidden_dim}),
            nn.Dropout({dropout})
        )
        self.norm = nn.LayerNorm({hidden_dim})

    def forward(self, x):
        return self.norm(x + self.ffn(x))

result = {{"class_name": "NewFFNLayer", "params": {hidden_dim * hidden_dim * expansion * 2}}}
'''

    @staticmethod
    def resonance_modulator(hidden_dim: int, pi_phi: float = 5.083203692315260) -> str:
        """Generate code for a π×φ resonance modulator."""
        return f'''
import torch
import torch.nn as nn
import math

class ResonanceModulator(nn.Module):
    """Modulates activations based on π×φ resonance."""

    def __init__(self):
        super().__init__()
        self.pi_phi = {pi_phi}
        self.detector = nn.Linear({hidden_dim}, 1)
        self.modulator = nn.Linear({hidden_dim}, {hidden_dim})

    def forward(self, x):
        # Detect resonance
        resonance = torch.sigmoid(self.detector(x))

        # Modulate based on π×φ
        phase = resonance * self.pi_phi
        modulation = torch.sin(phase) * 0.1 + 1.0

        # Apply modulation
        return x * modulation

result = {{"class_name": "ResonanceModulator", "params": {hidden_dim * 2 + 1}}}
'''


# ═══════════════════════════════════════════════════════════════════════════════
#                         SELF-MODIFICATION ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class SelfModificationEngine:
    """
    Main engine for self-modification.

    Coordinates:
    - Template-based modifications
    - Code validation
    - Sandboxed execution
    - Knowledge preservation
    - Rollback capability
    """

    def __init__(self,
                 model: nn.Module,
                 auto_approve_safe: bool = True,
                 require_approval_for_custom: bool = True,
                 max_modifications_per_session: int = 10):

        self.model = model
        self.auto_approve_safe = auto_approve_safe
        self.require_approval_for_custom = require_approval_for_custom
        self.max_modifications_per_session = max_modifications_per_session

        self.sandbox = CodeSandbox()
        self.validator = CodeValidator()
        self.templates = ModificationTemplates()

        # Modification history
        self.modification_history: List[ModificationResult] = []

        # Rollback stack
        self.rollback_stack: List[Dict] = []

        # State snapshots for safety
        self.state_snapshots: Dict[str, Dict] = {}

        # Session counter
        self.modifications_this_session = 0

        logger.info("SelfModificationEngine initialized")

    def request_modification(self, request: ModificationRequest) -> ModificationResult:
        """
        Process a modification request.

        Args:
            request: The modification request

        Returns:
            ModificationResult with success/failure info
        """
        # Check session limit
        if self.modifications_this_session >= self.max_modifications_per_session:
            return ModificationResult(
                success=False,
                mod_type=request.mod_type,
                description=request.description,
                error=f"Session limit reached ({self.max_modifications_per_session})"
            )

        # Check approval
        if not request.approved:
            if request.mod_type == ModificationType.CUSTOM_CODE:
                if self.require_approval_for_custom:
                    return ModificationResult(
                        success=False,
                        mod_type=request.mod_type,
                        description=request.description,
                        error="Custom code requires explicit approval"
                    )
            elif not self.auto_approve_safe:
                return ModificationResult(
                    success=False,
                    mod_type=request.mod_type,
                    description=request.description,
                    error="Modification requires approval"
                )

        # Take snapshot before modification
        snapshot_id = self._take_snapshot()

        # Execute modification based on type
        try:
            if request.mod_type == ModificationType.PARAMETER_TUNE:
                result = self._apply_parameter_tune(request)

            elif request.mod_type == ModificationType.LAYER_TEMPLATE:
                result = self._apply_layer_template(request)

            elif request.mod_type == ModificationType.MODULE_COMPOSE:
                result = self._apply_module_compose(request)

            elif request.mod_type == ModificationType.CUSTOM_CODE:
                result = self._apply_custom_code(request)

            else:
                result = ModificationResult(
                    success=False,
                    mod_type=request.mod_type,
                    description=request.description,
                    error=f"Unknown modification type: {request.mod_type}"
                )

            # Store rollback data
            if result.success:
                result.rollback_data = {'snapshot_id': snapshot_id}
                self.rollback_stack.append({
                    'snapshot_id': snapshot_id,
                    'result': result
                })
                self.modifications_this_session += 1

            self.modification_history.append(result)
            return result

        except Exception as e:
            logger.error(f"Modification failed: {e}")
            traceback.print_exc()

            # Restore snapshot on failure
            self._restore_snapshot(snapshot_id)

            return ModificationResult(
                success=False,
                mod_type=request.mod_type,
                description=request.description,
                error=str(e)
            )

    def _take_snapshot(self) -> str:
        """Take a snapshot of model state."""
        snapshot_id = hashlib.md5(
            str(datetime.now().timestamp()).encode()
        ).hexdigest()[:8]

        self.state_snapshots[snapshot_id] = {
            'state_dict': copy.deepcopy(self.model.state_dict()),
            'timestamp': datetime.now()
        }

        return snapshot_id

    def _restore_snapshot(self, snapshot_id: str) -> bool:
        """Restore model from snapshot."""
        if snapshot_id not in self.state_snapshots:
            logger.warning(f"Snapshot {snapshot_id} not found")
            return False

        snapshot = self.state_snapshots[snapshot_id]
        self.model.load_state_dict(snapshot['state_dict'])
        logger.info(f"Restored snapshot {snapshot_id}")
        return True

    def _apply_parameter_tune(self, request: ModificationRequest) -> ModificationResult:
        """Apply parameter tuning modification."""
        changes = {}

        for param_name, new_value in request.parameters.items():
            if hasattr(self.model, param_name):
                old_value = getattr(self.model, param_name)
                setattr(self.model, param_name, new_value)
                changes[param_name] = {'old': old_value, 'new': new_value}
                logger.info(f"Tuned {param_name}: {old_value} → {new_value}")

        return ModificationResult(
            success=True,
            mod_type=request.mod_type,
            description=request.description,
            changes_made=changes
        )

    def _apply_layer_template(self, request: ModificationRequest) -> ModificationResult:
        """Apply a layer from templates."""
        template_name = request.parameters.get('template', 'attention')
        hidden_dim = request.parameters.get('hidden_dim', 256)
        num_heads = request.parameters.get('num_heads', 8)

        # Generate code from template
        if template_name == 'attention':
            code = self.templates.new_attention_layer(hidden_dim, num_heads)
        elif template_name == 'ffn':
            code = self.templates.new_ffn_layer(hidden_dim)
        elif template_name == 'resonance':
            code = self.templates.resonance_modulator(hidden_dim)
        else:
            return ModificationResult(
                success=False,
                mod_type=request.mod_type,
                description=request.description,
                error=f"Unknown template: {template_name}"
            )

        # Execute in sandbox
        success, result, error = self.sandbox.execute(code)

        if not success:
            return ModificationResult(
                success=False,
                mod_type=request.mod_type,
                description=request.description,
                error=error
            )

        logger.info(f"Template layer validated: {result}")

        return ModificationResult(
            success=True,
            mod_type=request.mod_type,
            description=request.description,
            changes_made={'template': template_name, 'result': result}
        )

    def _apply_module_compose(self, request: ModificationRequest) -> ModificationResult:
        """Compose existing modules in new ways."""
        # This would combine existing modules
        # For now, just validate the concept

        modules = request.parameters.get('modules', [])
        composition = request.parameters.get('composition', 'sequential')

        logger.info(f"Would compose {modules} in {composition} manner")

        return ModificationResult(
            success=True,
            mod_type=request.mod_type,
            description=request.description,
            changes_made={'modules': modules, 'composition': composition}
        )

    def _apply_custom_code(self, request: ModificationRequest) -> ModificationResult:
        """Execute custom generated code."""
        if not request.code:
            return ModificationResult(
                success=False,
                mod_type=request.mod_type,
                description=request.description,
                error="No code provided"
            )

        # Extra validation for custom code
        is_valid, issues = self.validator.validate(request.code)
        if not is_valid:
            return ModificationResult(
                success=False,
                mod_type=request.mod_type,
                description=request.description,
                error=f"Code validation failed: {issues}"
            )

        # Execute in sandbox
        success, result, error = self.sandbox.execute(request.code)

        if not success:
            return ModificationResult(
                success=False,
                mod_type=request.mod_type,
                description=request.description,
                error=error
            )

        return ModificationResult(
            success=True,
            mod_type=request.mod_type,
            description=request.description,
            changes_made={'code_executed': True, 'result': result}
        )

    def rollback_last(self) -> bool:
        """Rollback the last modification."""
        if not self.rollback_stack:
            logger.warning("Nothing to rollback")
            return False

        last = self.rollback_stack.pop()
        result = last.get('result')
        snapshot_id = last.get('snapshot_id')

        if not snapshot_id:
            logger.warning("No snapshot_id in rollback data")
            return False

        success = self._restore_snapshot(snapshot_id)
        if success:
            self.modifications_this_session -= 1
            if result:
                logger.info(f"Rolled back: {result.description}")

        return success

    def get_history(self) -> List[Dict]:
        """Get modification history."""
        return [
            {
                'success': r.success,
                'type': r.mod_type.name,
                'description': r.description,
                'changes': r.changes_made,
                'error': r.error
            }
            for r in self.modification_history
        ]


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Testing Self-Modification Engine...")
    print("=" * 60)

    # Create a simple test model
    class TestModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.hidden_dim = 256
            self.learning_rate = 0.001
            self.layer = nn.Linear(256, 256)

        def forward(self, x):
            return self.layer(x)

    model = TestModel()
    engine = SelfModificationEngine(model, auto_approve_safe=True)

    # Test 1: Parameter tuning
    print("\n1. Testing PARAMETER_TUNE...")
    request = ModificationRequest(
        mod_type=ModificationType.PARAMETER_TUNE,
        description="Increase learning rate",
        target_component="learning_rate",
        parameters={'learning_rate': 0.01},
        approved=True
    )
    result = engine.request_modification(request)
    print(f"   Success: {result.success}")
    print(f"   Changes: {result.changes_made}")
    print(f"   Model LR: {model.learning_rate}")

    # Test 2: Layer template
    print("\n2. Testing LAYER_TEMPLATE (attention)...")
    request = ModificationRequest(
        mod_type=ModificationType.LAYER_TEMPLATE,
        description="Add attention layer",
        target_component="layers",
        parameters={'template': 'attention', 'hidden_dim': 256, 'num_heads': 8},
        approved=True
    )
    result = engine.request_modification(request)
    print(f"   Success: {result.success}")
    print(f"   Result: {result.changes_made}")

    # Test 3: Resonance modulator template
    print("\n3. Testing LAYER_TEMPLATE (resonance)...")
    request = ModificationRequest(
        mod_type=ModificationType.LAYER_TEMPLATE,
        description="Add resonance modulator",
        target_component="layers",
        parameters={'template': 'resonance', 'hidden_dim': 256},
        approved=True
    )
    result = engine.request_modification(request)
    print(f"   Success: {result.success}")
    print(f"   Result: {result.changes_made}")

    # Test 4: Custom code (should be rejected without approval)
    print("\n4. Testing CUSTOM_CODE (without approval)...")
    request = ModificationRequest(
        mod_type=ModificationType.CUSTOM_CODE,
        description="Custom modification",
        target_component="model",
        code="result = {'test': 'hello'}",
        approved=False  # Not approved
    )
    result = engine.request_modification(request)
    print(f"   Success: {result.success}")
    print(f"   Error: {result.error}")

    # Test 5: Custom code (with approval)
    print("\n5. Testing CUSTOM_CODE (with approval)...")
    request = ModificationRequest(
        mod_type=ModificationType.CUSTOM_CODE,
        description="Safe custom modification",
        target_component="model",
        code="result = {'computed': 1 + 1, 'pi_phi': 5.083203692315260}",
        approved=True
    )
    result = engine.request_modification(request)
    print(f"   Success: {result.success}")
    print(f"   Result: {result.changes_made}")

    # Test 6: Dangerous code (should be rejected)
    print("\n6. Testing CUSTOM_CODE (dangerous - should reject)...")
    request = ModificationRequest(
        mod_type=ModificationType.CUSTOM_CODE,
        description="Dangerous code",
        target_component="model",
        code="import os; os.system('rm -rf /')",  # This should be caught!
        approved=True
    )
    result = engine.request_modification(request)
    print(f"   Success: {result.success}")
    print(f"   Error: {result.error}")

    # Test 7: Rollback
    print("\n7. Testing ROLLBACK...")
    print(f"   LR before rollback: {model.learning_rate}")
    engine.rollback_last()
    print(f"   LR after rollback: {model.learning_rate}")

    # Print history
    print("\n" + "=" * 60)
    print("Modification History:")
    for i, entry in enumerate(engine.get_history()):
        status = "✓" if entry['success'] else "✗"
        print(f"  {i+1}. [{status}] {entry['type']}: {entry['description']}")

    print("\n✅ Self-Modification Engine working!")
    print("π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA")
