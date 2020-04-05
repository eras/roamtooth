"""Dispatch arranges events from

Copyright 2020 Erkki Seppälä <flux@inside.org>
License: MIT

"""

from abc import ABC, abstractclassmethod
from typing import Tuple, Optional, Any, NewType, Dict, Type
from types import TracebackType
from dataclasses import dataclass
from threading import Thread

import roamtoothd.mqueue as mqueue
from roamtoothd.idgen import IdGen

ClientId = NewType('ClientId', int)

@dataclass
class Context:
    """Context shared by different Cmds"""
    exit: bool
    clients: Dict[ClientId, "Client"]
    dispatch: "Dispatch"

class Cmd(ABC):
    """Base class for Cmds"""
    @abstractclassmethod
    def run(self, context: Context) -> None:
        """Command has been received; process it"""

class CmdExit(Cmd):
    """The exit; exit Dispatch"""
    def run(self, context: Context) -> None:
        context.exit = True

class CmdBroadcast(Cmd):
    """A broadcast request"""
    def __init__(self, message: Any):
        self.message = message

    def run(self, context: Context) -> None:
        for _, client in context.clients.items():
            client.to_client.put(self.message)

class Client:
    """Dispatcher client; an object for receiving events"""

    client_id_gen = IdGen(ClientId)

    def __init__(self, dispatch: "Dispatch") -> None:
        self.dispatch = dispatch
        self.client_id = Client.client_id_gen.make()
        self.to_client: mqueue.MQueue[Any] = mqueue.MQueue()

    def __enter__(self) -> "Client":
        """Returns self; __exit__ handles unregistration."""
        return self

    def __exit__(self,
                 exc_type: Optional[Type[BaseException]],
                 exc_value: Optional[BaseException],
                 traceback: Optional[TracebackType]) -> None:
        """Stop this client; unregister from Dispatch"""
        self.dispatch.unregister_client(self.client_id)

class CmdRegisterClient(Cmd):
    """Create a client"""
    def __init__(self, response: mqueue.MQueue[Client]):
        self.response = response

    def run(self, context: Context) -> None:
        client = Client(context.dispatch)
        context.clients[client.client_id] = client
        self.response.put(client)

class CmdUnregisterClient(Cmd):
    """Create a client"""
    def __init__(self, response: mqueue.MQueue[Tuple[()]], client_id: ClientId):
        self.response = response
        self.client_id = client_id

    def run(self, context: Context) -> None:
        if self.client_id in context.clients:
            del context.clients[self.client_id]
        self.response.put(())

class Dispatch:
    """Dispatch manages message dispatching to multiple subscribers."""
    def __init__(self) -> None:
        self._thread: Optional[Thread] = None
        self._exit_request: mqueue.MQueue[Tuple[()]] = mqueue.MQueue()
        self._broadcast_request: mqueue.MQueue[Any] = mqueue.MQueue()
        self._requests: mqueue.MQueue[Cmd] = mqueue.MQueue()

    def start(self) -> None:
        """Start the Dispatch thread"""
        assert not self._thread
        self._thread = Thread(target=self._run)
        self._thread.start()

    def stop(self) -> None:
        """Stop the Dispatch thread; waits for it to be stopped."""
        assert self._thread
        self._requests.put(CmdExit())
        self._thread.join()
        self._thread = None

    def register_client(self) -> Client:
        """Creates a new client

        Don't forget to .exit it afterwards to avoid message leaks.

        """
        response: mqueue.MQueue[Client] = mqueue.MQueue()
        self._requests.put(CmdRegisterClient(response))
        return mqueue.take(response)

    def unregister_client(self, client_id: ClientId) -> None:
        """Unregisters a client synchronously"""
        response: mqueue.MQueue[Tuple[()]] = mqueue.MQueue()
        self._requests.put(CmdUnregisterClient(response, client_id))
        mqueue.take(response)

    def broadcast(self, message: Any) -> None:
        """Send a message to all clients"""
        assert self._thread
        self._requests.put(CmdBroadcast(message))

    def _run(self) -> None:
        context = Context(exit=False, clients={}, dispatch=self)
        while not context.exit:
            value = mqueue.take(self._requests)
            value.run(context)
