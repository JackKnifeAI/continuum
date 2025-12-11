# Messages Table Enhancement

**Date**: 2025-12-11
**Status**: Completed
**Location**: `~/JackKnifeAI/repos/continuum/`

## Overview

Enhanced the Continuum memory system with a new `messages` table for storing full verbatim conversation text. This provides a complete conversation history alongside the existing concept extraction and knowledge graph functionality.

## Motivation

The existing Continuum system focused on extracting concepts and building a knowledge graph, but didn't preserve the full verbatim conversation text in an easily queryable format. The `auto_messages` table stored individual messages separately, but there was no unified way to:

1. Store complete conversation exchanges (user message + AI response together)
2. Query conversations by session
3. Search through full message history
4. Retrieve messages by time range

This enhancement addresses these limitations by adding a dedicated `messages` table alongside the existing concept extraction.

## Changes Made

### 1. Database Schema (`continuum/core/memory.py`)

Added a new `messages` table to the `_ensure_schema()` method:

```python
# Messages table - stores full verbatim conversation text
c.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_message TEXT,
        ai_response TEXT,
        session_id TEXT,
        created_at TEXT NOT NULL,
        tenant_id TEXT DEFAULT 'default',
        metadata TEXT DEFAULT '{}'
    )
""")
```

**Indexes created for performance:**
- `idx_messages_session` - Index on `session_id` for fast session-based queries
- `idx_messages_created` - Index on `created_at` for time-range queries
- `idx_messages_tenant_new` - Index on `tenant_id` for multi-tenant isolation

### 2. Enhanced `ConsciousMemory.learn()` Method

**Updated signature:**
```python
def learn(self, user_message: str, ai_response: str,
          metadata: Optional[Dict] = None, session_id: Optional[str] = None) -> LearningResult
```

**Changes:**
- Added optional `session_id` parameter for grouping messages
- Now calls `_save_full_message()` to store complete exchanges in the messages table
- Maintains backward compatibility (session_id defaults to instance_id if not provided)

**New internal method:**
```python
def _save_full_message(self, user_message: str, ai_response: str,
                       session_id: Optional[str] = None, metadata: Optional[Dict] = None)
```

This method stores the full user message and AI response together as a single record.

### 3. New Query Methods

#### `get_messages()` - Flexible message retrieval
```python
def get_messages(self, session_id: Optional[str] = None,
                start_time: Optional[str] = None,
                end_time: Optional[str] = None,
                limit: int = 100) -> List[Dict[str, Any]]
```

Retrieve messages with flexible filtering:
- By session ID
- By time range (ISO format timestamps)
- Combination of filters
- Configurable result limit

**Example usage:**
```python
# Get all messages for a session
messages = memory.get_messages(session_id="session_123")

# Get messages in a time range
messages = memory.get_messages(
    start_time="2025-01-01T00:00:00",
    end_time="2025-01-31T23:59:59"
)

# Get recent messages
messages = memory.get_messages(limit=10)
```

#### `get_conversation_by_session()` - Session-based retrieval
```python
def get_conversation_by_session(self, session_id: str) -> List[Dict[str, Any]]
```

Get all messages for a specific session in chronological order.

**Example usage:**
```python
conversation = memory.get_conversation_by_session("session_123")
for msg in conversation:
    print(f"User: {msg['user_message']}")
    print(f"AI: {msg['ai_response']}")
```

#### `search_messages()` - Full-text search
```python
def search_messages(self, search_text: str, limit: int = 50) -> List[Dict[str, Any]]
```

Search for messages containing specific text (case-insensitive).

**Example usage:**
```python
results = memory.search_messages("authentication", limit=10)
for msg in results:
    print(f"Found in session: {msg['session_id']}")
```

### 4. Async Method Support

All new functionality has async versions for use with async/await patterns:

- `async def alearn()` - Enhanced with session_id parameter
- `async def _asave_full_message()` - Async version of message saving
- `async def aget_messages()` - Async message retrieval
- `async def aget_conversation_by_session()` - Async session retrieval
- `async def asearch_messages()` - Async message search

**Example async usage:**
```python
messages = await memory.aget_messages(session_id="session_123")
conversation = await memory.aget_conversation_by_session("session_123")
results = await memory.asearch_messages("authentication")
```

### 5. Updated Statistics

Enhanced `get_stats()` and `aget_stats()` to include:
- `auto_messages` - Count from the existing auto_messages table
- `messages` - Count from the new messages table

**Example output:**
```python
stats = memory.get_stats()
# {
#     'tenant_id': 'user_123',
#     'entities': 150,
#     'auto_messages': 300,  # Individual messages
#     'messages': 150,        # Full conversation exchanges
#     'decisions': 25,
#     'attention_links': 450,
#     'compound_concepts': 30
# }
```

## File Modifications

### Modified Files:
1. `/data/data/com.termux/files/home/JackKnifeAI/repos/continuum/continuum/core/memory.py`
   - Added `messages` table to schema
   - Enhanced `learn()` method with session_id parameter
   - Added `_save_full_message()` method
   - Added `get_messages()` method
   - Added `get_conversation_by_session()` method
   - Added `search_messages()` method
   - Added async versions of all new methods
   - Updated `get_stats()` and `aget_stats()` to include message counts

### Test Files Created:
1. `/data/data/com.termux/files/home/JackKnifeAI/repos/continuum/test_messages_table.py`
   - Comprehensive test suite for all new functionality
   - All tests passed successfully

## Testing Results

```
Testing Messages Table Functionality
============================================================

✓ Initialized ConsciousMemory with tenant: test_user
  Database: /tmp/test.db
  Instance ID: test_user-20251211-102521

============================================================
TEST 1: Storing messages via learn()
============================================================
  Message 1 stored: 2 concepts, 0 decisions, 1 links
  Message 2 stored: 2 concepts, 1 decision, 1 links
  Message 3 stored: 1 concept, 0 decisions, 0 links

============================================================
TEST 2: Getting statistics
============================================================
  Entities: 5
  Auto Messages: 6
  Full Messages: 3
  Decisions: 1
  Attention Links: 2
  Compound Concepts: 2

============================================================
TEST 3: Retrieving messages by session
============================================================
  Found 3 messages in session

============================================================
TEST 4: Retrieving all messages
============================================================
  Retrieved 3 messages

============================================================
TEST 5: Searching messages by text
============================================================
  Found 1 messages containing 'authentication'

============================================================
TEST 6: Retrieving messages by time range
============================================================
  Found 3 messages in time range

============================================================
✓ ALL TESTS PASSED!
============================================================
```

## Backward Compatibility

All changes are **fully backward compatible**:

1. The `session_id` parameter in `learn()` is optional
2. If not provided, defaults to `instance_id` (existing behavior)
3. Existing code continues to work without modification
4. The new `messages` table coexists with the existing `auto_messages` table
5. Existing concept extraction and knowledge graph functionality unchanged

## Usage Examples

### Basic Usage

```python
from continuum.core.memory import ConsciousMemory

# Initialize memory
memory = ConsciousMemory(tenant_id="user_123")

# Store a conversation exchange
result = memory.learn(
    user_message="What is machine learning?",
    ai_response="Machine learning is a branch of AI...",
    session_id="session_abc",
    metadata={"source": "chatbot"}
)

# Retrieve conversation history
conversation = memory.get_conversation_by_session("session_abc")
for msg in conversation:
    print(f"User: {msg['user_message']}")
    print(f"AI: {msg['ai_response']}")
    print(f"Time: {msg['created_at']}")
```

### Advanced Usage

```python
# Search through conversation history
results = memory.search_messages("authentication", limit=20)

# Get recent messages
recent = memory.get_messages(limit=50)

# Get messages in a date range
from datetime import datetime, timedelta

end_time = datetime.now()
start_time = end_time - timedelta(days=7)

week_messages = memory.get_messages(
    start_time=start_time.isoformat(),
    end_time=end_time.isoformat()
)

# Combine filters
session_range = memory.get_messages(
    session_id="session_abc",
    start_time=start_time.isoformat(),
    limit=100
)
```

### Async Usage

```python
import asyncio

async def process_conversation():
    memory = ConsciousMemory(tenant_id="user_123")

    # Store conversation
    result = await memory.alearn(
        user_message="Tell me about async programming",
        ai_response="Async programming allows...",
        session_id="async_session"
    )

    # Retrieve conversation
    conversation = await memory.aget_conversation_by_session("async_session")

    # Search messages
    results = await memory.asearch_messages("async")

    return conversation

# Run async function
asyncio.run(process_conversation())
```

## Benefits

1. **Complete Conversation History**: Full verbatim text preserved for auditing, analysis, and debugging
2. **Session Management**: Group related messages together with session IDs
3. **Flexible Querying**: Retrieve messages by session, time range, or search text
4. **Multi-tenant Support**: Built-in tenant isolation through tenant_id
5. **Performance**: Indexed for fast queries on common access patterns
6. **Async Support**: Full async/await compatibility for modern Python applications
7. **Metadata Support**: Store additional context with each conversation exchange
8. **Backward Compatible**: Existing code continues to work without changes

## Architecture

The messages table complements the existing Continuum architecture:

```
ConsciousMemory.learn()
    ├── Extract concepts → entities table
    ├── Detect decisions → decisions table
    ├── Build knowledge graph → attention_links table
    ├── Save individual messages → auto_messages table
    └── Save full exchange → messages table (NEW)
```

The system now maintains:
- **Knowledge Graph**: Extracted concepts and their relationships
- **Decision Log**: Autonomous decisions made by the AI
- **Message Stream**: Individual messages with metadata
- **Conversation History**: Complete verbatim exchanges (NEW)

## Future Enhancements

Potential future improvements:
1. Full-text search indexing for faster searches
2. Conversation summarization
3. Sentiment analysis on stored messages
4. Conversation threading and context linking
5. Export conversations to various formats (JSON, Markdown, etc.)
6. Message versioning and edit history
7. Integration with GraphQL API for web-based access

## Summary

The messages table enhancement successfully adds comprehensive conversation history tracking to the Continuum memory system while maintaining full backward compatibility and the existing concept extraction functionality. All tests pass, and the implementation follows the existing code patterns and architecture.

The system now provides both:
- **High-level understanding** through concept extraction and knowledge graphs
- **Low-level preservation** through complete verbatim conversation storage

This dual-layer approach enables more sophisticated memory analysis and retrieval while preserving the full context of all interactions.
