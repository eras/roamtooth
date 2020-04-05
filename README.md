# RoamTooth

Centrally manage your bluetooth devices. In particular, the Sony
WH1000XM3 bluetooth headsets, which can be connected to only one
device at a time.

The Linux-client—and possible the MacOS and Windows clients in the
future—is implemented in Rust. The server is in Python (using Flask,
mypy). The possible future Android client might be written in Kotlin.

## How it works

There is a server in the Internet—or local network—to which clients
attach via HTTP/HTTPS, using the SSE protocol for listening
events. Such events curently include "disconnect device", which will
disconnect the requested device from all connected clients. After this
it's available to be connected from your laptop or other supported
device.

## Does it work?

It does work, if you happen to use Linux and the Bluetooth address is
the same as mine. Also no authentiation whatsoever. And end point
address is hardcoded. And you need to send the requsts in with
ie. `curl`. So.

## License

MIT
