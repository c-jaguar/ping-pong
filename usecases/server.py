import asyncio
import logging
import random
from asyncio import StreamWriter
from datetime import datetime

from pkg import logger


class TCPServer:

    def __init__(self, host: str = "localhost", port: int = 8888) -> None:
        self.host = host
        self.port = port
        self.response_counter = 0
        self.client_counter = 0
        self.clients: dict[StreamWriter, int] = {}
        logger.setup_logging()

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self.client_counter += 1
        client_id = self.client_counter
        self.clients[writer] = client_id
        try:
            while True:
                data = await reader.readline()
                if not data:
                    break

                request = data.decode().rstrip()
                receive_time = datetime.now()
                await self.process_ping(request, receive_time, client_id, writer)

        finally:
            writer.close()
            await writer.wait_closed()

    async def process_ping(self, request: str, receive_time: datetime, client_id: int, writer: asyncio.StreamWriter)\
            -> None:
        chance_to_fail = 0.1
        if random.random() < chance_to_fail:  # noqa: S311
            log_message = "{};{};{};(проигнорировано);(проигнорировано)".format(
                receive_time.strftime("%Y-%m-%d"), receive_time.strftime("%H:%M:%S.%f")[:-3], request,
            )
            logging.info(log_message)
            return

        request_number = request.split("]")[0].split("[")[1]
        delay = random.uniform(0.1, 1.0)  # noqa: S311
        await asyncio.sleep(delay)
        response = f"[{self.response_counter}/{request_number}] PONG ({client_id})"

        send_time = datetime.now()

        writer.write((response + "\n").encode())
        await writer.drain()

        self.response_counter += 1

        log_message = "{};{};{};{};{}".format(
            receive_time.strftime("%Y-%m-%d"), receive_time.strftime("%H:%M:%S.%f")[:-3], request,
            send_time.strftime("%H:%M:%S.%f")[:-3], response,
            )
        logging.info(log_message)


    async def keepalive(self) -> None:
        while True:
            await asyncio.sleep(5)
            message = f"[{self.response_counter}] keepalive"
            if self.clients:
                for writer in self.clients:
                    try:
                        writer.write((message + "\n").encode())
                        await writer.drain()
                        self.response_counter += 1
                    # Нет времени придумывать более приемлимый способ, чем трай-эксепт в цикле
                    except ConnectionResetError:  # noqa: PERF203
                        if writer in self.clients:
                            del self.clients[writer]

    async def run_server(self) -> None:
        server = await asyncio.start_server(
            self.handle_client, self.host, self.port,
        )

        asyncio.create_task(self.keepalive())  # noqa: RUF006

        async with server:
            await server.serve_forever()
