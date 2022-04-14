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

    # Other kind of errors (e.g, coming from Exponea)?
    except:
        return 'All other unknown errors', 7, request_num


@app.get("/api/smart/{timeout}")
async def api_smart(timeout: int) -> dict:
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    conn = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=conn, timeout=aiohttp.ClientTimeout(total=timeout / 1000)) as client:
        try:
            mytask_1 = asyncio.create_task(send_request(client, "request_1"))
            print("Fired first request and waiting for its response...")
            resp, status, which_request = await asyncio.wait_for(asyncio.shield(mytask_1), timeout=1000 / 1000)
            if status == 200:
                print("First request is SUCCESSFUL within 300ms.")
                print(which_request, "--->", status)
                resp["status"] = "SUCCESS"
                return resp
            else:
                print("First request is NOT SUCCESSFUL within 300ms.")
                print(which_request, "--->", resp)
                raise asyncio.exceptions.TimeoutError
        except asyncio.exceptions.TimeoutError:
            print("Firing two other requests...")
            mytask_2 = asyncio.create_task(send_request(client, "request_2"))
            mytask_3 = asyncio.create_task(send_request(client, "request_3"))

            for task in asyncio.as_completed(
                    [mytask_1, mytask_2, mytask_3]):
                earliest_resp, status, which_request = await task
                print(which_request, "--->", status)
                if status == 200:
                    if which_request == "request_1":
                        pass
                        #print("First request did not finish within 300ms. Fired two more requests.")
                    earliest_resp["status"] = "SUCCESS"
                    return earliest_resp
            return {"status": "ERROR"}
            # {"message": "ERROR! There was no successful response within endpoint's timeout."}  # either couldnt fire, or all failed
            # resp["message"] = "First request was SUCCESSFULL (it had status code 200) within 500 ms"
            #"First request either finished unsuccessfully with non-200 status code or it didn't still finish within 300 ms " \
            #"- fired two more requests and returned the earliest successfull reponse among all three requests."
#
# @app.get("/api/smart/{timeout}")
# async def api_smart(timeout: int):
#     async with aiohttp.ClientSession(..., timeout = ENDPOINT_TIMEOUT_PARAMETER):
#        try:
#          asyncio.wait_for(shield(send_request(first_request)), timeout=300/1000)
#          ## while waiting within 300ms, check below
#          if first_request is finished and status_code is 200:
#             return first_request
#          elif first_request is finished and status_code is NOT 200:
#             raise TimeoutError
#        except TimeoutError:
#          ## runs this if 300ms timeout exceeds or TimeoutError is raised manually
#         send_request(second_request) and send_request(third_request)
#          if any successfull response in asyncio.as_completed(all requests):
#             return earliest_successfull_response
#          return "ERROR! There is no successful response within endpoint's timeout."
#
