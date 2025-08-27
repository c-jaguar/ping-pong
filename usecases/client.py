import asyncio
import logging
import random
from datetime import datetime, timedelta
from pkg import logger

class PendingRequest:
    def __init__(self, time: datetime, text: str) -> None:
        self.time = time
        self.text = text

class TCPClient:
    def __init__(self, host: str = "localhost", port: int = 8888, timeout: int =15) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.request_counter = 0
        self.pending_requests: dict[int, PendingRequest] = {}
        logger.setup_logging()


    async def send_ping_messages(self, writer: asyncio.StreamWriter) -> None:
        while True:
            delay = random.uniform(0.3, 3.0)  # noqa: S311
            await asyncio.sleep(delay)

            self.request_counter += 1
            message = f"[{self.request_counter}] PING"
            send_time = datetime.now()
            writer.write((message + "\n").encode())
            await writer.drain()
            self.pending_requests[self.request_counter] = PendingRequest(send_time, message)


    async def receive_messages(self, reader: asyncio.StreamReader) -> None:
        while True:
            data = await asyncio.wait_for(reader.readline(), timeout=10.0)
            if not data:
                break

            message = data.decode().rstrip()
            receive_time = datetime.now()

            if "keepalive" in message:
                log_message = "{};;;{};{}".format(
                    receive_time.strftime("%Y-%m-%d"), receive_time.strftime("%H:%M:%S.%f")[:-3], message,
                )
                logging.info(log_message)
            else:
                request_number = int(message.split("]")[0].split("/")[1])
                pending_request = self.pending_requests.get(request_number)
                if pending_request:
                    log_message = "{};{};{};{};{}".format(
                        receive_time.strftime("%Y-%m-%d"), pending_request.time.strftime("%Y-%m-%d"),
                        pending_request.text, receive_time.strftime("%H:%M:%S.%f")[:-3], message,
                    )
                    logging.info(log_message)
                    del self.pending_requests[request_number]
                else:
                    msg = f"Unexpected error has occurred. No such pending request [{request_number}]"
                    raise RuntimeError(msg)

    async def request_timeout(self) -> None:
        while True:
            await asyncio.sleep(self.timeout)
            current_time = datetime.now()
            timeout_request_ids = [
                (request_id, pending_request)
                for request_id, pending_request in self.pending_requests.items()
                if current_time - pending_request.time > timedelta(seconds=self.timeout)
            ]
            for request_id, pending_request in timeout_request_ids:
                log_message = "{};{};{};{};(таймаут)".format(
                    pending_request.time.strftime("%Y-%m-%d"), pending_request.time.strftime("%H:%M:%S.%f")[:-3],
                    pending_request.text, current_time.strftime("%H:%M:%S.%f")[:-3],
                )
                logging.info(log_message)
                del self.pending_requests[request_id]

    async def run_client(self) -> None:
        try:
            reader, writer = await asyncio.open_connection(self.host, self.port)
            send_task = asyncio.create_task(self.send_ping_messages(writer))
            receive_task = asyncio.create_task(self.receive_messages(reader))
            request_timeout_task = asyncio.create_task(self.request_timeout())
            await asyncio.gather(send_task, receive_task, request_timeout_task)
        finally:
            if writer:
                writer.close()
                await writer.wait_closed()
