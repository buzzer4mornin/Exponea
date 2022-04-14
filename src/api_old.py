import json
import httpx
import asyncio
from fastapi import FastAPI

app = FastAPI()


async def get_time(n: int, data: dict, error_dict: dict, timeout: int) -> None:
    try:
        async with httpx.AsyncClient(timeout=timeout/1000) as client:
            response = await client.get(
                "https://exponea-engineering-assignment.appspot.com/api/work"
            )
        json_time = response.json()
        data[n] = json_time['time']
    # Timeout exception
    except httpx.ConnectTimeout:
        error_dict[n] = 'Connection timeout error (server timeout)'
        print('Connection timeout. Try again...')
    except httpx.ReadTimeout:
        error_dict[n] = 'Httpx timeout error (given parameter timeout)'
        print(f'Request number {n} exceed timeout period...')
    # Api response internal error
    except json.decoder.JSONDecodeError:
        '''
            possible errors
            <Response [500 Internal Server Error]>
            <Response [429 Too many requests]>
        '''
        error_dict[n] = 'Internal server error or too many requests'
        print(f'Request number {n} has failed. Try again...')


@app.get("/api/smart/{timeout}")
async def api_smart(timeout: int) -> dict:
    data: dict = {}
    error_dict: dict = {}

    await asyncio.gather(
        get_time(1, data, error_dict, timeout)
    )
    if 1 in data:
        if data[1] < 300:
            return {'time': data[1]}

    await asyncio.gather(
        get_time(2, data, error_dict, timeout),
        get_time(3, data, error_dict, timeout)
    )

    print(data)
    return {'time': min(list(data.values()))} if data else \
           {key: value for key, value in error_dict.items()}


##

