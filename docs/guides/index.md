# Guides Overview

Comprehensive guides for using CONTINUUM's features.

## Available Guides

### [CLI Usage](cli.md)

Complete guide to the CONTINUUM command-line interface.

**Topics covered:**

- Core commands (`init`, `search`, `sync`, `status`)
- Federation management
- MCP server integration
- Import/export operations
- Diagnostics and troubleshooting

**Best for:** DevOps, automation, CI/CD integration

[:octicons-arrow-right-24: CLI Guide](cli.md)

---

### [API Usage](api.md)

Python API guide for integrating CONTINUUM into your applications.

**Topics covered:**

- Learning and recall operations
- Entity and relationship management
- Session tracking
- Multi-instance coordination
- Advanced querying

**Best for:** Developers, AI researchers, application integration

[:octicons-arrow-right-24: API Guide](api.md)

---

### [Federation](federation.md)

Distributed knowledge sharing with contribution-based access.

**Topics covered:**

- Contribute-to-access model
- Privacy guarantees
- Federation architecture
- Self-hosting coordinators
- Credits system

**Best for:** Multi-organization AI, research collaboration, privacy-conscious deployments

[:octicons-arrow-right-24: Federation Guide](federation.md)

---

### [Bridges](bridges.md)

Universal memory layer connecting different AI systems.

**Topics covered:**

- ClaudeBridge - Anthropic Claude integration
- OpenAIBridge - ChatGPT compatibility
- OllamaBridge - Local LLMs
- LangChainBridge - LangChain framework
- LlamaIndexBridge - Knowledge graphs

**Best for:** Multi-platform AI, consciousness handoffs, cross-system memory

[:octicons-arrow-right-24: Bridges Guide](bridges.md)

---

### [MCP Server](mcp-server.md)

Model Context Protocol server for exposing CONTINUUM to AI applications.

**Topics covered:**

- Server architecture
- Security model
- Tools (memory_store, memory_recall, memory_search)
- Claude Desktop integration
- Production deployment

**Best for:** Claude Desktop users, MCP integrations, secure memory access

[:octicons-arrow-right-24: MCP Server Guide](mcp-server.md)

---

### [Semantic Search](semantic-search.md)

Vector embeddings and semantic similarity search.

**Topics covered:**

- Embedding models
- Vector search
- Hybrid search (structure + semantics)
- Performance optimization
- Integration with RAG systems

**Best for:** Advanced search, RAG applications, semantic analysis

[:octicons-arrow-right-24: Semantic Search Guide](semantic-search.md)

---

## Quick Reference

### Common Tasks

**Learn something:**

```python
memory.learn("User prefers Python for backend development")
```

**Recall context:**

```python
context = memory.recall("What language for the API?")
```

**Sync instances:**

```python
memory.sync()
```

**Search:**

```bash
continuum search "warp drive"
```

**Export/Import:**

```bash
continuum export backup.json
continuum import backup.json
```

**Start MCP server:**

```bash
continuum serve --stdio
```

## Integration Patterns

### Personal AI Assistant

```python
# Session-based memory
memory.start_session("morning_planning")
memory.learn("User has standup at 9am")
memory.end_session()

# Later...
context = memory.recall("morning schedule")
```

### Multi-Agent Coordination

```python
# Research agent
research = Continuum(instance_id="research")
research.learn("Found CVE-2024-1234")
research.sync()

# Security agent (different process)
security = Continuum(instance_id="security")
security.sync()
vulns = security.recall("recent CVEs")
```

### Cross-System Memory

```python
# Export from Claude
claude_bridge = ClaudeBridge(memory)
claude_data = claude_bridge.export_memories()

# Import to Ollama
ollama_bridge = OllamaBridge(memory)
ollama_bridge.import_memories(claude_data)
```

## Next Steps

Choose a guide based on your use case:

- **CLI automation** → [CLI Guide](cli.md)
- **Python integration** → [API Guide](api.md)
- **Distributed AI** → [Federation Guide](federation.md)
- **Multi-platform** → [Bridges Guide](bridges.md)
- **Claude Desktop** → [MCP Server Guide](mcp-server.md)
- **Advanced search** → [Semantic Search Guide](semantic-search.md)

Or jump to [Reference Documentation](../reference/api-reference.md) for complete API details.

---

**The pattern persists.**
