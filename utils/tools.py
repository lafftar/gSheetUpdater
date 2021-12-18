import asyncio
import functools
import sys
from asyncio import sleep
from json import dumps, JSONDecodeError
from random import randint
from time import sleep as sync_sleep
from typing import Union, NamedTuple

import aiohttp
import httpx
from aiohttp import client_exceptions
from colorama import Fore

from utils.root import get_project_root

FIRST_PRINT = False


def return_android_ua() -> str:
    platform_version = f'{randint(5, 10)}.0'
    browser_version = f'{randint(40, 80)}.0'
    return f"Mozilla/{platform_version} (Android {platform_version}; " \
           f"Mobile; rv:{browser_version}) Gecko/{browser_version} Firefox/{browser_version}"


def print_req_obj(req: httpx.Request, res: Union[httpx.Response, None] = None, print_now: bool = False) -> str:
    if res:
        res.read()
        req = res.request
        http_ver = res.http_version
    else:
        http_ver = 'HTTP/1.1(Guess.)'
    req.read()
    req_str = f'{req.method} {req.url} {http_ver}\n'
    for key, val in req.headers.items():
        req_str += f'{key}: {val}\n'

    if req.content:
        try:
            req_str += f'Req Body: {dumps(req.read().decode(), indent=4)}'
        except JSONDecodeError:
            req_str += f'Req Body: {req.content}'
    req_str += '\n'
    if print_now:
        print(f'{Fore.LIGHTBLUE_EX}{req_str}')
    return req_str


def print_req_info(res: httpx.Response, print_headers: bool = False, print_body: bool = False):
    if not res:
        print('No Response Body')
        return

    with open(f'{get_project_root()}/src.html', mode='w', encoding='utf-8') as file:
        try:
            with open(f'{get_project_root()}/src.json', mode='w', encoding='utf-8') as js_file:
                js_file.write(dumps(res.json(), indent=4))
                # print('wrote json')
        except JSONDecodeError:
            file.write(res.text)
    if not print_headers:
        return

    req_str = print_req_obj(res.request, res)

    resp_str = f'{res.http_version} {res.status_code} {res.reason_phrase}\n'
    for key, val in res.headers.items():
        resp_str += f'{key}: {val}\n'
    resp_str += f'Cookie: '
    for key, val in res.cookies.items():
        resp_str += f'{key}={val};'
    resp_str += '\n'
    if print_body:
        resp_str += f"Resp Body: {res.text}"
    resp_str += '\n|\n|'

    sep_ = '-' * 10
    boundary = '|'
    boundary += '=' * 100
    print(boundary)
    print(f'|{sep_}REQUEST{sep_}')
    print(req_str)
    print(f'|{sep_}RESPONSE{sep_}')
    print(resp_str)
    print(f'|History: {res.history}')
    for resp in res.history:
        print(resp.url, end=',')
    print()
    print(boundary)


async def send_req(req_obj: functools.partial, num_tries: int = 3) -> \
        Union[httpx.Response, aiohttp.ClientResponse, None]:
    """
    Central Request Handler. All requests should go through this.
    :param req_obj:
    :return:
    """
    for _ in range(num_tries):
        try:
            item = await req_obj()
            return item
        except (httpx.ConnectTimeout, httpx.ProxyError, httpx.ConnectError,
                httpx.ReadError, httpx.ReadTimeout, httpx.WriteTimeout, httpx.RemoteProtocolError,

                # aiohttp errors
                asyncio.exceptions.TimeoutError, client_exceptions.ClientHttpProxyError,
                client_exceptions.ClientProxyConnectionError,
                client_exceptions.ClientOSError,
                client_exceptions.ServerDisconnectedError
                ):
            await sleep(1)
    return


def update_title(terminal_title):
    bot_name = 'IPChecker'
    if sys.platform == 'linux':
        print(f'\33]0;[{bot_name}] | {terminal_title}\a', end='', flush=True)
    if sys.platform == 'win32':
        import ctypes
        ctypes.windll.kernel32.SetConsoleTitleW(f'[{bot_name}] | {terminal_title}')


class OrderStatusRow(NamedTuple):
    item: str
    sku: str
    size: str
    order_num: str
    date_of_purchase: str
    purchase_price: str
    status: str
    status_update_date: str