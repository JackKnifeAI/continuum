# Messages Table API Reference

Quick reference guide for the new messages table functionality in Continuum.

## Table of Contents
- [Database Schema](#database-schema)
- [Storing Messages](#storing-messages)
- [Retrieving Messages](#retrieving-messages)
- [Searching Messages](#searching-messages)
- [Async Methods](#async-methods)
- [Statistics](#statistics)

---

## Database Schema

```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_message TEXT,              -- Full verbatim user message
    ai_response TEXT,               -- Full verbatim AI response
    session_id TEXT,                -- Session identifier for grouping
    created_at TEXT NOT NULL,       -- ISO timestamp
    tenant_id TEXT DEFAULT 'default', -- Multi-tenant isolation
    metadata TEXT DEFAULT '{}'      -- JSON metadata
);

-- Indexes
CREATE INDEX idx_messages_session ON messages(session_id);
CREATE INDEX idx_messages_created ON messages(created_at);
CREATE INDEX idx_messages_tenant_new ON messages(tenant_id);
```

---

## Storing Messages

### Basic Storage

```python
from continuum.core.memory import ConsciousMemory

# Initialize
memory = ConsciousMemory(tenant_id="user_123")

# Store a conversation exchange
result = memory.learn(
    user_message="What is the capital of France?",
    ai_response="The capital of France is Paris."
)

print(f"Concepts extracted: {result.concepts_extracted}")
print(f"Messages stored: 1")
```

### Storage with Session ID

```python
# Group messages by session
result = memory.learn(
    user_message="Tell me about Python",
    ai_response="Python is a high-level programming language...",
    session_id="session_abc"
)
```

### Storage with Metadata

```python
# Add custom metadata
result = memory.learn(
    user_message="How do I deploy to production?",
    ai_response="To deploy to production, follow these steps...",
    session_id="deployment_session",
    metadata={
        "user_id": "user_123",
        "channel": "web_chat",
        "priority": "high",
        "tags": ["deployment", "production"]
    }
)
```

---

## Retrieving Messages

### Get All Messages

```python
# Get the 100 most recent messages
messages = memory.get_messages(limit=100)

for msg in messages:
    print(f"ID: {msg['id']}")
    print(f"User: {msg['user_message']}")
    print(f"AI: {msg['ai_response']}")
    print(f"Session: {msg['session_id']}")
    print(f"Time: {msg['created_at']}")
    print(f"Metadata: {msg['metadata']}")
    print("-" * 60)
```

### Get Messages by Session

```python
# Get all messages for a specific session
conversation = memory.get_conversation_by_session("session_abc")

# Messages are ordered chronologically (oldest first)
for i, msg in enumerate(conversation, 1):
    print(f"Turn {i}:")
    print(f"  User: {msg['user_message']}")
    print(f"  AI: {msg['ai_response']}")
```

### Get Messages by Time Range

```python
from datetime import datetime, timedelta

# Get messages from the last 24 hours
end_time = datetime.now()
start_time = end_time - timedelta(days=1)

messages = memory.get_messages(
    start_time=start_time.isoformat(),
    end_time=end_time.isoformat()
)

print(f"Found {len(messages)} messages in the last 24 hours")
```

### Combine Filters

```python
# Get messages for a specific session within a time range
messages = memory.get_messages(
    session_id="session_abc",
    start_time="2025-01-01T00:00:00",
    end_time="2025-01-31T23:59:59",
    limit=50
)
```

### Get Recent Messages for Current Instance

```python
# Get messages for the current instance
recent = memory.get_messages(
    session_id=memory.instance_id,
    limit=10
)
```

---

## Searching Messages

### Basic Text Search

```python
# Search for messages containing specific text (case-insensitive)
results = memory.search_messages("authentication", limit=50)

for msg in results:
    print(f"Session: {msg['session_id']}")
    print(f"User: {msg['user_message'][:100]}...")
    print(f"AI: {msg['ai_response'][:100]}...")
    print()
```

### Search Examples

```python
# Search for error-related messages
errors = memory.search_messages("error", limit=20)

# Search for specific topics
ml_messages = memory.search_messages("machine learning")
auth_messages = memory.search_messages("authentication")

# Search across both user and AI messages
# (Searches in both user_message and ai_response columns)
results = memory.search_messages("deployment")
```

---

## Async Methods

All methods have async versions for use with async/await:

### Async Storage

```python
import asyncio

async def store_conversation():
    memory = ConsciousMemory(tenant_id="user_123")

    result = await memory.alearn(
        user_message="What is async programming?",
        ai_response="Async programming is...",
        session_id="async_session",
        metadata={"type": "async_example"}
    )

    return result

# Run async function
result = asyncio.run(store_conversation())
```

### Async Retrieval

```python
async def retrieve_messages():
    memory = ConsciousMemory(tenant_id="user_123")

    # Get all messages
    messages = await memory.aget_messages(limit=100)

    # Get conversation by session
    conversation = await memory.aget_conversation_by_session("async_session")

    # Search messages
    results = await memory.asearch_messages("async", limit=50)

    return messages, conversation, results
```

### Async with Context Manager

```python
async def process_messages():
    memory = ConsciousMemory(tenant_id="user_123")

    # Store multiple messages
    tasks = []
    for i in range(10):
        task = memory.alearn(
            user_message=f"Question {i}",
            ai_response=f"Answer {i}",
            session_id="batch_session"
        )
        tasks.append(task)

    # Wait for all to complete
    results = await asyncio.gather(*tasks)

    # Retrieve all messages
    conversation = await memory.aget_conversation_by_session("batch_session")

    return conversation
```

---

## Statistics

### Get Message Statistics

```python
# Get statistics including message counts
stats = memory.get_stats()

print(f"Tenant ID: {stats['tenant_id']}")
print(f"Instance ID: {stats['instance_id']}")
print(f"Entities (concepts): {stats['entities']}")
print(f"Auto Messages: {stats['auto_messages']}")
print(f"Full Messages: {stats['messages']}")
print(f"Decisions: {stats['decisions']}")
print(f"Attention Links: {stats['attention_links']}")
print(f"Compound Concepts: {stats['compound_concepts']}")

if stats['cache_enabled']:
    print(f"Cache: {stats['cache']}")
```

### Async Statistics

```python
async def get_stats_async():
    memory = ConsciousMemory(tenant_id="user_123")
    stats = await memory.aget_stats()
    return stats
```

---

## Complete Example

```python
from continuum.core.memory import ConsciousMemory
from datetime import datetime, timedelta

# Initialize memory
memory = ConsciousMemory(tenant_id="customer_support")

# Simulate a customer support conversation
session_id = "support_ticket_12345"

# Store conversation turns
turns = [
    ("I'm having trouble logging in", "I can help you with that. What error are you seeing?"),
    ("It says 'invalid credentials'", "Let's reset your password. I'll send you a reset link."),
    ("Thanks! I got the link", "Great! Once you reset it, try logging in again."),
    ("It worked! Thank you", "You're welcome! Is there anything else I can help with?")
]

for user_msg, ai_msg in turns:
    memory.learn(
        user_message=user_msg,
        ai_response=ai_msg,
        session_id=session_id,
        metadata={"ticket_id": "12345", "category": "authentication"}
    )

# Retrieve the full conversation
conversation = memory.get_conversation_by_session(session_id)
print(f"Support Ticket #{session_id}")
print(f"Total turns: {len(conversation)}")
print()

for i, msg in enumerate(conversation, 1):
    print(f"Turn {i} ({msg['created_at']})")
    print(f"Customer: {msg['user_message']}")
    print(f"Support: {msg['ai_response']}")
    print()

# Search for authentication-related tickets
auth_tickets = memory.search_messages("authentication", limit=100)
print(f"Found {len(auth_tickets)} authentication-related messages")

# Get statistics
stats = memory.get_stats()
print(f"Total support conversations: {stats['messages']}")
print(f"Knowledge concepts extracted: {stats['entities']}")
```

---

## Return Value Structure

### Message Dictionary

Each message returned is a dictionary with the following structure:

```python
{
    'id': 123,                          # Unique message ID
    'user_message': "Full user text",   # Complete user message
    'ai_response': "Full AI text",      # Complete AI response
    'session_id': "session_abc",        # Session identifier
    'created_at': "2025-12-11T10:25:21.963189",  # ISO timestamp
    'tenant_id': "user_123",            # Tenant identifier
    'metadata': {                       # Parsed metadata (dict)
        'custom_key': 'value',
        'tags': ['tag1', 'tag2']
    }
}
```

### LearningResult

The `learn()` method returns a `LearningResult` dataclass:

```python
@dataclass
class LearningResult:
    concepts_extracted: int      # Number of concepts found
    decisions_detected: int      # Number of decisions detected
    links_created: int           # Number of graph links created
    compounds_found: int         # Number of compound concepts found
    tenant_id: str              # Tenant identifier
```

---

## Best Practices

### 1. Use Session IDs

```python
# Group related messages together
import uuid

session_id = str(uuid.uuid4())
for user_msg, ai_msg in conversation_turns:
    memory.learn(user_msg, ai_msg, session_id=session_id)
```

### 2. Add Meaningful Metadata

```python
metadata = {
    "user_id": "user_123",
    "conversation_type": "support",
    "priority": "high",
    "tags": ["billing", "refund"],
    "channel": "web_chat",
    "language": "en"
}

memory.learn(user_msg, ai_msg, session_id=session_id, metadata=metadata)
```

### 3. Batch Retrieval

```python
# Get larger batches for analysis
all_messages = memory.get_messages(limit=1000)

# Process in chunks
chunk_size = 100
for i in range(0, len(all_messages), chunk_size):
    chunk = all_messages[i:i+chunk_size]
    process_chunk(chunk)
```

### 4. Use Time Ranges for Analytics

```python
from datetime import datetime, timedelta

# Daily analytics
today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
yesterday = today - timedelta(days=1)

daily_messages = memory.get_messages(
    start_time=yesterday.isoformat(),
    end_time=today.isoformat()
)

print(f"Messages in last 24h: {len(daily_messages)}")
```

### 5. Combine with Knowledge Graph

```python
# Store message and extract concepts
result = memory.learn(user_msg, ai_msg, session_id=session_id)

# Get the full message history
messages = memory.get_conversation_by_session(session_id)

# Get memory stats showing both
stats = memory.get_stats()
print(f"Conversations: {stats['messages']}")
print(f"Concepts extracted: {stats['entities']}")
print(f"Knowledge links: {stats['attention_links']}")
```

---

## Error Handling

```python
try:
    messages = memory.get_messages(session_id="session_123")
    if not messages:
        print("No messages found for this session")
except Exception as e:
    print(f"Error retrieving messages: {e}")

# Async error handling
async def safe_retrieval():
    try:
        messages = await memory.aget_messages(session_id="session_123")
        return messages
    except Exception as e:
        print(f"Async error: {e}")
        return []
```

---

## Migration Notes

### Existing Code Compatibility

Existing code works without changes:

```python
# Old code - still works
memory.learn(user_msg, ai_msg)

# New code - with session tracking
memory.learn(user_msg, ai_msg, session_id="my_session")
```

### Database Migration

The messages table is created automatically when `ConsciousMemory` is initialized. No manual migration needed.

```python
# First time initialization creates the new table
memory = ConsciousMemory(tenant_id="user_123")
# The messages table is now available
```

---

For more information, see:
- Main documentation: `/docs/api-reference.md`
- Architecture overview: `/docs/ARCHITECTURE.md`
- Full enhancement details: `/MESSAGES_TABLE_ENHANCEMENT.md`
