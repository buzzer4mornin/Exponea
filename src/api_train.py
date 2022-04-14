import json
import aiohttp
import httpx
import asyncio
import certifi
import ssl
from fastapi import FastAPI

app = FastAPI()


async def SEND_REQUEST(client: aiohttp.ClientSession, request_num: str):
    try:
        response = await client.get(
            "https://exponea-engineering-assignment.appspot.com/api/work"
        )
        # print(response.headers.get('Content-Type'))
        # print(response.status_code)

        json_time = await response.json(content_type=None)
        # header = response.headers.get('Content-Type')

        return json_time, response.status, request_num

    except asyncio.exceptions.TimeoutError:
        return 'Timeout occured', 1, request_num

    except aiohttp.client_exceptions.ClientConnectionError:
        return 'Connection closed', 2, request_num

    except aiohttp.client_exceptions.ClientOSError:
        return 'ClientOSError', 3, request_num

    except asyncio.exceptions.CancelledError:
        return 'Task got cancelled', 4, request_num

    # Api response internal error
    except json.decoder.JSONDecodeError:
        '''
            <Response [500 Internal Server Error]>
            <Response [429 Too many requests]>
        '''
        return 'Server side error', 5, request_num

    # When failing to decode JSON
    except aiohttp.client_exceptions.ContentTypeError:
        return 'JSON decode failed', 6, request_num

    except:
        return 'Other unknown errors'


@app.get("/api/smart/{timeout}")
async def api_smart(timeout: int) -> dict:
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    conn = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=conn, timeout=aiohttp.ClientTimeout(total=timeout / 1000)) as client:
        try:
            mytask_1 = asyncio.create_task(SEND_REQUEST(client, "request_1"))
            resp, status, which_request = await asyncio.wait_for(asyncio.shield(mytask_1), timeout=300 / 1000)
            if status == 200:
                resp["is_successfull"] = True
                resp["successfull_request_num"] = which_request
                resp[
                    "message"] = "First request was SUCCESSFULL (it had status code 200) within 300 ms - returning its response."
                return resp
            else:
                raise asyncio.exceptions.TimeoutError
        except asyncio.exceptions.TimeoutError:
            mytask_2 = asyncio.create_task(SEND_REQUEST(client, "request_2"))
            mytask_3 = asyncio.create_task(SEND_REQUEST(client, "request_3"))

            for task in asyncio.as_completed(
                    [mytask_1, mytask_2, mytask_3]):
                earliest_resp, status, which_request = await task
                print(status)
                if status == 200:
                    earliest_resp["is_successfull"] = True
                    earliest_resp["successfull_request_num"] = which_request
                    earliest_resp["message"] = \
                        "First request is NOT SUCCESSFULL (either it had non-200 status code or it didn't finish yet) within 300 ms " \
                        "- firing two more requests and returning the earliest successfull reponse among all three requests."
                    # client.close() TODO: how?
                    return earliest_resp
            return {"is_successfull": False,
                    "message": "ERROR! There is no successful response within endpoint's timeout."}  # either couldnt fire, or all failed
