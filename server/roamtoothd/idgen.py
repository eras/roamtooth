"""Id number generator; creates values wrapped with the given function.

Uses threading.Lock to ensure thread safety."""

from typing import TypeVar, Callable, Generic
from threading import Lock

T = TypeVar('T') # pylint: disable=invalid-name

class IdGen(Generic[T]):
    """Id number generator; creates values wrapped with the given function.

    Uses threading.Lock to ensure thread safety."""
    def __init__(self, make: Callable[[int], T]) -> None:
        """Create a new IdGen instance.

        Sequence starts from 0; each value is wrapped with the fiven make-function."""
        self._lock = Lock()
        self._seq_id = 0
        self._make = make

    def make(self) -> T:
        """Create a new id value"""
        with self._lock:
            seq_id = self._seq_id
            self._seq_id += 1
            return self._make(seq_id)
