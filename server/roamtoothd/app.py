"""The web app providing API for RoamTooth clients.

Copyright 2020 Erkki Seppälä <flux@inside.org>
License: MIT

"""
import os

from dataclasses import dataclass
from typing import Any

import json

from flask import Flask, Response, request
from pydantic import BaseModel # pylint: disable=no-name-in-module

import roamtoothd.config as config
import roamtoothd.dispatch
import roamtoothd.mqueue as mqueue

@dataclass
class ServerSyncRequest:
    """Server-initiated synchronous message to client."""
    sid: int
    sync: str
    args: Any

class RequestDeviceConnect(BaseModel):
    """Device connect request (from server to client)"""
    request = "device_connect"
    device: str

def create() -> Flask:
    """Create the Flask app"""

    dispatch = roamtoothd.dispatch.Dispatch()
    dispatch.start()

    app = Flask(__name__, instance_relative_config=True)

    app.config.from_object(os.environ['APP_SETTINGS'] if 'APP_SETTINGS' in os.environ else config.DevelopmentConfig)

    @app.route("/stream")
    def stream(): # type: ignore # pylint: disable=unused-variable
        """Request a server-side event stream to this client"""
        def event_stream(): # type: ignore
            yield "data: {}\n\n".format(json.dumps({"hello": "world"}))
            counter = 0
            with dispatch.register_client() as client: # pylint: disable=not-context-manager
                while True:
                    message = mqueue.take(client.to_client, 1.0)
                    if message:
                        yield "data: {}\n\n".format(json.dumps(message))
                    else:
                        yield "data: {}\n\n".format(json.dumps({"async": "keepalive", "args": {"counter": counter}}))
                        counter += 1

        return Response(event_stream(), mimetype="text/event-stream") # type: ignore

    # a simple page that says hello
    @app.route('/cmd/device_disconnect', methods=['POST'])
    def device_disconnect(): # type: ignore # pylint: disable=unused-variable
        """Post a synchronous or asynchronous event from a client."""
        content = RequestDeviceConnect(**request.json)
        dispatch.broadcast({"sid": 1, "sync": "device_disconnect", "args": {}})
        return content.device

    return app

if __name__ == '__main__':
    create().run()
