import json
import aiohttp
import httpx
import asyncio
import certifi
import ssl
from fastapi import FastAPI
from time import time
app = FastAPI()


async def send_request(connector: aiohttp.TCPConnector, timeout: int, request_num: str):
    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as client:
            response = await client.get(
                "https://exponea-engineering-assignment.appspot.com/api/work"
            )

            json_time = await response.json(content_type=None)
            return json_time, response.status, request_num

    except asyncio.exceptions.TimeoutError:
        return 'Timeout Error', 0, request_num

    except aiohttp.client_exceptions.ClientConnectionError:
        return 'Connection Error', 0, request_num

    except aiohttp.client_exceptions.ClientOSError:
        return 'ClientOSError', 0, request_num

    except asyncio.exceptions.CancelledError:
        return 'Task got cancelled', 0, request_num

    # Api response internal error
    except json.decoder.JSONDecodeError:
        '''
            <Response [500 Internal Server Error]>
            <Response [429 Too many requests]>
        '''
        return 'Exponea server error [500 or 429]', 0, request_num

    # When failing to decode JSON
    except aiohttp.client_exceptions.ContentTypeError:
        return 'JSON decode failed', 0, request_num

    # Other kind of errors (e.g, coming from Exponea)?
    except Exception as e:
        return str(e), request_num


@app.get("/api/smart/{ENDPOINT_TIMEOUT}")
async def api_smart(ENDPOINT_TIMEOUT: int) -> dict:
    if ENDPOINT_TIMEOUT <= 300:
        return {"message": "Endpoint timeout parameter should be above 300."}
    # default is 300ms
    time_spent = 300
    # bool to check if first request is finished and NOT SUCCESSFUL within 300ms
    flag = False
    try:
        print("Fired first request and waiting 300ms for its response..")
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        conn_1 = aiohttp.TCPConnector(ssl=ssl_context)
        mytask_1 = asyncio.create_task(send_request(connector=conn_1, timeout=aiohttp.ClientTimeout(total=ENDPOINT_TIMEOUT / 1000), request_num="request_1"))
        start = time()
        resp, status, which_request = await asyncio.wait_for(asyncio.shield(mytask_1), timeout=300 / 1000)
        if status == 200:
            print("First request is SUCCESSFUL within 300ms.")
            print(which_request, "--->", resp)
            resp["message"] = "SUCCESS"
            return resp
        else:
            time_spent = int((time() - start)*1000)
            flag = True
            print("First request finished but is NOT SUCCESSFUL within 300ms.")
            print(which_request, "--->", resp)
            raise asyncio.exceptions.TimeoutError
    except asyncio.exceptions.TimeoutError:
        if flag:
            print("Firing two other requests and waiting for first successful response.")
        else:
            print("300ms timeout exceeded with no response from first request.")
            print("Firing two other requests and waiting for first successful response..")
        ssl_context_2 = ssl.create_default_context(cafile=certifi.where())
        ssl_context_3 = ssl.create_default_context(cafile=certifi.where())
        conn_2 = aiohttp.TCPConnector(ssl=ssl_context_2)
        conn_3 = aiohttp.TCPConnector(ssl=ssl_context_3)
        mytask_2 = asyncio.create_task(send_request(connector=conn_2, timeout=aiohttp.ClientTimeout(total=(ENDPOINT_TIMEOUT - time_spent) / 1000), request_num="request_2"))
        mytask_3 = asyncio.create_task(send_request(connector=conn_3, timeout=aiohttp.ClientTimeout(total=(ENDPOINT_TIMEOUT - time_spent) / 1000), request_num="request_3"))

        for task in asyncio.as_completed([mytask_1, mytask_2, mytask_3]):
            earliest_resp, status, which_request = await task
            if (which_request == "request_1" and flag is not True) or which_request != "request_1":
                print(which_request, "--->", earliest_resp)
            if status == 200:
                earliest_resp["status"] = "SUCCESS"
                return earliest_resp

        print("ERROR! There is no successfull response within ENDPOINT_TIMEOUT!")
        return {"message": "ERROR"}

