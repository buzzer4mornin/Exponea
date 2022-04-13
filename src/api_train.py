import json
import aiohttp
import httpx
import asyncio
import certifi
import ssl
from fastapi import FastAPI
from asyncio_throttle import Throttler

app = FastAPI()

async def get_time(client: aiohttp.ClientSession, request_num: str):
    try:
        # throttler = Throttler(rate_limit=100, period=15)
        # async with throttler:
        response = await client.get(
            "https://exponea-engineering-assignment.appspot.com/api/work"
        )
        # print(response)
        json_time = await response.json(content_type=None)

        return json_time, response.status, request_num

    # Api response internal error
    except json.decoder.JSONDecodeError:
        '''
            <Response [500 Internal Server Error]>
            <Response [429 Too many requests]>
        '''
        return f'Request has failed. Try again...', response.status, request_num

    except aiohttp.client_exceptions.ContentTypeError:
        return "decoder error", response.status, request_num


@app.get("/api/smart/{timeout}")
async def api_smart(timeout: int):
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    conn = aiohttp.TCPConnector(ssl=ssl_context)
    try:
        async with aiohttp.ClientSession(connector=conn, timeout=aiohttp.ClientTimeout(total=timeout / 1000)) as client:
            try:
                mytask_1 = asyncio.create_task(get_time(client, "request_1"))
                r, c, which_request = await asyncio.wait_for(asyncio.shield(mytask_1), timeout=1 / 1000)
                if c == 200:
                    r["request_num"] = which_request
                    return "FIRST request is SUCCESSFULL within 300 ms - returning its response.", f"Returning " \
                                                                                                   f"first SUCCESSFULL " \
                                                                                                   f"response: " \
                                                                                                   f"", r
                else:
                    mytask_2 = asyncio.create_task(get_time(client, "request_2"))
                    mytask_3 = asyncio.create_task(get_time(client, "request_3"))

                    for coro in asyncio.as_completed([mytask_2, mytask_3]):
                        earliest_result, c, which_request = await coro
                        if c == 200:
                            earliest_result["request_num"] = which_request
                            return "FIRST request FAILED within 300 ms - firing two more requests " \
                                   "and returning the earliest successfull reponse among these " \
                                   "two requests.", f"Returning first SUCCESSFULL response:", earliest_result
                    return "NO SUCCESSFULL RESULT"
            except asyncio.exceptions.TimeoutError:
                mytask_2 = asyncio.create_task(get_time(client, "request_2"))
                mytask_3 = asyncio.create_task(get_time(client, "request_3"))

                for coro in asyncio.as_completed([mytask_1, mytask_2, mytask_3]):
                    earliest_result, c, which_request = await coro
                    if c == 200:
                        earliest_result["request_num"] = which_request
                        # client.close() TODO: how?
                        return "FIRST request DID NOT finish within 300 ms - firing two more " \
                               "requests and returning the earliest successfull reponse among all" \
                               " of three requests.", f"Returning first SUCCESSFULL response:", earliest_result
                print("two")
                return "NO SUCCESSFULL RESULT"

    except asyncio.exceptions.TimeoutError:
        return "Timeout Error"

    except aiohttp.client_exceptions.ClientOSError:
        print("hihihihi")
