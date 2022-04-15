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
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    conn = aiohttp.TCPConnector(ssl=ssl_context)
    # default is 300ms
    time_spent = 300
    # bool to check if first request is finished, but NOT SUCCESSFUL within 300ms
    flag = False
    all_responses = []  # to collect all available responses
    try:
        print("Fired first request and waiting 300ms for its response..")
        mytask_1 = asyncio.create_task(send_request(connector=conn, timeout=aiohttp.ClientTimeout(total=ENDPOINT_TIMEOUT / 1000), request_num="request_1"))
        start = time()
        resp, status, which_request = await asyncio.wait_for(asyncio.shield(mytask_1), timeout=300 / 1000)
        all_responses.append(resp)
        if status == 200:  # i.e., if first request's response status is 200
            print("First request is SUCCESSFUL within 300ms.")
            print(which_request, "--->", resp)
            print(all_responses)
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
        #print(ENDPOINT_TIMEOUT - time_spent)
        mytask_2 = asyncio.create_task(send_request(connector=conn_2, timeout=aiohttp.ClientTimeout(total=(ENDPOINT_TIMEOUT - time_spent) / 1000), request_num="request_2"))
        mytask_3 = asyncio.create_task(send_request(connector=conn_3, timeout=aiohttp.ClientTimeout(total=(ENDPOINT_TIMEOUT - time_spent) / 1000), request_num="request_3"))

        for task in asyncio.as_completed([mytask_1, mytask_2, mytask_3]):
            earliest_resp, status, which_request = await task
            all_responses.append(earliest_resp)
            if (which_request == "request_1" and flag is not True) or which_request != "request_1":
                print(which_request, "--->", earliest_resp)
            if status == 200:  # i.e., if response status is 200
                #print(all_responses)
                earliest_resp["status"] = "SUCCESS"
                return earliest_resp

        print("ERROR! There is no successfull response within ENDPOINT_TIMEOUT!")
        return {"message": "ERROR"}

