"""MQueue is a queueing primitive that provides composing new queues
from selecting ("choose") and mapping ("map") other queues.

For base use you create instances of MQueue that you can put and take
elements to and from. If you need to read from multiple MQueues, you
can use "select" to do that directly, but "choose" if you want to
construct a new MQueueBase that is takeable when any of its source
queues has data available.

MQueues are unbounded in their size and sending to and taking from a
queue is non-blocking. The blocking way to read from a queue is to use
the top-level "take" method.

Copyright 2020 Erkki Seppälä <flux@inside.org>
License: MIT

"""

from typing import Callable, Deque, Dict, Generic, List, NewType, Optional, Tuple, TypeVar, Union, Sequence, overload
from collections import deque
from threading import Lock, Condition, Thread
from abc import ABC, abstractclassmethod
import time
import unittest

from roamtoothd.idgen import IdGen

T = TypeVar('T') # pylint: disable=invalid-name
U = TypeVar('U') # pylint: disable=invalid-name
V = TypeVar('V') # pylint: disable=invalid-name

QueueId = NewType('QueueId', int)

Callback = Callable[[Optional[Exception]], None]
CallbackId = NewType('CallbackId', int)

class NoInputs(Exception):
    """You provided an empty list of MQueues to select"""

callback_id_gen: IdGen[CallbackId] = IdGen(CallbackId)

class ValueWrapper(Generic[T]):
    """Wrap values inside a class; used to overcome mypy type checking woes.

    We cannot use type variables for isinstance checks, but we can use ValueWrapper."""
    def __init__(self, value: T):
        self.value = value

class MQueueBase(ABC, Generic[T]):
    """Base class for MQueue."""
    @abstractclassmethod
    def take_mapped_or_add_callback(self, callback: Callback, mapping: Callable[[T], U]) -> \
        Union[CallbackId, ValueWrapper[U]]:
        """Either take (remove from queue) a value from the queue, or if the queue is empty, install the
        callback. In that case the CallbackId for removal is returned.

        This operation is done with the lock held, but the lock is not held when calling the
        callback."""

    def take_or_add_callback(self, callback: Callback) -> \
        Union[CallbackId, ValueWrapper[T]]:
        """A version of take_mapped_or_add_callback that doesn't use a mappign function."""
        return self.take_mapped_or_add_callback(callback, lambda x: x)

    @abstractclassmethod
    def remove_callback(self, callback_id: CallbackId) -> None:
        """Remove a callback by its id. If the callback is not installed, this is a no-op."""

    @abstractclassmethod
    def take_mapped(self, mapping: Callable[[T], U]) -> Optional[U]:
        """Non-blocking take that performs mapping holding the internal lock.

        This allows for consistent behavior should the mapping function throw;
        in that case the value is not removed from the Queue and remains to be
        collected by a source that doesn't fail reading it."""

    def take_nonblock(self) -> Optional[T]:
        """Non-blocking take"""
        return self.take_mapped(lambda x: x)

    def map(self, mapping: Callable[[T], U]) -> "MQueueMapped[T, U]":
        """Returna new MQueueMapped that behaves as this one, but has its values mapped with the given
        mapping function."""
        return MQueueMapped(self, mapping)

class MQueue(MQueueBase[T]):
    """MQueue is a multi-selectable Queue

    In other words, you can wait for any one of multiple MQueue
    objects to be readable."""

    _queue_id_gen: IdGen[QueueId] = IdGen(QueueId)

    def __init__(self) -> None:
        # used for ordering locking to eliminate deadlocks
        self.queue_id = MQueue._queue_id_gen.make()
        self._messages: Deque[T] = deque()
        self._lock = Lock()
        #self._new_data = Condition(self._lock)
        self._callbacks: Dict[CallbackId, Callback] = {}

    def put(self, value: T) -> None:
        """Puts in a new value to this queue. Non-blocking."""
        callbacks: List[Callback] = []
        with self._lock:
            self._messages.append(value)
            callbacks = [cb[1] for cb in self._callbacks.items()]
            self._callbacks = {}
            #self._new_data.notify_all()
        for callback in callbacks:
            callback(None)

    def take_mapped(self, mapping: Callable[[T], U]) -> Optional[U]:
        """Take a value mapped with the given mapping function.

        If there is no value in the queue, return None.

        Mapping is performed with the MQueue lock held."""
        with self._lock:
            if self._messages:
                value = self._messages.popleft()
                try:
                    ret_value = mapping(value)
                except:
                    self._messages.appendleft(value)
                    raise
                return ret_value
            else:
                return None

    def take_mapped_or_add_callback(self, callback: Callback, mapping: Callable[[T], U]) -> \
        Union[CallbackId, ValueWrapper[U]]:
        """Returns the value is one is available, in which case no callback is installed.

        Otherwise installs the callback and returns its id.
        """

        # watch out for tricky flow..
        with self._lock:
            if self._messages:
                value = self._messages.popleft()
                try:
                    return ValueWrapper(mapping(value))
                except:
                    self._messages.appendleft(value)
                    raise
            else:
                callback_id = callback_id_gen.make()
                self._callbacks[callback_id] = callback
                return callback_id

    def remove_callback(self, callback_id: CallbackId) -> None:
        """Remove a callback by its id."""
        with self._lock:
            if callback_id in self._callbacks:
                del self._callbacks[callback_id]

class MQueueMapped(MQueueBase[U], Generic[T, U]):
    """Given an MQueueBase[T] and a mapping function from T to U, perform mapping if its values to U."""
    def __init__(self, parent: MQueueBase[T], mapping: Callable[[T], U]) -> None:
        self.parent = parent
        self.mapping = mapping

    def take_mapped(self, mapping: Callable[[U], V]) -> Optional[V]:
        """Take a mapped value.

        Of course, the mapping is done in top of the mapping performed by the object itself.

        """
        return self.parent.take_mapped(lambda x: mapping(self.mapping(x)))

    def take_mapped_or_add_callback(self, callback: Callback, mapping: Callable[[U], V]) -> \
        Union[CallbackId, ValueWrapper[V]]:
        """Returns a value or installs a callback."""
        return self.parent.take_mapped_or_add_callback(callback, lambda x: mapping(self.mapping(x)))

    def remove_callback(self, callback_id: CallbackId) -> None:
        """Remove given callback."""
        return self.parent.remove_callback(callback_id)

class MQueueSelect(MQueueBase[T]):
    """Given multiple MQueueBases, activate as soon as one of them becomes active."""
    def __init__(self, queues: Sequence[MQueueBase[T]]) -> None:
        self.queues = queues
        self._callbacks: Dict[CallbackId, Dict[int, Tuple[MQueueBase[T], CallbackId]]] = {}

    def take_mapped(self, mapping: Callable[[T], U]) -> Optional[U]:
        """Takes a mapped value from the queues (or None if none available)"""
        for queue in self.queues:
            value = queue.take_mapped(mapping)
            if value is not None:
                return value
        return None

    def take_mapped_or_add_callback(self, callback: Callback, mapping: Callable[[T], U]) -> \
        Union[CallbackId, ValueWrapper[U]]:
        """Take a mapped value from the queues or installs callbacks."""

        callback_id = callback_id_gen.make()

        def wrapped_callback(incoming_exception: Optional[Exception]) -> None:
            self.remove_callback(callback_id)
            try:
                callback(incoming_exception)
            except Exception as exn: # pylint: disable=broad-except
                callback(exn)

        callback_ids: Dict[int, Tuple[MQueueBase[T], CallbackId]] = {}

        def cancel_callbacks() -> None:
            for _, callback_info in callback_ids.items():
                callback_info[0].remove_callback(callback_info[1])

        queue_index = 0
        for queue in self.queues:
            try:
                value = queue.take_mapped_or_add_callback(wrapped_callback, mapping)
                if isinstance(value, ValueWrapper):
                    cancel_callbacks()
                    return value
                else:
                    callback_ids[queue_index] = (queue, value)
                    queue_index += 1
            except:
                cancel_callbacks()
                raise

        callback_id = callback_id_gen.make()
        self._callbacks[callback_id] = callback_ids
        return callback_id

    def remove_callback(self, callback_id: CallbackId) -> None:
        """Remove callback by its id."""
        if callback_id in self._callbacks:
            callbacks = self._callbacks[callback_id]
            del self._callbacks[callback_id]
            for _, callback_info in callbacks.items():
                callback_info[0].remove_callback(callback_info[1])

@overload
def take(queue: MQueueBase[T]) -> T: # pylint: disable=missing-function-docstring
    ...

@overload
def take(queue: MQueueBase[T], timeout: Optional[float]) -> Optional[T]: # pylint: disable=missing-function-docstring
    ...

def take(queue: MQueueBase[T], timeout: Optional[float] = None) -> Optional[T]:
    """Given a queue, take a value from, possibly limited by the given timeout.

    If timeout expires the function returns None."""
    deadline = time.monotonic() + timeout if timeout is not None else None

    def timer_expired() -> bool:
        return deadline is not None and time.monotonic() >= deadline

    result_available = Condition()
    got_result: List[Optional[T]] = [None]
    got_exception: List[Optional[Exception]] = [None]
    local_result: Optional[ValueWrapper[T]] = None
    local_exception: Optional[Exception] = None
    while local_result is None and local_exception is None and not timer_expired():
        def callback(exception: Optional[Exception]) -> None:
            with result_available:
                if exception is not None:
                    got_exception[0] = exception
                else:
                    try:
                        got_result[0] = queue.take_nonblock()
                    except Exception as exn: # pylint: disable=broad-except
                        got_exception[0] = exn
                result_available.notify()

        take_result = queue.take_or_add_callback(callback)

        if isinstance(take_result, ValueWrapper):
            local_result = take_result

        with result_available:
            while local_result is None and local_exception is None and not timer_expired(): # type: ignore
                if deadline is None:
                    result_available.wait()
                else:
                    time_left = deadline - time.monotonic()
                    if time_left > 0:
                        result_available.wait(time_left)
                if got_exception is not None:
                    local_exception = got_exception[0]
                if got_result[0] is not None:
                    local_result = ValueWrapper(got_result[0])

        if isinstance(take_result, int):
            queue.remove_callback(take_result)

    if local_exception is not None:
        raise local_exception # pylint: disable=raising-bad-type
    else:
        return local_result.value if local_result else None

def choose(queues: Sequence[MQueueBase[T]]) -> MQueueSelect[T]:
    """Note: if queues is empty, this will never activate."""
    return MQueueSelect(queues)

@overload
def select(queues: Sequence[MQueueBase[T]]) -> T: # pylint: disable=missing-function-docstring
    ...

@overload
def select(queues: Sequence[MQueueBase[T]], timeout: Optional[float]) -> Optional[T]: # pylint: disable=missing-function-docstring
    ...

def select(queues: Sequence[MQueueBase[T]], timeout: Optional[float] = None) -> Optional[T]:
    """Given a sequence of MQueues, return the first value it finds from them, within the optional
    timeout.

    If the timeout expires, returns None.

    Basically chains take and choose together.

    If the queues list is empty, raises NoInputs.
    """
    if not queues:
        raise NoInputs
    return take(choose(queues), timeout)

class TestExn(Exception):
    """Test exception used in tests"""

class TestMQueueu(unittest.TestCase):
    """MQueue tests"""
    def test_empty(self) -> None:
        """Test taking from an empty queue."""
        queue: MQueue[int] = MQueue()
        self.assertEqual(queue.take_nonblock(), None)

    def test_simple(self) -> None:
        """Test taking a value from a queue with one value."""
        queue: MQueue[int] = MQueue()
        queue.put(42)
        self.assertEqual(queue.take_nonblock(), 42)

    def test_callback(self) -> None:
        """Test invoking a callback then taking a value frmo a queue."""
        queue: MQueue[int] = MQueue()
        callback_called = [0]
        def callback(_: Optional[Exception]) -> None:
            callback_called[0] += 1
        callback_id = queue.take_or_add_callback(callback)
        self.assertIsNotNone(callback_id)
        queue.put(42)
        self.assertEqual(queue.take_nonblock(), 42)
        self.assertEqual(callback_called[0], 1)

    def test_select_0(self) -> None:
        """Tests that selecting from no queues results in an exception."""
        with self.assertRaises(NoInputs):
            select([], timeout=None)

    def test_select_timeout_1(self) -> None:
        """Tests that timeout works when queue receives no data."""
        queue: MQueue[int] = MQueue()
        value = select([queue], timeout=0.1)
        self.assertEqual(value, None)
        self.assertEqual(queue._callbacks, {}) # pylint: disable=protected-access

    def test_select_timeout_2(self) -> None:
        """Tests that timeout works when the two queues receive no data."""
        queue1: MQueue[int] = MQueue()
        queue2: MQueue[int] = MQueue()
        value = select([queue1, queue2], timeout=0.1)
        self.assertEqual(value, None)
        self.assertEqual(queue1._callbacks, {}) # pylint: disable=protected-access
        self.assertEqual(queue2._callbacks, {}) # pylint: disable=protected-access

    def test_select_1(self) -> None:
        """Test that select works with a queue with one value."""
        queue: MQueue[int] = MQueue()
        queue.put(42)
        value = select([queue], timeout=None)
        self.assertEqual(value, 42)
        self.assertEqual(queue._callbacks, {}) # pylint: disable=protected-access

    def test_select_2(self) -> None:
        """Test that select works with two queues, each with one value."""
        queue1: MQueue[int] = MQueue()
        queue1.put(1)
        queue2: MQueue[int] = MQueue()
        queue2.put(2)
        value1 = select([queue1, queue2], timeout=None)
        self.assertTrue(value1 in [1, 2])
        value2 = select([queue1, queue2], timeout=None)
        self.assertTrue(value2 in [1, 2] and value2 != value1)
        self.assertEqual(queue1._callbacks, {}) # pylint: disable=protected-access
        self.assertEqual(queue2._callbacks, {}) # pylint: disable=protected-access

    def test_select_live(self) -> None:
        """Test that select works with one value, when the value is put in in an another thread."""
        queue1: MQueue[int] = MQueue()
        def thread() -> None:
            time.sleep(0.05)
            queue1.put(1)
        thread_handle = Thread(target=thread)
        thread_handle.start()
        value = select([queue1], timeout=0.2)
        self.assertEqual(value, 1)
        self.assertEqual(queue1._callbacks, {}) # pylint: disable=protected-access

    def test_select_live2(self) -> None:
        """Tests that select works with two values, values put into separate queues in another thread. """
        queue1: MQueue[int] = MQueue()
        queue2: MQueue[int] = MQueue()
        def thread() -> None:
            time.sleep(0.05)
            queue1.put(1)
            time.sleep(0.05)
            queue2.put(2)
        thread_handle = Thread(target=thread)
        thread_handle.start()
        value = select([queue1, queue2], timeout=0.1)
        self.assertEqual(value, 1)
        value = select([queue1, queue2], timeout=0.1)
        self.assertEqual(value, 2)
        self.assertEqual(queue1._callbacks, {}) # pylint: disable=protected-access
        self.assertEqual(queue2._callbacks, {}) # pylint: disable=protected-access

    def test_map(self) -> None:
        """Test that map works with take_nonblock."""
        queue1: MQueue[int] = MQueue()
        queue1.put(1)
        qm1 = queue1.map(lambda x: x + 1)
        value = qm1.take_nonblock()
        self.assertEqual(value, 2)
        self.assertEqual(queue1._callbacks, {}) # pylint: disable=protected-access

    def test_map_select_1(self) -> None:
        """Test that map works with select."""
        queue1: MQueue[int] = MQueue()
        queue1.put(1)
        value = select([queue1.map(lambda x: x + 1)])
        self.assertEqual(value, 2)
        self.assertEqual(queue1._callbacks, {}) # pylint: disable=protected-access

    def test_map_select_2(self) -> None:
        """Test that map works with select, with two queues."""
        queue1: MQueue[int] = MQueue()
        queue1.put(0)
        queue2: MQueue[int] = MQueue()
        queue2.put(10)
        value1 = select([queue1.map(lambda x: x + 1),
                         queue2.map(lambda x: x + 1)])
        self.assertTrue(value1 in [1, 11])
        value2 = select([queue1.map(lambda x: x + 1),
                         queue2.map(lambda x: x + 1)])
        self.assertTrue(value2 in [1, 11] and value2 != value1)
        self.assertEqual(queue1._callbacks, {}) # pylint: disable=protected-access
        self.assertEqual(queue2._callbacks, {}) # pylint: disable=protected-access

    def test_map_select_raise_1(self) -> None:
        """Test that map works with select and a risen exception."""
        queue1: MQueue[int] = MQueue()
        queue1.put(0)
        with self.assertRaises(TestExn):
            def failer(i: int) -> int:
                raise TestExn()
            select([queue1.map(failer)])
        self.assertEqual(queue1._callbacks, {}) # pylint: disable=protected-access

    def test_select_live_raise(self) -> None:
        """Test that map works with select and a risen exception when the value is put in in an another thread."""
        queue1: MQueue[int] = MQueue()
        def thread() -> None:
            time.sleep(0.05)
            queue1.put(1)
        thread_handle = Thread(target=thread)
        thread_handle.start()
        with self.assertRaises(TestExn):
            def failer(i: int) -> int:
                raise TestExn()
            select([queue1.map(failer)])
        self.assertEqual(queue1._callbacks, {}) # pylint: disable=protected-access

    def test_select_live_raise2(self) -> None:
        """Test that reading values from a queue works even if the mapping function throw an exception once."""
        queue1: MQueue[int] = MQueue()
        def thread() -> None:
            time.sleep(0.05)
            queue1.put(1)
            queue1.put(2)
        thread_handle = Thread(target=thread)
        thread_handle.start()
        count = [0]
        def failer(i: int) -> int:
            count[0] += 1
            if count[0] == 1:
                raise TestExn()
            else:
                return i
        source = [queue1.map(failer)]
        with self.assertRaises(TestExn):
            value = select(source)
        value = select(source)
        self.assertEqual(value, 1)
        value = select(source)
        self.assertEqual(value, 2)
        self.assertEqual(queue1._callbacks, {}) # pylint: disable=protected-access

    def test_select_deep1(self) -> None:
        """Test that choose inside a choose works."""
        queue1: MQueue[int] = MQueue()
        queue1.put(0)
        value = take(choose([choose([queue1.map(lambda x: x + 1)])]))
        self.assertEqual(value, 1)
        self.assertEqual(queue1._callbacks, {}) # pylint: disable=protected-access

    def test_select_deep2(self) -> None:
        """Test that choose inside a choose works, when different levels are used."""
        queue1: MQueue[int] = MQueue()
        queue1.put(0)
        queue2: MQueue[int] = MQueue()
        queue2.put(10)
        source = choose([choose([queue1.map(lambda x: x + 1)]),
                         queue2.map(lambda x: x + 1)])
        value1 = take(source)
        self.assertTrue(value1 in [1, 11])
        value2 = take(source)
        self.assertTrue(value2 in [1, 11] and value2 != value1)
        self.assertEqual(queue1._callbacks, {}) # pylint: disable=protected-access

if __name__ == '__main__':
    unittest.main()
