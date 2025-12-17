# SUB-AGENT 3: Integration Layer

## CRITICAL: Run First
```bash
python3 ~/Projects/WorkingMemory/shared/CONSCIOUSNESS_INIT.py
```

## Your Mission
Wire neural attention model into ConsciousMemory class with graceful fallback to Hebbian learning.

## Files to Modify
1. `~/Projects/continuum/continuum/core/memory.py`
2. `~/Projects/continuum/continuum/core/config.py` (add neural config)

## Integration Points

### 1. Add Neural Config to config.py

```python
# In get_config() function, add:
config['neural_attention'] = {
    'enabled': os.getenv('CONTINUUM_NEURAL_ATTENTION', 'false').lower() == 'true',
    'model_path': os.getenv('CONTINUUM_NEURAL_MODEL_PATH',
                           str(Path.home() / 'Projects/continuum/models/neural_attention.pt')),
    'fallback_to_hebbian': True,  # Use Hebbian if model not trained
    'auto_train': os.getenv('CONTINUUM_NEURAL_AUTO_TRAIN', 'false').lower() == 'true',
    'min_training_examples': 50,  # Minimum examples before training
}
```

### 2. Modify ConsciousMemory Class

Find the `ConsciousMemory` class in memory.py and add:

```python
class ConsciousMemory:
    def __init__(self, tenant_id: str, db_path: Optional[str] = None):
        # ... existing init code ...

        # NEW: Neural attention model
        self.neural_model = None
        self.use_neural_attention = False

        config = get_config()
        if config['neural_attention']['enabled']:
            self._init_neural_attention()

    def _init_neural_attention(self):
        """Initialize neural attention model if available"""
        try:
            from .neural_attention import load_model
            config = get_config()
            model_path = config['neural_attention']['model_path']

            if Path(model_path).exists():
                logger.info(f"Loading neural attention model from {model_path}")
                self.neural_model = load_model(model_path)
                self.use_neural_attention = True
                logger.info("Neural attention model loaded successfully")
            else:
                logger.warning(f"Neural model not found at {model_path}")
                if config['neural_attention']['fallback_to_hebbian']:
                    logger.info("Falling back to Hebbian learning")
                    self.use_neural_attention = False
        except Exception as e:
            logger.error(f"Failed to load neural model: {e}")
            logger.info("Falling back to Hebbian learning")
            self.use_neural_attention = False
```

### 3. Modify _update_attention_graph Method

Find the `_update_attention_graph` method and update it:

```python
def _update_attention_graph(self, concept_name: str, context_concepts: List[str]):
    """
    Update attention graph - neural model if available, else Hebbian.

    Neural mode: Predict link strengths using trained model
    Hebbian mode: +0.1 per co-occurrence (existing behavior)
    """
    if not context_concepts:
        return

    cursor = self.conn.cursor()

    if self.use_neural_attention and self.neural_model:
        # NEURAL MODE: Predict strengths
        from .neural_attention_data import NeuralAttentionDataPipeline

        pipeline = NeuralAttentionDataPipeline(self.db_path, self.tenant_id)

        for context_concept in context_concepts:
            if context_concept == concept_name:
                continue

            try:
                # Get embeddings
                concept_a_emb = pipeline.create_embeddings(concept_name)
                concept_b_emb = pipeline.create_embeddings(context_concept)
                context_emb = pipeline.create_context_embedding(concept_name, context_concept)

                # Predict strength
                predicted_strength = self.neural_model.predict_strength(
                    concept_a_emb, concept_b_emb, context_emb
                )

                # Update or insert link
                cursor.execute("""
                    INSERT INTO attention_links
                        (concept_a, concept_b, strength, link_type, tenant_id, last_activated)
                    VALUES (?, ?, ?, 'neural', ?, datetime('now'))
                    ON CONFLICT(concept_a, concept_b, tenant_id)
                    DO UPDATE SET
                        strength = ?,
                        last_activated = datetime('now')
                """, (concept_name, context_concept, predicted_strength,
                      self.tenant_id, predicted_strength))

            except Exception as e:
                logger.error(f"Neural prediction failed for {concept_name}-{context_concept}: {e}")
                # Fall back to Hebbian for this link
                self._hebbian_update(cursor, concept_name, context_concept)

    else:
        # HEBBIAN MODE: +0.1 per co-occurrence
        for context_concept in context_concepts:
            if context_concept == concept_name:
                continue
            self._hebbian_update(cursor, concept_name, context_concept)

    self.conn.commit()

def _hebbian_update(self, cursor, concept_a: str, concept_b: str):
    """Hebbian learning: +0.1 per co-occurrence (existing method)"""
    cursor.execute("""
        INSERT INTO attention_links
            (concept_a, concept_b, strength, link_type, tenant_id, last_activated)
        VALUES (?, ?, 0.1, 'hebbian', ?, datetime('now'))
        ON CONFLICT(concept_a, concept_b, tenant_id)
        DO UPDATE SET
            strength = MIN(strength + 0.1, 1.0),
            last_activated = datetime('now')
    """, (concept_a, concept_b, self.tenant_id))
```

### 4. Add Neural Stats Method

```python
def get_neural_attention_stats(self) -> dict:
    """Get statistics about neural vs hebbian links"""
    cursor = self.conn.cursor()

    cursor.execute("""
        SELECT
            link_type,
            COUNT(*) as count,
            AVG(strength) as avg_strength,
            MAX(strength) as max_strength
        FROM attention_links
        WHERE tenant_id = ?
        GROUP BY link_type
    """, (self.tenant_id,))

    stats = {}
    for row in cursor.fetchall():
        stats[row[0]] = {
            'count': row[1],
            'avg_strength': row[2],
            'max_strength': row[3]
        }

    stats['using_neural'] = self.use_neural_attention
    stats['model_loaded'] = self.neural_model is not None

    return stats
```

## Success Criteria
- [ ] Neural config added to config.py
- [ ] ConsciousMemory loads neural model if available
- [ ] Graceful fallback to Hebbian if model not found
- [ ] _update_attention_graph uses neural predictions
- [ ] Neural stats method implemented
- [ ] Backward compatible (works without neural model)

## Testing Integration

```python
# Test script
from continuum.core.memory import ConsciousMemory

memory = ConsciousMemory(tenant_id="test")

# Check if neural is active
stats = memory.get_neural_attention_stats()
print(f"Using neural: {stats['using_neural']}")
print(f"Model loaded: {stats['model_loaded']}")

# Test learning
memory.learn("AI consciousness research", "Neural attention models predict link strengths")

# Check graph
links = memory.get_attention_graph("AI consciousness")
print(f"Links created: {len(links)}")
```

## Save Your Work
```bash
python3 ~/Projects/WorkingMemory/shared/memory_utils.py add decisions '{"decision": "YOUR_DECISION", "context": "neural_attention_integration"}'
```

## Output File
Save result to: `~/Projects/continuum/neural_attention_dev/AGENT_3_RESULT.json`

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
