import re
import logging
import asyncio
import aiohttp

API_TOKEN = "redacted"
API_URL = "https://api.telegram.org"
API_TIMEOUT = 60
COMMANDS = []

conn = aiohttp.TCPConnector(verify_ssl=False)
session = aiohttp.ClientSession(connector=conn)


@asyncio.coroutine
def api_call(method, **params):
    url = "{0}/bot{1}/{2}".format(API_URL, API_TOKEN, method)
    response = yield from session.request('GET', url, params=params)
    assert response.status == 200
    return (yield from response.json())


def reply_to(message, text):
    return api_call('sendMessage',
        chat_id=message["chat"]["id"],
        text=text,
        reply_to_message_id=message["message_id"])

def command(regexp):
    def decorator(fn):
        COMMANDS.append((regexp, fn))
    return decorator

@asyncio.coroutine
def process_message(message):
    if not "text" in message:
        return
    text = message["text"].lower()

    for patterns, handler in COMMANDS:
        m = re.search(patterns, text)
        if m:
            return handler(message, m)

running = True

@asyncio.coroutine
def bot_loop():
    offset = 0
    while running:
        resp = yield from api_call('getUpdates', offset=offset+1, timeout=API_TIMEOUT)
        logging.debug("getUpdates %s", resp)
        for update in resp["result"]:
            offset = max(offset, update["update_id"])
            message = update["message"]
            asyncio.async(process_message(message))