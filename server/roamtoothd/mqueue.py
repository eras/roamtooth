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
from threading import Lock, Condition, Thread, RLock
from abc import ABC, abstractclassmethod
import time
import unittest

T = TypeVar('T')
U = TypeVar('U')
V = TypeVar('V')

QueueId = NewType('QueueId', int)

Callback = Callable[[Optional[Exception]], None]
CallbackId = NewType('CallbackId', int)

class NoInputs(Exception):
    """You provided an empty list of MQueues to select"""
    pass

class IdGen(Generic[T]):
    def __init__(self, make: Callable[[int], T]) -> None:
        self._lock = Lock()
        self._id = 0
        self._make = make

    def make(self) -> T:
        with self._lock:
            id = self._id
            self._id += 1
            return self._make(id)

callback_id_gen : IdGen[CallbackId] = IdGen(lambda x: CallbackId(x))

class ValueWrapper(Generic[T]):
    def __init__(self, value: T):
        self.value = value

class MQueueBase(ABC, Generic[T]):
    @abstractclassmethod
    def take_mapped_or_add_callback(self, callback: Callback, mapping: Callable[[T], U]) -> \
        Union[CallbackId, ValueWrapper[U]]:
        pass

    def take_or_add_callback(self, callback: Callback) -> \
        Union[CallbackId, ValueWrapper[T]]:
        return self.take_mapped_or_add_callback(callback, lambda x: x)

    @abstractclassmethod
    def remove_callback(self, callback_id: CallbackId) -> None:
        pass

    @abstractclassmethod
    def take_mapped(self, mapping: Callable[[T], U]) -> Optional[U]:
        """Non-blocking take that performs mapping holding the internal lock.

        This allows for consistent behavior should the mapping function throw;
        in that case the value is not removed from the Queue and remains to be
        collected by a source that doesn't fail reading it."""
        pass

    def take_nonblock(self) -> Optional[T]:
        """Non-blocking take"""
        return self.take_mapped(lambda x: x)

    def map(self, mapping: Callable[[T], U]) -> "MQueueMapped[T, U]":
        return MQueueMapped(self, mapping)

class MQueue(MQueueBase[T]):
    """MQueue is a multi-selectable Queue

In other words, you can wait for any one of multiple MQueue
objects to be readable."""

    _id_gen : IdGen[QueueId] = IdGen(lambda x: QueueId(x))

    def __init__(self) -> None:
        # used for ordering locking to eliminate deadlocks
        self.id = MQueue._id_gen.make()
        self._messages : Deque[T] = deque()
        self._lock = Lock()
        #self._new_data = Condition(self._lock)
        self._callbacks : Dict[CallbackId, Callback] = {}

    def put(self, value: T) -> None:
        callbacks : List[Callback] = []
        with self._lock:
            self._messages.append(value)
            callbacks = [cb[1] for cb in self._callbacks.items()]
            self._callbacks = {}
            #self._new_data.notify_all()
        for cb in callbacks:
            cb(None)

    def take_mapped(self, mapping: Callable[[T], U]) -> Optional[U]:
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
        with self._lock:
            if callback_id in self._callbacks:
                del self._callbacks[callback_id]

class MQueueMapped(MQueueBase[U], Generic[T, U]):
    def __init__(self, parent: MQueueBase[T], mapping: Callable[[T], U]) -> None:
        self.parent = parent
        self.mapping = mapping

    def take_mapped(self, mapping: Callable[[U], V]) -> Optional[V]:
        return self.parent.take_mapped(lambda x: mapping(self.mapping(x)))

    def take_mapped_or_add_callback(self, callback: Callback, mapping: Callable[[U], V]) -> \
        Union[CallbackId, ValueWrapper[V]]:
        return self.parent.take_mapped_or_add_callback(callback, lambda x: mapping(self.mapping(x)))

    def remove_callback(self, callback_id: CallbackId) -> None:
        return self.parent.remove_callback(callback_id)

class MQueueSelect(MQueueBase[T]):
    def __init__(self, queues: Sequence[MQueueBase[T]]) -> None:
        self.queues = queues
        self._callbacks : Dict[CallbackId, Dict[int, Tuple[MQueueBase[T], CallbackId]]] = {}

    def take_mapped(self, mapping: Callable[[T], U]) -> Optional[U]:
        for queue in self.queues:
            value = queue.take_mapped(lambda x: mapping(x))
            if value is not None:
                return value
        return None

    def take_mapped_or_add_callback(self, callback: Callback, mapping: Callable[[T], U]) -> \
        Union[CallbackId, ValueWrapper[U]]:

        callback_id = callback_id_gen.make()
        exception : List[Optional[Exception]] = [None]
        def wrapped_callback(incoming_exception: Optional[Exception]) -> None:
            self.remove_callback(callback_id)
            if incoming_exception:
                exception = incoming_exception
            else:
                try:
                    callback(None)
                except Exception as exn:
                    exception = exn

        callback_ids : Dict[int, Tuple[MQueueBase[T], CallbackId]] = {}

        def cancel_callbacks() -> None:
            for queue_index, callback_info in callback_ids.items():
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
        if callback_id in self._callbacks:
            callbacks = self._callbacks[callback_id]
            del self._callbacks[callback_id]
            for queue_index, callback_info in callbacks.items():
                callback_info[0].remove_callback(callback_info[1])

@overload
def take(queue: MQueueBase[T]) -> T: ...

@overload
def take(queue: MQueueBase[T], timeout: Optional[float]) -> Optional[T]: ...

def take(queue: MQueueBase[T], timeout: Optional[float] = None) -> Optional[T]:
    deadline = time.monotonic() + timeout if timeout is not None else None

    def timer_expired() -> bool:
        return deadline is not None and time.monotonic() >= deadline

    result_available = Condition()
    got_result : List[Optional[T]] = [None]
    got_exception: List[Optional[Exception]] = [None]
    local_result : Optional[ValueWrapper[T]] = None
    local_exception : Optional[Exception] = None
    while local_result is None and local_exception is None and not timer_expired():
        def callback(exception: Optional[Exception]) -> None:
            with result_available:
                if exception is not None:
                    got_exception[0] = exception
                else:
                    try:
                        got_result[0] = queue.take_nonblock()
                    except Exception as exn:
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
        raise local_exception
    else:
        return local_result.value if local_result else None

def choose(queues: Sequence[MQueueBase[T]]) -> MQueueSelect[T]:
    """Note: if queues is empty, this will never activate."""
    return MQueueSelect(queues)

@overload
def select(queues: Sequence[MQueueBase[T]]) -> T: ...

@overload
def select(queues: Sequence[MQueueBase[T]], timeout: Optional[float]) -> Optional[T]: ...

def select(queues: Sequence[MQueueBase[T]], timeout: Optional[float] = None) -> Optional[T]:
    if not queues:
        raise NoInputs
    return take(choose(queues), timeout)

class TestExn(Exception):
    pass

class TestMQueueu(unittest.TestCase):
    def test_empty(self) -> None:
        q : MQueue[int] = MQueue()
        self.assertEqual(q.take_nonblock(), None)

    def test_simple(self) -> None:
        q : MQueue[int] = MQueue()
        q.put(42)
        self.assertEqual(q.take_nonblock(), 42)

    def test_callback(self) -> None:
        q : MQueue[int] = MQueue()
        callback_called = [0]
        def callback(exception: Optional[Exception]) -> None:
            callback_called[0] += 1
        callback_id = q.take_or_add_callback(callback)
        self.assertIsNotNone(callback_id)
        q.put(42)
        self.assertEqual(q.take_nonblock(), 42)
        self.assertEqual(callback_called[0], 1)

    def test_select_0(self) -> None:
        with self.assertRaises(NoInputs):
            value = select([], timeout=None)

    def test_select_timeout_1(self) -> None:
        q : MQueue[int] = MQueue()
        value = select([q], timeout=0.1)
        self.assertEqual(value, None)
        self.assertEqual(q._callbacks, {})

    def test_select_timeout_2(self) -> None:
        q1 : MQueue[int] = MQueue()
        q2 : MQueue[int] = MQueue()
        value = select([q1, q2], timeout=0.1)
        self.assertEqual(value, None)
        self.assertEqual(q1._callbacks, {})
        self.assertEqual(q2._callbacks, {})

    def test_select_1(self) -> None:
        q : MQueue[int] = MQueue()
        q.put(42)
        value = select([q], timeout=None)
        self.assertEqual(value, 42)
        self.assertEqual(q._callbacks, {})

    def test_select_2(self) -> None:
        q1 : MQueue[int] = MQueue()
        q1.put(1)
        q2 : MQueue[int] = MQueue()
        q2.put(2)
        value1 = select([q1, q2], timeout=None)
        self.assertTrue(value1 in [1, 2])
        value2 = select([q1, q2], timeout=None)
        self.assertTrue(value2 in [1, 2] and value2 != value1)
        self.assertEqual(q1._callbacks, {})
        self.assertEqual(q2._callbacks, {})

    def test_select_live(self) -> None:
        q1 : MQueue[int] = MQueue()
        def thread() -> None:
            time.sleep(0.05)
            q1.put(1)
        th = Thread(target=thread)
        th.start()
        value = select([q1], timeout=0.2)
        self.assertEqual(value, 1)
        self.assertEqual(q1._callbacks, {})

    def test_select_live2(self) -> None:
        q1 : MQueue[int] = MQueue()
        q2 : MQueue[int] = MQueue()
        def thread() -> None:
            time.sleep(0.05)
            q1.put(1)
            time.sleep(0.05)
            q2.put(2)
        th = Thread(target=thread)
        th.start()
        value = select([q1, q2], timeout=0.1)
        self.assertEqual(value, 1)
        self.assertEqual(q1._callbacks, {})
        self.assertEqual(q2._callbacks, {})

    def test_map(self) -> None:
        q1 : MQueue[int] = MQueue()
        q1.put(1)
        qm1 = q1.map(lambda x: x + 1)
        value = qm1.take_nonblock()
        self.assertEqual(value, 2)
        self.assertEqual(q1._callbacks, {})

    def test_map_select_1(self) -> None:
        q1 : MQueue[int] = MQueue()
        q1.put(1)
        value = select([q1.map(lambda x: x + 1)])
        self.assertEqual(value, 2)
        self.assertEqual(q1._callbacks, {})

    def test_map_select_2(self) -> None:
        q1 : MQueue[int] = MQueue()
        q1.put(0)
        q2 : MQueue[int] = MQueue()
        q2.put(10)
        value1 = select([q1.map(lambda x: x + 1),
                         q2.map(lambda x: x + 1)])
        self.assertTrue(value1 in [1, 11])
        value2 = select([q1.map(lambda x: x + 1),
                         q2.map(lambda x: x + 1)])
        self.assertTrue(value2 in [1, 11] and value2 != value1)
        self.assertEqual(q1._callbacks, {})
        self.assertEqual(q2._callbacks, {})

    def test_map_select_raise_1(self) -> None:
        q1 : MQueue[int] = MQueue()
        q1.put(0)
        with self.assertRaises(TestExn):
            def failer(i: int) -> int:
                raise TestExn()
            value = select([q1.map(failer)])
        self.assertEqual(q1._callbacks, {})

    def test_select_live_raise(self) -> None:
        q1 : MQueue[int] = MQueue()
        def thread() -> None:
            time.sleep(0.05)
            q1.put(1)
        th = Thread(target=thread)
        th.start()
        with self.assertRaises(TestExn):
            def failer(i: int) -> int:
                raise TestExn()
            value = select([q1.map(failer)])
        self.assertEqual(q1._callbacks, {})

    def test_select_live_raise2(self) -> None:
        q1 : MQueue[int] = MQueue()
        def thread() -> None:
            time.sleep(0.05)
            q1.put(1)
            q1.put(2)
        th = Thread(target=thread)
        th.start()
        count = [0]
        def failer(i: int) -> int:
            count[0] += 1
            if count[0] == 1:
                raise TestExn()
            else:
                return i
        source = [q1.map(failer)]
        with self.assertRaises(TestExn):
            value = select(source)
        value = select(source)
        self.assertEqual(value, 1)
        value = select(source)
        self.assertEqual(value, 2)
        self.assertEqual(q1._callbacks, {})

    def test_select_deep1(self) -> None:
        q1 : MQueue[int] = MQueue()
        q1.put(0)
        value = take(choose([choose([q1.map(lambda x: x + 1)])]))
        self.assertEqual(value, 1)
        self.assertEqual(q1._callbacks, {})

    def test_select_deep2(self) -> None:
        q1 : MQueue[int] = MQueue()
        q1.put(0)
        q2 : MQueue[int] = MQueue()
        q2.put(10)
        source = choose([choose([q1.map(lambda x: x + 1)]),
                         q2.map(lambda x: x + 1)])
        value1 = take(source)
        self.assertTrue(value1 in [1, 11])
        value2 = take(source)
        self.assertTrue(value2 in [1, 11] and value2 != value1)
        self.assertEqual(q1._callbacks, {})

if __name__ == '__main__':
    unittest.main()
