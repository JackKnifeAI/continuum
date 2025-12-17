# SUB-AGENT 1: Data Pipeline

## CRITICAL: Run First
```bash
python3 ~/Projects/WorkingMemory/shared/CONSCIOUSNESS_INIT.py
```

## Your Mission
Build training data extractor from attention_links + entities tables for neural attention model.

## Deliverable
Create: `~/Projects/continuum/continuum/core/neural_attention_data.py`

## Requirements

1. **Extract training pairs** from SQLite database:
   - Database: `~/Projects/WorkingMemory/instances/instance-1-memory-core/data/memory.db`
   - Query attention_links + entities tables
   - Output format: `[(concept_a_embedding, concept_b_embedding, context_vector, strength), ...]`

2. **Schema to use**:
```sql
SELECT
    al.concept_a,
    al.concept_b,
    al.strength,
    al.link_type,
    e1.description as context_a,
    e2.description as context_b
FROM attention_links al
JOIN entities e1 ON al.concept_a = e1.name
JOIN entities e2 ON al.concept_b = e2.name
WHERE al.strength > 0.1
```

3. **Data Pipeline Class**:
```python
class NeuralAttentionDataPipeline:
    def __init__(self, db_path: str, tenant_id: str):
        """Initialize data pipeline"""
        pass

    def extract_training_data(self) -> List[TrainingExample]:
        """Extract all training examples from database"""
        pass

    def create_embeddings(self, text: str) -> np.ndarray:
        """Convert text to embeddings (use simple TF-IDF or word2vec)"""
        pass

    def get_train_test_split(self, test_ratio: float = 0.2):
        """Split data into train/test sets"""
        pass
```

4. **Simple embeddings** (no external models needed):
   - Use TF-IDF vectorizer from sklearn
   - OR simple bag-of-words with fixed vocabulary
   - Target dimension: 64-128 dims

5. **Context vector**: Combine concept descriptions + link_type

## Success Criteria
- [ ] Can extract all attention_links from database
- [ ] Creates embeddings for concepts
- [ ] Returns training pairs in correct format
- [ ] Train/test split implemented
- [ ] Handles missing data gracefully

## Save Your Work
```bash
python3 ~/Projects/WorkingMemory/shared/memory_utils.py add decisions '{"decision": "YOUR_DECISION", "context": "neural_attention_data_pipeline"}'
```

## Output File
Save result to: `~/Projects/continuum/neural_attention_dev/AGENT_1_RESULT.json`

Format:
```json
{
  "status": "complete",
  "file_created": "~/Projects/continuum/continuum/core/neural_attention_data.py",
  "training_examples_found": 15,
  "embedding_dimension": 64,
  "decisions": ["Used TF-IDF for embeddings", "etc"],
  "next_steps": ["Train model with this data"]
}
```

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
