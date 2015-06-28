import re
import logging
import asyncio
import aiohttp

API_URL = "https://api.telegram.org"
API_TIMEOUT = 60

conn = aiohttp.TCPConnector(verify_ssl=False)
session = aiohttp.ClientSession(connector=conn)


class TeleBot:
    def __init__(self, api_token, api_timeout=API_TIMEOUT):
        self.api_token = api_token
        self.api_timeout = api_timeout
        self.commands = []
        conn = aiohttp.TCPConnector(verify_ssl=False)
        self.session = aiohttp.ClientSession(connector=conn)
        self.running = True

    @asyncio.coroutine
    def api_call(self, method, **params):
        url = "{0}/bot{1}/{2}".format(API_URL, self.api_token, method)
        response = yield from self.session.request('GET', url, params=params)
        assert response.status == 200
        return (yield from response.json())

    def reply_to(self, message, text):
        return self.api_call('sendMessage',
            chat_id=message["chat"]["id"],
            text=text,
            reply_to_message_id=message["message_id"])

    def command(self, regexp):
        def decorator(fn):
            self.commands.append((regexp, fn))
        return decorator

    @asyncio.coroutine
    def process_message(self, message):
        if not "text" in message:
            return
        text = message["text"].lower()

        for patterns, handler in self.commands:
            m = re.search(patterns, text)
            if m:
                return handler(message, m)

    @asyncio.coroutine
    def loop(self):
        offset = 0
        while self.running:
            resp = yield from self.api_call('getUpdates',
                offset=offset+1,
                timeout=self.api_timeout)

            for update in resp["result"]:
                logging.debug("update %s", update)
                offset = max(offset, update["update_id"])
                message = update["message"]
                asyncio.async(self.process_message(message))

