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

        return json_time, request_num

    except asyncio.exceptions.TimeoutError:
        return 'Timeout Error', request_num

    except aiohttp.client_exceptions.ClientConnectionError:
        return 'Connection Error', request_num

    except aiohttp.client_exceptions.ClientOSError:
        return 'ClientOSError', request_num

    except asyncio.exceptions.CancelledError:
        return 'Task got cancelled', request_num

    # Api response internal error
    except json.decoder.JSONDecodeError:
        '''
            <Response [500 Internal Server Error]>
            <Response [429 Too many requests]>
        '''
        return 'Exponea server error [500 or 429]', request_num

    # When failing to decode JSON
    except aiohttp.client_exceptions.ContentTypeError:
        return 'JSON decode failed', request_num

    # Other kind of errors (e.g, coming from Exponea)?
    except BaseException as e:
        return str(e), request_num


@app.get("/api/smart/{total_timeout}")
async def api_smart(total_timeout: int) -> dict:
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    conn = aiohttp.TCPConnector(ssl=ssl_context)
    flag = False
    try:
        start = time()
        time_spent = 300
        mytask_1 = asyncio.create_task(send_request(connector=conn, timeout=aiohttp.ClientTimeout(total=total_timeout / 1000), request_num="request_1"))
        print("Fired first request and waiting 300ms for its response..")
        resp, which_request = await asyncio.wait_for(asyncio.shield(mytask_1), timeout=1000 / 1000)

        if type(resp) is dict:  # i.e., if response status is 200
            print("First request is SUCCESSFUL within 300ms.")
            print(which_request, "--->", resp)
            resp["status"] = "SUCCESS"
            return resp
        else:
            time_spent = int((time() - start)*1000)
            flag = True
            print("First request is NOT SUCCESSFUL within 300ms.")
            print(which_request, "--->", resp)
            raise asyncio.exceptions.TimeoutError
    except asyncio.exceptions.TimeoutError:
        if flag:
            print("Firing two other requests and waiting for first successful response.")
        else:
            print("300ms timeout exceeded with no response from first request.")
            print("Firing two other requests and waiting for first successful response..")
        mytask_2 = asyncio.create_task(send_request(connector=conn, timeout=aiohttp.ClientTimeout(total=(total_timeout - time_spent) / 1000), request_num="request_2"))
        mytask_3 = asyncio.create_task(send_request(connector=conn, timeout=aiohttp.ClientTimeout(total=(total_timeout - time_spent) / 1000), request_num="request_3"))

        for task in asyncio.as_completed(
                [mytask_1, mytask_2, mytask_3]):
            earliest_resp, which_request = await task
            if (which_request == "request_1" and flag is not True) or which_request != "request_1":
                print(which_request, "--->", earliest_resp)
            if type(earliest_resp) is dict:  # i.e., if response status is 200
                earliest_resp["status"] = "SUCCESS"
                return earliest_resp
            elif earliest_resp == "Timeout Error":
                return {"status": "ERROR"}
        print("None of 3 requests is successfull!")
        return {"status": "ERROR"}
