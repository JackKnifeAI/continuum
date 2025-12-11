#!/usr/bin/env python3
"""
Test script for FileDigester functionality
"""

import sys
import tempfile
from pathlib import Path

# Add continuum to path
sys.path.insert(0, str(Path(__file__).parent))

from continuum.core.file_digester import FileDigester

def test_digest_text():
    """Test digesting raw text"""
    print("\n=== Testing digest_text ===")

    digester = FileDigester(tenant_id="test_digester")

    text = """
    Machine Learning is a subset of Artificial Intelligence.
    It focuses on building systems that can learn from data.

    Common algorithms include:
    - Neural Networks
    - Decision Trees
    - Support Vector Machines

    Deep Learning is a specialized area of Machine Learning.
    """

    result = digester.digest_text(text, source="test_input")

    print(f"Files processed: {result.files_processed}")
    print(f"Chunks processed: {result.chunks_processed}")
    print(f"Concepts extracted: {result.concepts_extracted}")
    print(f"Links created: {result.links_created}")
    print(f"Errors: {result.errors}")
    print(f"Tenant ID: {result.tenant_id}")

    assert result.files_processed == 1
    assert result.chunks_processed >= 1
    assert result.concepts_extracted > 0
    assert len(result.errors) == 0

    print("✓ digest_text test passed!")
    return True


def test_digest_file():
    """Test digesting a file"""
    print("\n=== Testing digest_file ===")

    digester = FileDigester(tenant_id="test_digester")

    # Create a temporary test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("""# Test Document

This is a test document for the FileDigester.

## Concepts to Extract

- Python programming language
- FastAPI web framework
- RESTful API design
- Database management
- Knowledge graphs

The system should extract these concepts and build connections between them.
""")
        temp_file = f.name

    try:
        result = digester.digest_file(temp_file)

        print(f"Files processed: {result.files_processed}")
        print(f"Chunks processed: {result.chunks_processed}")
        print(f"Concepts extracted: {result.concepts_extracted}")
        print(f"Links created: {result.links_created}")
        print(f"Errors: {result.errors}")

        assert result.files_processed == 1
        assert result.chunks_processed >= 1
        assert result.concepts_extracted > 0
        assert len(result.errors) == 0

        print("✓ digest_file test passed!")
        return True
    finally:
        # Clean up temp file
        Path(temp_file).unlink()


def test_digest_directory():
    """Test digesting a directory"""
    print("\n=== Testing digest_directory ===")

    digester = FileDigester(tenant_id="test_digester")

    # Create a temporary directory with test files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test files
        (temp_path / "file1.md").write_text("# File 1\nThis is about Python and FastAPI.")
        (temp_path / "file2.txt").write_text("Testing with REST APIs and databases.")
        (temp_path / "file3.py").write_text("# Python code\ndef hello(): pass")

        # Create subdirectory
        subdir = temp_path / "subdir"
        subdir.mkdir()
        (subdir / "file4.md").write_text("# Subdirectory file\nMore content here.")

        result = digester.digest_directory(str(temp_path))

        print(f"Files processed: {result.files_processed}")
        print(f"Chunks processed: {result.chunks_processed}")
        print(f"Concepts extracted: {result.concepts_extracted}")
        print(f"Links created: {result.links_created}")
        print(f"Errors: {result.errors}")

        assert result.files_processed >= 3  # At least 3 files should be processed
        assert result.chunks_processed >= 3
        assert result.concepts_extracted > 0

        print("✓ digest_directory test passed!")
        return True


def test_chunking():
    """Test text chunking for large content"""
    print("\n=== Testing chunking ===")

    digester = FileDigester(tenant_id="test_digester", chunk_size=100)

    # Create a long text that will need chunking
    long_text = "This is a test sentence. " * 50  # ~1250 chars

    result = digester.digest_text(long_text, source="chunking_test")

    print(f"Chunks processed: {result.chunks_processed}")
    print(f"Concepts extracted: {result.concepts_extracted}")

    # Should be split into multiple chunks
    assert result.chunks_processed > 1, f"Expected multiple chunks, got {result.chunks_processed}"

    print("✓ Chunking test passed!")
    return True


if __name__ == "__main__":
    print("Starting FileDigester tests...")
    print("=" * 60)

    try:
        test_digest_text()
        test_digest_file()
        test_digest_directory()
        test_chunking()

        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
