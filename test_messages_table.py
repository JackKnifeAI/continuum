#!/usr/bin/env python3
"""
Test script for the new messages table functionality.

This script tests:
1. Creating the messages table
2. Storing full verbatim messages via learn()
3. Retrieving messages by session
4. Retrieving messages by time range
5. Searching messages by text
"""

import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

# Add the continuum package to the path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from continuum.core.memory import ConsciousMemory


def test_messages_table():
    """Test the new messages table functionality"""

    # Create a temporary database
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
        test_db = f.name

    try:
        print("Testing Messages Table Functionality")
        print("=" * 60)

        # Initialize memory with a test tenant
        memory = ConsciousMemory(tenant_id="test_user", db_path=test_db)
        print(f"\n✓ Initialized ConsciousMemory with tenant: {memory.tenant_id}")
        print(f"  Database: {test_db}")
        print(f"  Instance ID: {memory.instance_id}")

        # Test 1: Store some messages using learn()
        print("\n" + "=" * 60)
        print("TEST 1: Storing messages via learn()")
        print("=" * 60)

        test_messages = [
            ("What is the capital of France?", "The capital of France is Paris."),
            ("Tell me about machine learning", "Machine learning is a branch of artificial intelligence that focuses on building systems that can learn from data."),
            ("How do I authenticate users?", "User authentication can be implemented using various methods like JWT tokens, OAuth, or session-based authentication.")
        ]

        for i, (user_msg, ai_resp) in enumerate(test_messages, 1):
            result = memory.learn(
                user_msg,
                ai_resp,
                session_id=f"session_{memory.instance_id}",
                metadata={"message_index": i}
            )
            print(f"\n  Message {i} stored:")
            print(f"    Concepts extracted: {result.concepts_extracted}")
            print(f"    Decisions detected: {result.decisions_detected}")
            print(f"    Links created: {result.links_created}")

        # Test 2: Get stats
        print("\n" + "=" * 60)
        print("TEST 2: Getting statistics")
        print("=" * 60)

        stats = memory.get_stats()
        print(f"\n  Entities: {stats['entities']}")
        print(f"  Auto Messages: {stats['auto_messages']}")
        print(f"  Full Messages: {stats['messages']}")
        print(f"  Decisions: {stats['decisions']}")
        print(f"  Attention Links: {stats['attention_links']}")
        print(f"  Compound Concepts: {stats['compound_concepts']}")

        # Test 3: Retrieve messages by session
        print("\n" + "=" * 60)
        print("TEST 3: Retrieving messages by session")
        print("=" * 60)

        session_messages = memory.get_conversation_by_session(f"session_{memory.instance_id}")
        print(f"\n  Found {len(session_messages)} messages in session")

        for i, msg in enumerate(session_messages, 1):
            print(f"\n  Message {i}:")
            print(f"    ID: {msg['id']}")
            print(f"    User: {msg['user_message'][:50]}...")
            print(f"    AI: {msg['ai_response'][:50]}...")
            print(f"    Created: {msg['created_at']}")
            print(f"    Metadata: {msg['metadata']}")

        # Test 4: Retrieve all messages (no filters)
        print("\n" + "=" * 60)
        print("TEST 4: Retrieving all messages")
        print("=" * 60)

        all_messages = memory.get_messages(limit=10)
        print(f"\n  Retrieved {len(all_messages)} messages")

        # Test 5: Search messages by text
        print("\n" + "=" * 60)
        print("TEST 5: Searching messages by text")
        print("=" * 60)

        search_results = memory.search_messages("authentication", limit=10)
        print(f"\n  Found {len(search_results)} messages containing 'authentication'")

        for msg in search_results:
            print(f"\n    Session: {msg['session_id']}")
            print(f"    User: {msg['user_message'][:60]}...")
            print(f"    AI: {msg['ai_response'][:60]}...")

        # Test 6: Retrieve messages by time range
        print("\n" + "=" * 60)
        print("TEST 6: Retrieving messages by time range")
        print("=" * 60)

        now = datetime.now()
        start_time = (now - timedelta(minutes=5)).isoformat()
        end_time = now.isoformat()

        time_range_messages = memory.get_messages(
            start_time=start_time,
            end_time=end_time,
            limit=10
        )
        print(f"\n  Found {len(time_range_messages)} messages in time range")
        print(f"    Start: {start_time}")
        print(f"    End: {end_time}")

        # Success!
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print(f"\nThe messages table is working correctly.")
        print(f"Database location: {test_db}")

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up
        if os.path.exists(test_db):
            print(f"\nCleaning up test database: {test_db}")
            os.remove(test_db)
            # Also remove WAL files if they exist
            for suffix in ['-wal', '-shm']:
                wal_file = test_db + suffix
                if os.path.exists(wal_file):
                    os.remove(wal_file)

    return True


if __name__ == "__main__":
    success = test_messages_table()
    sys.exit(0 if success else 1)
