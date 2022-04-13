import json
import aiohttp
import httpx
import asyncio
import certifi
import ssl
from fastapi import FastAPI

app = FastAPI()


async def get_time(client: aiohttp.ClientSession, request_num: str):
    try:
        response = await client.get(
            "https://exponea-engineering-assignment.appspot.com/api/work"
        )
        #print(response.headers.get('Content-Type'))
        #print(response.status_code)

        json_time = await response.json(content_type=None)
        #header = response.headers.get('Content-Type')

        return json_time, response.status, request_num

    # Api response internal error
    except json.decoder.JSONDecodeError:
        '''
            <Response [500 Internal Server Error]>
            <Response [429 Too many requests]>
        '''
        return f'/server side error', response.status, request_num

    except aiohttp.client_exceptions.ContentTypeError:
        return "//content type error", response.status, request_num


@app.get("/api/smart/{timeout}")
async def api_smart(timeout: int):
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    conn = aiohttp.TCPConnector(ssl=ssl_context)
    try:
        async with aiohttp.ClientSession(connector=conn, timeout=aiohttp.ClientTimeout(total=timeout / 1000)) as client:
            try:
                mytask_1 = asyncio.create_task(get_time(client, "request_1"))
                resp, status, which_request = await asyncio.wait_for(asyncio.shield(mytask_1), timeout=300 / 1000)
                if status == 200:
                    resp["message"] = "SUCCESS! First request is SUCCESSFULL within 300 ms - returning its response."
                    resp["successfull_request_num"] = which_request
                    return resp
                else:
                    mytask_2 = asyncio.create_task(get_time(client, "request_2"))
                    mytask_3 = asyncio.create_task(get_time(client, "request_3"))

                    for task in asyncio.as_completed([mytask_2, mytask_3]):
                        earliest_resp, status, which_request = await task
                        if status == 200:
                            earliest_resp["message"] = "SUCCESS! First request FAILED within 300 ms - firing two more requests " \
                                             "and returning the earliest successfull reponse among these  " \
                                             "two requests.", f"Returning first SUCCESSFULL response: "
                            earliest_resp["successfull_request_num"] = which_request

                            return earliest_resp
                    return {"message": "ERROR! None of the requests sent were successfull in given timeout."}
            except asyncio.exceptions.TimeoutError:
                mytask_2 = asyncio.create_task(get_time(client, "request_2"))
                mytask_3 = asyncio.create_task(get_time(client, "request_3"))

                for task in asyncio.as_completed([mytask_1, mytask_2, mytask_3]):
                    earliest_resp, status, which_request = await task
                    if status == 200:
                        earliest_resp[
                            "message"] = "SUCCESS! First request DID NOT finish within 300 ms - firing two more " \
                                         "requests and returning the earliest successfull reponse among all of three " \
                                         "requests. Returning first SUCCESSFULL response: "
                        earliest_resp["successfull_request_num"] = which_request
                        # client.close() TODO: how?
                        return earliest_resp
                return {"message": "ERROR! None of the requests sent were successfull in given timeout."}

    except asyncio.exceptions.TimeoutError:
        return {"message": "ERROR! Timeout exceeded."}
