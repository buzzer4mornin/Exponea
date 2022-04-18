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

    # need this for properly adjusting timeout of second and third request
    time_spent = 300

    try:
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        conn_1 = aiohttp.TCPConnector(ssl=ssl_context)

        # prepare first request
        request_1 = asyncio.create_task(
            send_request(connector=conn_1, timeout=aiohttp.ClientTimeout(total=ENDPOINT_TIMEOUT / 1000)))
        start = time()
        # send and wait for response 300ms. Shield protects request from being cancelled by wait_for's timeout
        resp, status = await asyncio.wait_for(asyncio.shield(request_1), timeout=300 / 1000)

        if status == 200:
            # first request finished and is SUCCESSFUL within 300ms
            # add success message to json response and return it
            resp["message"] = "SUCCESS"
            return resp
        else:
            # first request finished but is NOT SUCCESSFUL within 300ms
            time_spent = int((time() - start) * 1000)
            raise asyncio.exceptions.TimeoutError

    except asyncio.exceptions.TimeoutError:
        # either {300ms timeout exceeded with no response from first request}
        #   or   {first request finished but is NOT SUCCESSFUL within 300ms}
        ssl_context_2 = ssl.create_default_context(cafile=certifi.where())
        ssl_context_3 = ssl.create_default_context(cafile=certifi.where())
        conn_2 = aiohttp.TCPConnector(ssl=ssl_context_2)
        conn_3 = aiohttp.TCPConnector(ssl=ssl_context_3)

        # prepare second and third request
        request_2 = asyncio.create_task(
            send_request(connector=conn_2, timeout=aiohttp.ClientTimeout(total=(ENDPOINT_TIMEOUT - time_spent) / 1000)))
        request_3 = asyncio.create_task(
            send_request(connector=conn_3, timeout=aiohttp.ClientTimeout(total=(ENDPOINT_TIMEOUT - time_spent) / 1000)))

        # send second and third request, and process requests greedily as they finish
        for request in asyncio.as_completed([request_1, request_2, request_3]):
            earliest_resp, status = await request
            if status == 200:
                # received earliest successful response.
                # add success message to json response and return it
                earliest_resp["message"] = "SUCCESS"
                return earliest_resp
            elif earliest_resp == "Timeout Error":
                # api_smart() exceeds ENDPOINT_TIMEOUT. No successfull response within ENDPOINT_TIMEOUT!
                return {"message": "ERROR"}

        # all requests are finished within ENDPOINT_TIMEOUT but there is no successfull response!
        return {"message": "ERROR"}
