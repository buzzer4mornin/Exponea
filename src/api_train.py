import json
from asyncio import shield
import aiohttp
import httpx
import asyncio
from fastapi import FastAPI
import certifi
from asyncio_throttle import Throttler
import ssl
app = FastAPI()


async def get_time(client: aiohttp.ClientSession) -> None:
    try:
        throttler = Throttler(rate_limit=100, period=15)
        async with throttler:
            response = await client.get(
                    "https://exponea-engineering-assignment.appspot.com/api/work"
                )
            #print(response)
            json_time = await response.json(content_type=None)

            return json_time, response.status
    # Timeout exception
    except httpx.ConnectTimeout:
        return ('Connection timeout error (server timeout)'), response.status
    except httpx.ReadTimeout:
        return (f'Request exceeded timeout period...'), response.status

    # Api response internal error
    except json.decoder.JSONDecodeError:
        '''
            <Response [500 Internal Server Error]>
            <Response [429 Too many requests]>
        '''
        return (f'Request has failed. Try again...'), response.status

    except aiohttp.client_exceptions.ContentTypeError:
        return ("decoder error"), response.status



@app.get("/api/smart/{timeout}")
async def api_smart(timeout: int):
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    conn = aiohttp.TCPConnector(ssl=ssl_context)
    try:
        async with aiohttp.ClientSession(connector=conn, timeout=aiohttp.ClientTimeout(total=timeout / 1000)) as client:
            try:
                mytask_1 = asyncio.create_task(get_time(client))
                r, c = await asyncio.wait_for(asyncio.shield(mytask_1), timeout=500/1000)
                if c == 200:
                    return r, c, "FIRST request is SUCCESSFULL within 300 ms - returning its response."
                else:
                    mytask_2 = asyncio.create_task(get_time(client))
                    mytask_3 = asyncio.create_task(get_time(client))

                    for coro in asyncio.as_completed([mytask_2, mytask_3]):
                        earliest_result, c = await coro
                        if c == 200:
                            return earliest_result, c, "FIRST request FAILED within 300 ms - firing two more requests and returning the earliest successfull reponse among these two requests."
                    return "NO SUCCESSFULL RESULT"
            except:
                mytask_2 = asyncio.create_task(get_time(client))
                mytask_3 = asyncio.create_task(get_time(client))

                for coro in asyncio.as_completed([mytask_1, mytask_2, mytask_3]):
                    earliest_result, c = await coro
                    if c == 200:
                        # client.close() TODO: how?
                        return earliest_result, c, "FIRST request DID NOT finish within 300 ms - firing two more requests and returning the earliest successfull reponse among all of three requests."
                return "NO SUCCESSFULL RESULT"

    except asyncio.exceptions.TimeoutError:
        return "Timeout Error"



        #await asyncio.sleep(4)
        #print(r)

        #tasks = [mytask_2, mytask_1]
        #r_1 = await mytask_1
        #return mytask_1.done()

        #print(len(done), len(pending))


        #r_2 = await mytask_2

        #for coro in asyncio.as_completed(tasks):
        #    s = await coro
        #    print(s)
        #return r, mytask.done()
        #result = await mytask
        #return result
    #
    #     if 1 in data:
    #         if data[1] < 300:
    #             return {'time': data[1]}
    #
    #     await asyncio.gather(
    #         get_time(2, data, error_dict, timeout),
    #         get_time(3, data, error_dict, timeout)
    #     )
    #
    # print(data)
    # return {'time': min(list(data.values()))} if data else \
    #        {key: value for key, value in error_dict.items()}
##

