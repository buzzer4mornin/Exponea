import attr
from ratelimiter import RateLimiter
import json
import aiohttp
import asyncio
import certifi
import ssl
from fastapi import FastAPI
from time import time

app = FastAPI()


async def send_request(connector: aiohttp.TCPConnector, timeout: int):
    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as client:
            response = await client.get(
                "https://exponea-engineering-assignment.appspot.com/api/work"
            )

            json_time = await response.json(content_type=None)
            return json_time, response.status

    except asyncio.exceptions.TimeoutError:
        return 'Timeout Error', 0

    except aiohttp.client_exceptions.ClientConnectionError:
        return 'Connection Error', 0

    except aiohttp.client_exceptions.ClientOSError:
        return 'ClientOSError', 0

    except asyncio.exceptions.CancelledError:
        return 'Task got cancelled', 0

    except json.decoder.JSONDecodeError:
        '''
            <Response [500 Internal Server Error]>
            <Response [429 Too many requests]>
        '''
        return 'Exponea server error [500 or 429]', 0

    except aiohttp.client_exceptions.ContentTypeError:
        return 'JSON decode failed', 0

    except Exception as e:
        return str(e), 0


@app.get("/api/smart/{ENDPOINT_TIMEOUT}")
async def api_smart(ENDPOINT_TIMEOUT) -> dict:
    try:
        ENDPOINT_TIMEOUT = int(ENDPOINT_TIMEOUT)
    except ValueError:
        return {"message": "Endpoint timeout parameter should be INTEGER"}

    if ENDPOINT_TIMEOUT <= 300:
        return {"message": "Endpoint timeout parameter should be above 300"}

    # default is 300ms
    time_spent = 300

    try:
        # Fired first request and waiting 300ms for its response..
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        conn_1 = aiohttp.TCPConnector(limit=100, ssl=ssl_context)

        request_1 = asyncio.create_task(
            send_request(connector=conn_1, timeout=aiohttp.ClientTimeout(total=ENDPOINT_TIMEOUT / 1000)))
        start = time()
        resp, status = await asyncio.wait_for(asyncio.shield(request_1), timeout=1000 / 1000)
        if status == 200:
            # First request is SUCCESSFUL within 300ms.
            resp["message"] = "SUCCESS"
            return resp
        else:
            # First request finished but is NOT SUCCESSFUL within 300ms.
            time_spent = int((time() - start) * 1000)
            raise asyncio.exceptions.TimeoutError

    except asyncio.exceptions.TimeoutError:
        # Either {300ms timeout exceeded with no response from first request} or {First request finished but is NOT SUCCESSFUL within 300ms}
        ssl_context_2 = ssl.create_default_context(cafile=certifi.where())
        ssl_context_3 = ssl.create_default_context(cafile=certifi.where())
        conn_2 = aiohttp.TCPConnector(limit=100, ssl=ssl_context_2)
        conn_3 = aiohttp.TCPConnector(limit=100, ssl=ssl_context_3)

        request_2 = asyncio.create_task(
            send_request(connector=conn_2, timeout=aiohttp.ClientTimeout(total=(ENDPOINT_TIMEOUT - time_spent) / 1000)))
        request_3 = asyncio.create_task(
            send_request(connector=conn_3, timeout=aiohttp.ClientTimeout(total=(ENDPOINT_TIMEOUT - time_spent) / 1000)))

        # Firing two other requests and waiting for earliest successful response.
        for request in asyncio.as_completed([request_1, request_2, request_3]):
            earliest_resp, status = await request
            if status == 200:
                earliest_resp["status"] = "SUCCESS"
                return earliest_resp
            elif earliest_resp == "Timeout Error":
                # ERROR! api_smart() exceeds ENDPOINT_TIMEOUT.There is no successfull response within ENDPOINT_TIMEOUT!
                return {"message": "ERROR"}

        # ERROR! All requests are finished within ENDPOINT_TIMEOUT but there is no successfull response!
        return {"message": "ERROR"}
