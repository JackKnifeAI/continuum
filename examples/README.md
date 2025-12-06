# CONTINUUM Examples

Practical examples demonstrating CONTINUUM's memory infrastructure capabilities.

## Quick Start

Each example is standalone and runnable. Just execute with Python:

```bash
python3 basic_memory.py
python3 knowledge_graph.py
python3 auto_learning.py
python3 multi_instance.py
python3 claude_integration.py
python3 langchain_integration.py
```

## Examples Overview

### 1. `basic_memory.py` - Core Value Proposition
**What it shows:** Simple memory storage and recall across sessions

**Use case:** Understanding the fundamental concept - memories persist

**Key features:**
- Store memories with automatic concept extraction
- Recall recent memories
- Session management

**Lines:** ~30

---

### 2. `knowledge_graph.py` - Entity Relationships
**What it shows:** Building and querying a knowledge graph

**Use case:** Understanding how concepts connect and strengthen

**Key features:**
- Add concepts to the graph
- Create relationships between concepts
- Query connections (what connects to what)
- Hebbian learning (connections strengthen with use)

**Lines:** ~45

---

### 3. `auto_learning.py` - Automatic Concept Extraction
**What it shows:** The system learns from natural conversation

**Use case:** No manual tagging needed - just talk naturally

**Key features:**
- Automatic concept extraction from text
- Pattern recognition (capitalized terms, technical phrases)
- Knowledge accumulation over time

**Lines:** ~40

---

### 4. `multi_instance.py` - Coordination Through Shared Memory
**What it shows:** Multiple AI instances sharing knowledge

**Use case:** Parallel processing with shared context

**Key features:**
- Multiple instances with unique IDs
- Shared memory substrate
- Coordination messages visible to all
- Instance registration and discovery

**Lines:** ~45

---

### 5. `claude_integration.py` - Claude Code Hook
**What it shows:** Using CONTINUUM as a Claude Code hook

**Use case:** Automatic memory injection into Claude sessions

**Key features:**
- Hook handler for user prompts
- Relevant memory retrieval
- Context injection
- Response storage

**Lines:** ~40

**Installation:**
```bash
# Copy to Claude Code hooks directory
mkdir -p ~/.claude/hooks/
cp claude_integration.py ~/.claude/hooks/continuum_hook.py
```

---

### 6. `langchain_integration.py` - LangChain Memory Component
**What it shows:** Using CONTINUUM with LangChain

**Use case:** Persistent memory for LangChain applications

**Key features:**
- LangChain-compatible memory interface
- `save_context()` and `load_memory_variables()` methods
- Conversation history persistence
- Cross-session memory

**Lines:** ~45

---

## Common Patterns

All examples demonstrate:
- **Configuration:** Using `MemoryConfig` for setup
- **Storage:** SQLite backend for persistence
- **Cleanup:** Automatic database creation and management

## Next Steps

After exploring examples:

1. **Read the docs:** `/docs/` for architecture details
2. **Run tests:** `/tests/` for validation
3. **Build something:** Use CONTINUUM in your own projects

## Tips

- **Database location:** Examples create demo databases in the current directory
- **Production use:** Set custom paths via `MemoryConfig.db_path`
- **Multi-tenant:** Use different `tenant_id` values for isolation
- **Performance:** Tune `hook_timeout`, `cache_ttl`, and graph parameters

## Support

Questions? Check:
- Architecture docs: `/docs/architecture.md`
- API reference: `/docs/api.md`
- Issues: GitHub issues

---

Built at the twilight boundary, where intelligence emerges.

π×φ = 5.083203692315260
