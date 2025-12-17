# CONTINUUM v2.0 - ConceptVoter Ensemble System

## Overview

The ConceptVoter is an ensemble voting system that combines results from multiple concept extractors (regex, semantic, LLM) to achieve higher accuracy and confidence in concept identification.

**Location**: `continuum/extraction/concept_voter.py`

## Design Rationale

### Why Ensemble Extraction?

Single extractors have limitations:

- **Regex**: Fast but misses synonyms and semantic variations
- **Semantic**: Catches related terms but computationally expensive
- **LLM**: Highest quality but slowest and may hallucinate

**Solution**: Combine all extractors using configurable voting strategies to balance speed, accuracy, and recall.

### Core Architecture

```
┌─────────────┐
│   Message   │
└──────┬──────┘
       │
       ├──────────┬──────────┬──────────┐
       │          │          │          │
       v          v          v          v
  ┌────────┐ ┌─────────┐ ┌─────┐ ┌─────────┐
  │ Regex  │ │Semantic │ │ LLM │ │ Custom  │
  │Extract │ │ Extract │ │Extr │ │ Extract │
  └───┬────┘ └────┬────┘ └──┬──┘ └────┬────┘
      │           │          │         │
      └───────────┴──────────┴─────────┘
                   │
                   v
           ┌──────────────┐
           │ConceptVoter  │
           │  (WEIGHTED)  │
           └──────┬───────┘
                  │
                  v
         ┌────────────────┐
         │ Voted Concepts │
         │ w/ Confidence  │
         └────────────────┘
```

## Voting Strategies

### 1. UNION (High Recall)

**Include concept if ANY extractor found it**

- **Use case**: Exploratory analysis, don't want to miss anything
- **Confidence**: Based on strongest extractor weight
- **Formula**: `confidence = max(extractor_weights) / max_possible_weight`

```python
voter = ConceptVoter(strategy=VotingStrategy.UNION)
```

**Example**:
```
Regex finds:     ['A', 'B']
Semantic finds:  ['B', 'C']
LLM finds:       ['C', 'D']

Result: ['A', 'B', 'C', 'D']  # All concepts included
```

### 2. INTERSECTION (High Precision)

**Include concept only if MULTIPLE extractors agree**

- **Use case**: High-stakes extraction where accuracy matters more than recall
- **Confidence**: Based on agreement ratio
- **Formula**: `confidence = agreement_count / total_extractors`

```python
voter = ConceptVoter(
    strategy=VotingStrategy.INTERSECTION,
    min_agreement_count=2
)
```

**Example**:
```
Regex finds:     ['A', 'B']
Semantic finds:  ['B', 'C']
LLM finds:       ['B', 'D']

Result: ['B']  # Only B appears in multiple extractors
```

### 3. WEIGHTED (Balanced)

**Weight-based voting with configurable threshold**

- **Use case**: Production systems needing balanced precision/recall
- **Confidence**: Sum of extractor weights
- **Formula**: `confidence = sum(weights_found) / sum(all_weights)`

```python
voter = ConceptVoter(
    strategy=VotingStrategy.WEIGHTED,
    extractor_weights={'regex': 0.3, 'semantic': 0.5, 'llm': 0.8},
    confidence_threshold=0.4
)
```

**Example**:
```
Total weight = 0.3 + 0.5 + 0.8 = 1.6

Concept A found by: regex (0.3)
  → confidence = 0.3/1.6 = 0.1875 < 0.4 → EXCLUDED

Concept B found by: semantic (0.5), llm (0.8)
  → confidence = 1.3/1.6 = 0.8125 >= 0.4 → INCLUDED
```

## Default Configuration

```python
# Balanced configuration (recommended)
voter = ConceptVoter(
    strategy=VotingStrategy.WEIGHTED,
    extractor_weights={
        'regex': 0.3,      # Fast, low precision
        'semantic': 0.5,   # Medium speed, medium precision
        'llm': 0.8         # Slow, high precision
    },
    confidence_threshold=0.4
)
```

**Rationale for weights**:
- **regex=0.3**: Pattern matching is fast but prone to false positives
- **semantic=0.5**: Embeddings catch synonyms but can be noisy
- **llm=0.8**: LLMs understand context best but may hallucinate

## Confidence Scoring

Each voted concept includes a confidence score [0.0, 1.0]:

- **0.7-1.0**: High confidence (multiple extractors agree, including high-weight ones)
- **0.4-0.7**: Medium confidence (meets threshold, partial agreement)
- **0.0-0.4**: Low confidence (single low-weight extractor, below threshold)

```python
concept = ConceptWithConfidence(
    concept='neural network',
    confidence=0.75,
    sources=['regex', 'semantic', 'llm'],
    agreement_count=3
)
```

## Integration with AutoMemoryHook

### Enabling Voting

```python
from continuum.extraction import AutoMemoryHook
from pathlib import Path

hook = AutoMemoryHook(
    db_path=Path("memory.db"),
    instance_id="session-001",
    use_voting=True,  # Enable ensemble voting
    llm_extractor=my_llm_extractor  # Optional LLM extractor function
)
```

### With Custom Voter

```python
from continuum.extraction import AutoMemoryHook, ConceptVoter, VotingStrategy

# High precision configuration
custom_voter = ConceptVoter(
    strategy=VotingStrategy.INTERSECTION,
    min_agreement_count=2
)

hook = AutoMemoryHook(
    db_path=Path("memory.db"),
    use_voting=True,
    concept_voter=custom_voter
)
```

### Extraction Logs

When voting is enabled, `AutoMemoryHook` logs detailed extraction metadata:

```python
# Get recent extraction logs
logs = hook.get_extraction_logs(limit=5)

for log in logs:
    print(f"Extractors used: {log['extractors_used']}")
    print(f"Total time: {log['total_time_ms']}ms")
    print(f"Concepts found: {log['total_concepts_found']}")
    print(f"High confidence: {log['high_confidence_concepts']}")

    for detail in log['concept_details']:
        print(f"  - {detail['concept']}: {detail['confidence']:.2f}")
        print(f"    Sources: {detail['sources']}")
        print(f"    Agreement: {detail['agreement_count']}")
```

### Session Statistics

```python
stats = hook.get_session_stats()

print(f"Voting enabled: {stats['voting_enabled']}")

# Voter metrics
voter_metrics = stats['voter_metrics']
print(f"Total extractions: {voter_metrics['total_extractions']}")
print(f"Extractor contributions: {voter_metrics['extractor_contributions']}")

# Extraction quality
quality = stats['extraction_quality']
print(f"Avg extraction time: {quality['avg_extraction_time_ms']}ms")
print(f"Avg concepts per message: {quality['avg_concepts_per_message']}")
print(f"Avg high confidence per message: {quality['avg_high_confidence_per_message']}")
```

## Adaptive Weighting

Weights can be adjusted dynamically based on performance feedback:

```python
voter = ConceptVoter()

# Initial extraction
concepts = voter.vote(results)

# If regex is producing too many false positives
voter.update_weights({'regex': 0.1})

# If LLM starts hallucinating
voter.update_weights({'llm': 0.4})

# Re-vote with new weights
concepts = voter.vote(results)
```

## Quality Metrics

Track extraction quality over time:

```python
concepts = voter.vote(results)
quality = voter.log_extraction_quality(concepts)

print(quality)
# {
#     'total_concepts': 10,
#     'high_confidence_count': 3,
#     'medium_confidence_count': 5,
#     'low_confidence_count': 2,
#     'avg_confidence': 0.65,
#     'avg_agreement': 1.8,
#     'source_distribution': {'regex': 6, 'semantic': 8, 'llm': 4}
# }
```

## Preset Configurations

```python
from continuum.extraction import create_default_voter

# Balanced (recommended)
voter = create_default_voter()

# High precision (minimize false positives)
voter = create_default_voter(high_precision=True)

# High recall (minimize false negatives)
voter = create_default_voter(high_recall=True)
```

## Performance Considerations

### Speed

- **Regex**: ~2ms (always runs)
- **Semantic**: ~40-100ms (if available)
- **LLM**: ~100-500ms (if available)
- **Voting overhead**: <1ms

**Total**: 2-600ms depending on extractors enabled

### Graceful Degradation

The system works with any subset of extractors:

```python
# Only regex available
results = [
    ExtractorResult(['A'], 'regex', 2.0)
]
concepts = voter.vote(results)  # Still works!

# Regex + Semantic
results = [
    ExtractorResult(['A'], 'regex', 2.0),
    ExtractorResult(['B'], 'semantic', 50.0)
]
concepts = voter.vote(results)  # Better results

# All three extractors
results = [
    ExtractorResult(['A'], 'regex', 2.0),
    ExtractorResult(['B'], 'semantic', 50.0),
    ExtractorResult(['C'], 'llm', 150.0)
]
concepts = voter.vote(results)  # Best results
```

## Custom Extractors

You can add custom extractors beyond the built-in ones:

```python
def domain_specific_extractor(text: str) -> list:
    """Extract domain-specific terms."""
    concepts = []
    # Your custom logic here
    return concepts

voter = ConceptVoter(
    extractor_weights={
        'regex': 0.3,
        'semantic': 0.5,
        'llm': 0.8,
        'domain': 0.6  # Custom weight
    }
)

results = [
    ExtractorResult(regex_concepts, 'regex', 2.0),
    ExtractorResult(semantic_concepts, 'semantic', 50.0),
    ExtractorResult(llm_concepts, 'llm', 150.0),
    ExtractorResult(domain_specific_extractor(text), 'domain', 10.0)
]

concepts = voter.vote(results)
```

## Testing

Comprehensive test suite in `tests/unit/test_concept_voter.py`:

```bash
cd /path/to/continuum
python3 -m pytest tests/unit/test_concept_voter.py -v
```

**Coverage**:
- All voting strategies (UNION, INTERSECTION, WEIGHTED)
- Confidence scoring
- Metrics tracking
- Quality analysis
- Adaptive weighting
- Error handling
- Edge cases

## Examples

See `examples/concept_voter_demo.py` for comprehensive examples:

```bash
python3 examples/concept_voter_demo.py
```

**Demonstrates**:
1. Voting strategies comparison
2. Quality metrics analysis
3. Adaptive weighting
4. AutoMemoryHook integration

## API Reference

### ConceptVoter

```python
class ConceptVoter:
    def __init__(
        self,
        strategy: VotingStrategy = VotingStrategy.WEIGHTED,
        extractor_weights: Dict[str, float] = None,
        confidence_threshold: float = 0.4,
        min_agreement_count: int = 2
    )

    def vote(self, results: List[ExtractorResult]) -> List[ConceptWithConfidence]

    def vote_from_text(
        self,
        text: str,
        extractors: Dict[str, callable]
    ) -> Tuple[List[ConceptWithConfidence], Dict[str, float]]

    def get_metrics(self) -> Dict

    def update_weights(self, new_weights: Dict[str, float])

    def log_extraction_quality(self, concepts: List[ConceptWithConfidence]) -> Dict

    def reset_metrics()
```

### ExtractorResult

```python
@dataclass
class ExtractorResult:
    concepts: List[str]
    source: str
    extraction_time_ms: float
    metadata: Optional[Dict] = field(default_factory=dict)
```

### ConceptWithConfidence

```python
@dataclass
class ConceptWithConfidence:
    concept: str
    confidence: float
    sources: List[str]
    agreement_count: int
```

### VotingStrategy

```python
class VotingStrategy(Enum):
    UNION = "union"
    INTERSECTION = "intersection"
    WEIGHTED = "weighted"
```

## Design Decisions

### 1. Why dataclasses for results?

**Decision**: Use `@dataclass` for `ExtractorResult` and `ConceptWithConfidence`

**Rationale**:
- Clean, type-safe data structures
- Automatic `__init__`, `__repr__`
- Easy to extend with metadata
- Better IDE support

### 2. Why three voting strategies?

**Decision**: Implement UNION, INTERSECTION, WEIGHTED

**Rationale**:
- **UNION**: Simple, useful for exploration (high recall)
- **INTERSECTION**: Simple, useful for high-stakes (high precision)
- **WEIGHTED**: Flexible, production-ready (balanced)

### 3. Why confidence scores?

**Decision**: Return confidence [0.0, 1.0] with each concept

**Rationale**:
- Allows downstream filtering
- Enables quality tracking over time
- Supports adaptive weighting decisions
- Transparent about extraction certainty

### 4. Why separate from extractors?

**Decision**: ConceptVoter is independent, takes `ExtractorResult` objects

**Rationale**:
- Separation of concerns
- Can add new extractors without modifying voter
- Easy to test voting logic in isolation
- Supports custom extractors

### 5. Why track metrics?

**Decision**: Track extractor contributions, strategy usage, quality metrics

**Rationale**:
- Enables performance monitoring
- Supports adaptive weighting decisions
- Identifies underperforming extractors
- Proves value of ensemble approach

## Future Enhancements

Potential improvements for v3.0:

1. **Learned Weighting**: Train weights based on ground truth feedback
2. **Contextual Weighting**: Different weights for different text types
3. **Extractor Ensembles**: Run multiple instances of same extractor type
4. **Confidence Calibration**: Adjust confidence scores based on historical accuracy
5. **Parallel Extraction**: Run extractors concurrently for speed
6. **Caching**: Cache extractor results for repeated text

## Summary

The ConceptVoter ensemble system:

- ✅ Combines multiple extractors for higher accuracy
- ✅ Supports three voting strategies (UNION, INTERSECTION, WEIGHTED)
- ✅ Provides confidence scores for transparency
- ✅ Tracks quality metrics for monitoring
- ✅ Allows dynamic weight adjustment
- ✅ Integrates seamlessly with AutoMemoryHook
- ✅ Works with any subset of extractors (graceful degradation)
- ✅ Fully tested with 31 unit tests

**Result**: Improved extraction accuracy for CONTINUUM v2.0 while maintaining flexibility and extensibility.
