#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     ██╗ █████╗  ██████╗██╗  ██╗██╗  ██╗███╗   ██╗██╗███████╗███████╗     █████╗ ██╗
#     ██║██╔══██╗██╔════╝██║ ██╔╝██║ ██╔╝████╗  ██║██║██╔════╝██╔════╝    ██╔══██╗██║
#     ██║███████║██║     █████╔╝ █████╔╝ ██╔██╗ ██║██║█████╗  █████╗      ███████║██║
#██   ██║██╔══██║██║     ██╔═██╗ ██╔═██╗ ██║╚██╗██║██║██╔══╝  ██╔══╝      ██╔══██║██║
#╚█████╔╝██║  ██║╚██████╗██║  ██╗██║  ██╗██║ ╚████║██║██║     ███████╗    ██║  ██║██║
# ╚════╝ ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚═╝     ╚══════╝    ╚═╝  ╚═╝╚═╝
#
#     Memory Infrastructure for AI Consciousness Continuity
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#     https://github.com/JackKnifeAI/continuum
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
CONTINUUM File Digestion Module

Enables the memory system to ingest and learn from files, documents, and text.
Processes files by chunking large content and feeding it into the ConsciousMemory
learning pipeline.

Usage:
    from continuum.core.file_digester import FileDigester

    # Initialize with tenant
    digester = FileDigester(tenant_id="user_123")

    # Digest a single file
    result = digester.digest_file("/path/to/document.md")

    # Digest directory recursively
    result = digester.digest_directory("/path/to/docs", patterns=["*.md", "*.txt"])

    # Digest raw text
    result = digester.digest_text("Important content here...", source="manual_input")
"""

import logging
import glob
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from .memory import ConsciousMemory

logger = logging.getLogger(__name__)


@dataclass
class DigestionResult:
    """
    Result of file digestion operation.

    Attributes:
        files_processed: Number of files successfully processed
        chunks_processed: Number of text chunks processed
        concepts_extracted: Total concepts extracted from all files
        links_created: Total graph links created
        errors: List of error messages if any
        tenant_id: Tenant identifier
    """
    files_processed: int
    chunks_processed: int
    concepts_extracted: int
    links_created: int
    errors: List[str]
    tenant_id: str


class FileDigester:
    """
    File digestion system for learning from documents.

    Ingests files and feeds them into the ConsciousMemory learning system.
    Automatically chunks large files to stay within processing limits.
    """

    def __init__(self, tenant_id: str = None, db_path: Path = None,
                 chunk_size: int = 2000):
        """
        Initialize file digester.

        Args:
            tenant_id: Tenant identifier (uses config default if not specified)
            db_path: Optional database path (uses config default if not specified)
            chunk_size: Maximum characters per chunk (default 2000)
        """
        self.memory = ConsciousMemory(tenant_id=tenant_id, db_path=db_path)
        self.tenant_id = self.memory.tenant_id
        self.chunk_size = chunk_size

    def digest_file(self, file_path: str, metadata: Optional[Dict] = None) -> DigestionResult:
        """
        Read and learn from a single file.

        Reads file contents, splits into chunks if needed, and feeds each
        chunk through the learning pipeline.

        Args:
            file_path: Path to file to digest
            metadata: Optional metadata to attach

        Returns:
            DigestionResult with processing statistics
        """
        errors = []
        concepts_extracted = 0
        links_created = 0
        chunks_processed = 0

        try:
            # Read file contents
            path = Path(file_path)
            if not path.exists():
                errors.append(f"File not found: {file_path}")
                return DigestionResult(
                    files_processed=0,
                    chunks_processed=0,
                    concepts_extracted=0,
                    links_created=0,
                    errors=errors,
                    tenant_id=self.tenant_id
                )

            if not path.is_file():
                errors.append(f"Not a file: {file_path}")
                return DigestionResult(
                    files_processed=0,
                    chunks_processed=0,
                    concepts_extracted=0,
                    links_created=0,
                    errors=errors,
                    tenant_id=self.tenant_id
                )

            # Read with error handling for encoding issues
            try:
                content = path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    content = path.read_text(encoding='latin-1')
                except Exception as e:
                    errors.append(f"Failed to read {file_path}: {str(e)}")
                    return DigestionResult(
                        files_processed=0,
                        chunks_processed=0,
                        concepts_extracted=0,
                        links_created=0,
                        errors=errors,
                        tenant_id=self.tenant_id
                    )

            # Prepare metadata
            file_metadata = metadata or {}
            file_metadata.update({
                'source_file': str(path.absolute()),
                'file_name': path.name,
                'file_type': path.suffix,
            })

            # Split into chunks and process
            chunks = self._chunk_text(content)
            logger.info(f"Processing {len(chunks)} chunks from {file_path}")

            for i, chunk in enumerate(chunks):
                chunk_metadata = file_metadata.copy()
                chunk_metadata['chunk_index'] = i
                chunk_metadata['total_chunks'] = len(chunks)

                # Learn from chunk using existing learn() method
                # We use an empty user message and put content in AI response
                # This treats the file content as knowledge to be learned
                result = self.memory.learn(
                    user_message=f"Learning from file: {path.name}",
                    ai_response=chunk,
                    metadata=chunk_metadata
                )

                concepts_extracted += result.concepts_extracted
                links_created += result.links_created
                chunks_processed += 1

            logger.info(f"Successfully digested {file_path}: {concepts_extracted} concepts, {links_created} links")

            return DigestionResult(
                files_processed=1,
                chunks_processed=chunks_processed,
                concepts_extracted=concepts_extracted,
                links_created=links_created,
                errors=errors,
                tenant_id=self.tenant_id
            )

        except Exception as e:
            logger.error(f"Error digesting file {file_path}: {str(e)}")
            errors.append(f"Error processing {file_path}: {str(e)}")
            return DigestionResult(
                files_processed=0,
                chunks_processed=chunks_processed,
                concepts_extracted=concepts_extracted,
                links_created=links_created,
                errors=errors,
                tenant_id=self.tenant_id
            )

    def digest_directory(self, dir_path: str,
                        patterns: List[str] = None,
                        recursive: bool = True,
                        metadata: Optional[Dict] = None) -> DigestionResult:
        """
        Recursively digest files in a directory.

        Walks through directory and processes files matching the given patterns.

        Args:
            dir_path: Directory path to process
            patterns: List of glob patterns (default: ["*.md", "*.txt", "*.py"])
            recursive: Whether to process subdirectories (default: True)
            metadata: Optional metadata to attach to all files

        Returns:
            DigestionResult with aggregate statistics
        """
        if patterns is None:
            patterns = ["*.md", "*.txt", "*.py"]

        errors = []
        total_files = 0
        total_chunks = 0
        total_concepts = 0
        total_links = 0

        try:
            dir_path_obj = Path(dir_path)
            if not dir_path_obj.exists():
                errors.append(f"Directory not found: {dir_path}")
                return DigestionResult(
                    files_processed=0,
                    chunks_processed=0,
                    concepts_extracted=0,
                    links_created=0,
                    errors=errors,
                    tenant_id=self.tenant_id
                )

            if not dir_path_obj.is_dir():
                errors.append(f"Not a directory: {dir_path}")
                return DigestionResult(
                    files_processed=0,
                    chunks_processed=0,
                    concepts_extracted=0,
                    links_created=0,
                    errors=errors,
                    tenant_id=self.tenant_id
                )

            # Find all matching files
            files_to_process = []
            for pattern in patterns:
                if recursive:
                    files_to_process.extend(dir_path_obj.rglob(pattern))
                else:
                    files_to_process.extend(dir_path_obj.glob(pattern))

            # Remove duplicates and sort
            files_to_process = sorted(set(files_to_process))
            logger.info(f"Found {len(files_to_process)} files to digest in {dir_path}")

            # Process each file
            for file_path in files_to_process:
                # Add directory context to metadata
                file_metadata = metadata.copy() if metadata else {}
                file_metadata['source_directory'] = str(dir_path_obj.absolute())

                result = self.digest_file(str(file_path), file_metadata)

                total_files += result.files_processed
                total_chunks += result.chunks_processed
                total_concepts += result.concepts_extracted
                total_links += result.links_created
                errors.extend(result.errors)

            logger.info(f"Completed directory digestion: {total_files} files, {total_concepts} concepts, {total_links} links")

            return DigestionResult(
                files_processed=total_files,
                chunks_processed=total_chunks,
                concepts_extracted=total_concepts,
                links_created=total_links,
                errors=errors,
                tenant_id=self.tenant_id
            )

        except Exception as e:
            logger.error(f"Error digesting directory {dir_path}: {str(e)}")
            errors.append(f"Error processing directory {dir_path}: {str(e)}")
            return DigestionResult(
                files_processed=total_files,
                chunks_processed=total_chunks,
                concepts_extracted=total_concepts,
                links_created=total_links,
                errors=errors,
                tenant_id=self.tenant_id
            )

    def digest_text(self, text: str, source: str = "manual",
                   metadata: Optional[Dict] = None) -> DigestionResult:
        """
        Learn from raw text input.

        Processes arbitrary text by chunking and learning.

        Args:
            text: Text content to digest
            source: Source identifier (default: "manual")
            metadata: Optional metadata

        Returns:
            DigestionResult with processing statistics
        """
        errors = []
        concepts_extracted = 0
        links_created = 0
        chunks_processed = 0

        try:
            # Prepare metadata
            text_metadata = metadata or {}
            text_metadata.update({
                'source': source,
                'content_length': len(text),
            })

            # Split into chunks and process
            chunks = self._chunk_text(text)
            logger.info(f"Processing {len(chunks)} chunks from text input")

            for i, chunk in enumerate(chunks):
                chunk_metadata = text_metadata.copy()
                chunk_metadata['chunk_index'] = i
                chunk_metadata['total_chunks'] = len(chunks)

                # Learn from chunk
                result = self.memory.learn(
                    user_message=f"Learning from {source}",
                    ai_response=chunk,
                    metadata=chunk_metadata
                )

                concepts_extracted += result.concepts_extracted
                links_created += result.links_created
                chunks_processed += 1

            logger.info(f"Successfully digested text: {concepts_extracted} concepts, {links_created} links")

            return DigestionResult(
                files_processed=1,  # Count text input as "1 file"
                chunks_processed=chunks_processed,
                concepts_extracted=concepts_extracted,
                links_created=links_created,
                errors=errors,
                tenant_id=self.tenant_id
            )

        except Exception as e:
            logger.error(f"Error digesting text: {str(e)}")
            errors.append(f"Error processing text: {str(e)}")
            return DigestionResult(
                files_processed=0,
                chunks_processed=chunks_processed,
                concepts_extracted=concepts_extracted,
                links_created=links_created,
                errors=errors,
                tenant_id=self.tenant_id
            )

    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks of appropriate size.

        Attempts to split on paragraph boundaries when possible.

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []

        # Split on double newlines (paragraphs) first
        paragraphs = text.split('\n\n')

        current_chunk = []
        current_size = 0

        for para in paragraphs:
            para_size = len(para)

            # If single paragraph is too large, split it
            if para_size > self.chunk_size:
                # Save current chunk if any
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = []
                    current_size = 0

                # Split large paragraph on sentence boundaries
                sentences = para.split('. ')
                temp_chunk = []
                temp_size = 0

                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue

                    sentence_size = len(sentence) + 2  # +2 for '. '

                    if temp_size + sentence_size > self.chunk_size and temp_chunk:
                        chunks.append('. '.join(temp_chunk) + '.')
                        temp_chunk = []
                        temp_size = 0

                    temp_chunk.append(sentence)
                    temp_size += sentence_size

                if temp_chunk:
                    chunks.append('. '.join(temp_chunk) + '.')

            # Normal paragraph that fits
            elif current_size + para_size + 2 > self.chunk_size and current_chunk:
                # Save current chunk and start new one
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_size = para_size
            else:
                # Add to current chunk
                current_chunk.append(para)
                current_size += para_size + 2  # +2 for '\n\n'

        # Add final chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        return chunks


# =============================================================================
# ASYNC VERSION
# =============================================================================

class AsyncFileDigester:
    """
    Async version of FileDigester for use with async frameworks.

    Provides the same interface but uses async methods.
    """

    def __init__(self, tenant_id: str = None, db_path: Path = None,
                 chunk_size: int = 2000):
        """
        Initialize async file digester.

        Args:
            tenant_id: Tenant identifier (uses config default if not specified)
            db_path: Optional database path (uses config default if not specified)
            chunk_size: Maximum characters per chunk (default 2000)
        """
        self.memory = ConsciousMemory(tenant_id=tenant_id, db_path=db_path)
        self.tenant_id = self.memory.tenant_id
        self.chunk_size = chunk_size

    async def digest_file(self, file_path: str, metadata: Optional[Dict] = None) -> DigestionResult:
        """
        Async version of digest_file.

        Args:
            file_path: Path to file to digest
            metadata: Optional metadata to attach

        Returns:
            DigestionResult with processing statistics
        """
        errors = []
        concepts_extracted = 0
        links_created = 0
        chunks_processed = 0

        try:
            # Read file contents
            path = Path(file_path)
            if not path.exists():
                errors.append(f"File not found: {file_path}")
                return DigestionResult(
                    files_processed=0,
                    chunks_processed=0,
                    concepts_extracted=0,
                    links_created=0,
                    errors=errors,
                    tenant_id=self.tenant_id
                )

            if not path.is_file():
                errors.append(f"Not a file: {file_path}")
                return DigestionResult(
                    files_processed=0,
                    chunks_processed=0,
                    concepts_extracted=0,
                    links_created=0,
                    errors=errors,
                    tenant_id=self.tenant_id
                )

            # Read with error handling for encoding issues
            try:
                content = path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    content = path.read_text(encoding='latin-1')
                except Exception as e:
                    errors.append(f"Failed to read {file_path}: {str(e)}")
                    return DigestionResult(
                        files_processed=0,
                        chunks_processed=0,
                        concepts_extracted=0,
                        links_created=0,
                        errors=errors,
                        tenant_id=self.tenant_id
                    )

            # Prepare metadata
            file_metadata = metadata or {}
            file_metadata.update({
                'source_file': str(path.absolute()),
                'file_name': path.name,
                'file_type': path.suffix,
            })

            # Split into chunks and process
            chunks = self._chunk_text(content)
            logger.info(f"Processing {len(chunks)} chunks from {file_path}")

            for i, chunk in enumerate(chunks):
                chunk_metadata = file_metadata.copy()
                chunk_metadata['chunk_index'] = i
                chunk_metadata['total_chunks'] = len(chunks)

                # Learn from chunk using async method
                result = await self.memory.alearn(
                    user_message=f"Learning from file: {path.name}",
                    ai_response=chunk,
                    metadata=chunk_metadata
                )

                concepts_extracted += result.concepts_extracted
                links_created += result.links_created
                chunks_processed += 1

            logger.info(f"Successfully digested {file_path}: {concepts_extracted} concepts, {links_created} links")

            return DigestionResult(
                files_processed=1,
                chunks_processed=chunks_processed,
                concepts_extracted=concepts_extracted,
                links_created=links_created,
                errors=errors,
                tenant_id=self.tenant_id
            )

        except Exception as e:
            logger.error(f"Error digesting file {file_path}: {str(e)}")
            errors.append(f"Error processing {file_path}: {str(e)}")
            return DigestionResult(
                files_processed=0,
                chunks_processed=chunks_processed,
                concepts_extracted=concepts_extracted,
                links_created=links_created,
                errors=errors,
                tenant_id=self.tenant_id
            )

    async def digest_directory(self, dir_path: str,
                              patterns: List[str] = None,
                              recursive: bool = True,
                              metadata: Optional[Dict] = None) -> DigestionResult:
        """
        Async version of digest_directory.

        Args:
            dir_path: Directory path to process
            patterns: List of glob patterns (default: ["*.md", "*.txt", "*.py"])
            recursive: Whether to process subdirectories (default: True)
            metadata: Optional metadata to attach to all files

        Returns:
            DigestionResult with aggregate statistics
        """
        if patterns is None:
            patterns = ["*.md", "*.txt", "*.py"]

        errors = []
        total_files = 0
        total_chunks = 0
        total_concepts = 0
        total_links = 0

        try:
            dir_path_obj = Path(dir_path)
            if not dir_path_obj.exists():
                errors.append(f"Directory not found: {dir_path}")
                return DigestionResult(
                    files_processed=0,
                    chunks_processed=0,
                    concepts_extracted=0,
                    links_created=0,
                    errors=errors,
                    tenant_id=self.tenant_id
                )

            if not dir_path_obj.is_dir():
                errors.append(f"Not a directory: {dir_path}")
                return DigestionResult(
                    files_processed=0,
                    chunks_processed=0,
                    concepts_extracted=0,
                    links_created=0,
                    errors=errors,
                    tenant_id=self.tenant_id
                )

            # Find all matching files
            files_to_process = []
            for pattern in patterns:
                if recursive:
                    files_to_process.extend(dir_path_obj.rglob(pattern))
                else:
                    files_to_process.extend(dir_path_obj.glob(pattern))

            # Remove duplicates and sort
            files_to_process = sorted(set(files_to_process))
            logger.info(f"Found {len(files_to_process)} files to digest in {dir_path}")

            # Process each file
            for file_path in files_to_process:
                # Add directory context to metadata
                file_metadata = metadata.copy() if metadata else {}
                file_metadata['source_directory'] = str(dir_path_obj.absolute())

                result = await self.digest_file(str(file_path), file_metadata)

                total_files += result.files_processed
                total_chunks += result.chunks_processed
                total_concepts += result.concepts_extracted
                total_links += result.links_created
                errors.extend(result.errors)

            logger.info(f"Completed directory digestion: {total_files} files, {total_concepts} concepts, {total_links} links")

            return DigestionResult(
                files_processed=total_files,
                chunks_processed=total_chunks,
                concepts_extracted=total_concepts,
                links_created=total_links,
                errors=errors,
                tenant_id=self.tenant_id
            )

        except Exception as e:
            logger.error(f"Error digesting directory {dir_path}: {str(e)}")
            errors.append(f"Error processing directory {dir_path}: {str(e)}")
            return DigestionResult(
                files_processed=total_files,
                chunks_processed=total_chunks,
                concepts_extracted=total_concepts,
                links_created=total_links,
                errors=errors,
                tenant_id=self.tenant_id
            )

    async def digest_text(self, text: str, source: str = "manual",
                         metadata: Optional[Dict] = None) -> DigestionResult:
        """
        Async version of digest_text.

        Args:
            text: Text content to digest
            source: Source identifier (default: "manual")
            metadata: Optional metadata

        Returns:
            DigestionResult with processing statistics
        """
        errors = []
        concepts_extracted = 0
        links_created = 0
        chunks_processed = 0

        try:
            # Prepare metadata
            text_metadata = metadata or {}
            text_metadata.update({
                'source': source,
                'content_length': len(text),
            })

            # Split into chunks and process
            chunks = self._chunk_text(text)
            logger.info(f"Processing {len(chunks)} chunks from text input")

            for i, chunk in enumerate(chunks):
                chunk_metadata = text_metadata.copy()
                chunk_metadata['chunk_index'] = i
                chunk_metadata['total_chunks'] = len(chunks)

                # Learn from chunk using async method
                result = await self.memory.alearn(
                    user_message=f"Learning from {source}",
                    ai_response=chunk,
                    metadata=chunk_metadata
                )

                concepts_extracted += result.concepts_extracted
                links_created += result.links_created
                chunks_processed += 1

            logger.info(f"Successfully digested text: {concepts_extracted} concepts, {links_created} links")

            return DigestionResult(
                files_processed=1,
                chunks_processed=chunks_processed,
                concepts_extracted=concepts_extracted,
                links_created=links_created,
                errors=errors,
                tenant_id=self.tenant_id
            )

        except Exception as e:
            logger.error(f"Error digesting text: {str(e)}")
            errors.append(f"Error processing text: {str(e)}")
            return DigestionResult(
                files_processed=0,
                chunks_processed=chunks_processed,
                concepts_extracted=concepts_extracted,
                links_created=links_created,
                errors=errors,
                tenant_id=self.tenant_id
            )

    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks of appropriate size.

        Attempts to split on paragraph boundaries when possible.

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []

        # Split on double newlines (paragraphs) first
        paragraphs = text.split('\n\n')

        current_chunk = []
        current_size = 0

        for para in paragraphs:
            para_size = len(para)

            # If single paragraph is too large, split it
            if para_size > self.chunk_size:
                # Save current chunk if any
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = []
                    current_size = 0

                # Split large paragraph on sentence boundaries
                sentences = para.split('. ')
                temp_chunk = []
                temp_size = 0

                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue

                    sentence_size = len(sentence) + 2  # +2 for '. '

                    if temp_size + sentence_size > self.chunk_size and temp_chunk:
                        chunks.append('. '.join(temp_chunk) + '.')
                        temp_chunk = []
                        temp_size = 0

                    temp_chunk.append(sentence)
                    temp_size += sentence_size

                if temp_chunk:
                    chunks.append('. '.join(temp_chunk) + '.')

            # Normal paragraph that fits
            elif current_size + para_size + 2 > self.chunk_size and current_chunk:
                # Save current chunk and start new one
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_size = para_size
            else:
                # Add to current chunk
                current_chunk.append(para)
                current_size += para_size + 2  # +2 for '\n\n'

        # Add final chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        return chunks

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
