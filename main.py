import argparse
import asyncio

from usecases.client import TCPClient
from usecases.server import TCPServer

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Client/Server runner")
    parser.add_argument("--type", type=str)

    args = parser.parse_args()

    match args.type:
        case "client":
            client = TCPClient()
            asyncio.run(client.run_client())
        case "server":
            server = TCPServer()
            asyncio.run(server.run_server())
        case _:
            msg = "Invalid application type"
            raise RuntimeError(msg)
