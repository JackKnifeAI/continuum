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
Synchronization Utilities
=========================

Thread-safe and process-safe synchronization primitives.

Features:
- File-based locking for cross-process coordination
- Decorator for synchronized functions
- Context manager for explicit locking
- Shared (read) and exclusive (write) locks
"""

import fcntl
import time
import functools
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Callable


class FileLock:
    """
    File-based lock for cross-process synchronization.

    Uses fcntl advisory locking to coordinate access across processes.
    Supports both shared (read) and exclusive (write) locks.

    Example:
        # Exclusive lock (default)
        with FileLock("/path/to/file.json"):
            data = read_and_modify_file()

        # Shared lock for reading
        with FileLock("/path/to/file.json", shared=True):
            data = read_file()

        # Or use as context manager with manual control
        lock = FileLock("/path/to/file.json")
        lock.acquire()
        try:
            # Critical section
            pass
        finally:
            lock.release()
    """

    def __init__(self, file_path, shared: bool = False, timeout: float = 30.0):
        """
        Initialize file lock.

        Args:
            file_path: Path to file to lock (str or Path)
            shared: If True, use shared lock (allows multiple readers)
            timeout: Maximum seconds to wait for lock
        """
        self.file_path = Path(file_path)
        self.shared = shared
        self.timeout = timeout
        self._file_handle = None
        self._locked = False

    def acquire(self) -> bool:
        """
        Acquire the lock.

        Returns:
            True if lock acquired successfully

        Raises:
            TimeoutError: If lock cannot be acquired within timeout
        """
        # Ensure file exists
        self.file_path.touch()

        # Open file for locking
        self._file_handle = open(self.file_path, 'a+')

        # Determine lock type
        lock_type = fcntl.LOCK_SH if self.shared else fcntl.LOCK_EX

        # Try to acquire lock with timeout
        start_time = time.time()
        while True:
            try:
                fcntl.flock(self._file_handle, lock_type | fcntl.LOCK_NB)
                self._locked = True
                return True
            except BlockingIOError:
                # Lock is held by another process
                if time.time() - start_time > self.timeout:
                    self._file_handle.close()
                    self._file_handle = None
                    raise TimeoutError(
                        f"Could not acquire lock on {self.file_path} within {self.timeout}s"
                    )
                # Wait a bit and retry
                time.sleep(0.01)

    def release(self):
        """Release the lock."""
        if self._locked and self._file_handle:
            fcntl.flock(self._file_handle, fcntl.LOCK_UN)
            self._file_handle.close()
            self._file_handle = None
            self._locked = False

    def __enter__(self):
        """Context manager entry."""
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release()
        return False

    def __del__(self):
        """Ensure lock is released on deletion."""
        if self._locked:
            self.release()


@contextmanager
def file_lock(file_path, shared: bool = False, timeout: float = 30.0):
    """
    Convenience context manager for file locking.

    Args:
        file_path: Path to file to lock
        shared: If True, use shared lock (allows multiple readers)
        timeout: Maximum seconds to wait for lock

    Example:
        with file_lock("/path/to/file.json"):
            # Exclusive lock - no other process can read or write
            modify_file()

        with file_lock("/path/to/file.json", shared=True):
            # Shared lock - other processes can also read
            read_file()
    """
    lock = FileLock(file_path, shared=shared, timeout=timeout)
    lock.acquire()
    try:
        yield lock
    finally:
        lock.release()


def synchronized(lock_file: str = None, shared: bool = False):
    """
    Decorator to synchronize function execution across processes.

    Args:
        lock_file: Path to lock file (if None, derives from function name)
        shared: If True, use shared lock

    Example:
        @synchronized("/tmp/my_function.lock")
        def my_function():
            # Only one process can execute this at a time
            pass

        # Or with auto-generated lock file
        @synchronized()
        def another_function():
            # Lock file will be /tmp/another_function.lock
            pass
    """
    def decorator(func: Callable) -> Callable:
        # Determine lock file path
        if lock_file is None:
            import tempfile
            path = Path(tempfile.gettempdir()) / f"{func.__name__}.lock"
        else:
            path = Path(lock_file)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with FileLock(path, shared=shared):
                return func(*args, **kwargs)

        return wrapper

    return decorator


class RateLimiter:
    """
    Rate limiter for controlling access frequency.

    Uses file-based state for cross-process rate limiting.

    Example:
        limiter = RateLimiter(
            rate_file="/tmp/api_calls.rate",
            max_calls=100,
            time_window=60  # 100 calls per 60 seconds
        )

        if limiter.can_proceed():
            make_api_call()
        else:
            print("Rate limit exceeded, please wait")
    """

    def __init__(self, rate_file: str, max_calls: int, time_window: float):
        """
        Initialize rate limiter.

        Args:
            rate_file: Path to file storing rate limit state
            max_calls: Maximum number of calls allowed
            time_window: Time window in seconds
        """
        self.rate_file = Path(rate_file)
        self.max_calls = max_calls
        self.time_window = time_window

        # Ensure parent directory exists
        self.rate_file.parent.mkdir(parents=True, exist_ok=True)

    def can_proceed(self) -> bool:
        """
        Check if action can proceed without exceeding rate limit.

        Returns:
            True if action can proceed, False if rate limited
        """
        import json

        with FileLock(self.rate_file):
            # Load current state
            if self.rate_file.exists():
                try:
                    with open(self.rate_file, 'r') as f:
                        state = json.load(f)
                except (json.JSONDecodeError, IOError):
                    state = {"calls": []}
            else:
                state = {"calls": []}

            # Get current time
            now = time.time()

            # Remove calls outside time window
            state["calls"] = [
                call_time for call_time in state["calls"]
                if now - call_time < self.time_window
            ]

            # Check if we can proceed
            if len(state["calls"]) >= self.max_calls:
                return False

            # Record this call
            state["calls"].append(now)

            # Save state
            with open(self.rate_file, 'w') as f:
                json.dump(state, f)

        return True

    def wait_if_needed(self, max_wait: float = None):
        """
        Wait until action can proceed.

        Args:
            max_wait: Maximum seconds to wait (None = wait forever)

        Raises:
            TimeoutError: If max_wait exceeded
        """
        start_time = time.time()

        while not self.can_proceed():
            if max_wait and (time.time() - start_time) > max_wait:
                raise TimeoutError("Rate limit wait timeout exceeded")
            time.sleep(0.1)

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
