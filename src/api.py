import json
import aiohttp
import httpx
import asyncio
import certifi
import ssl
from fastapi import FastAPI

app = FastAPI()


async def send_request(client: aiohttp.ClientSession, request_num: str):
    try:
        response = await client.get(
            "https://exponea-engineering-assignment.appspot.com/api/work"
        )

        json_time = await response.json(content_type=None)

        return json_time, request_num

    except asyncio.exceptions.TimeoutError:
        return 'TimeoutError', request_num

    except aiohttp.client_exceptions.ClientConnectionError:
        return 'Connection closed', request_num

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
    except:
        return 'All other unknown errors', request_num


@app.get("/api/smart/{timeout}")
async def api_smart(timeout: int) -> dict:
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    conn = aiohttp.TCPConnector(ssl=ssl_context)
    flag = False
    async with aiohttp.ClientSession(connector=conn, timeout=aiohttp.ClientTimeout(total=timeout / 1000)) as client:
        try:
            mytask_1 = asyncio.create_task(send_request(client, "request_1"))
            print("Fired first request and waiting 300ms for its response..")
            resp, which_request = await asyncio.wait_for(asyncio.shield(mytask_1), timeout=300 / 1000)
            if type(resp) is dict:  # i.e., if response status is 200
                print("First request is SUCCESSFUL within 300ms.")
                print(which_request, "--->", resp)
                resp["status"] = "SUCCESS"
                return resp
            else:
                flag = True
                print("First request is NOT SUCCESSFUL within 300ms.")
                print(which_request, "--->", resp)
                raise asyncio.exceptions.TimeoutError
        except asyncio.exceptions.TimeoutError:
            if flag:
                print("Firing two other requests and waiting for first successful response.")
            else:
                print("300ms timeout exceeded with no response from first request."
                      " Firing two other requests and waiting for first successful response.")
            mytask_2 = asyncio.create_task(send_request(client, "request_2"))
            mytask_3 = asyncio.create_task(send_request(client, "request_3"))

            for task in asyncio.as_completed(
                    [mytask_1, mytask_2, mytask_3]):
                earliest_resp, which_request = await task
                if (which_request == "request_1" and flag is not True) or which_request != "request_1":
                    print(which_request, "--->", earliest_resp)
                if type(earliest_resp) is dict:  # i.e., if response status is 200
                    earliest_resp["status"] = "SUCCESS"
                    return earliest_resp
            return {"status": "ERROR"}
