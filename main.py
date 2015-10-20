import logging
import asyncio
import aioredis
import aiohttp
import os
from aiotg import TgBot

bot = TgBot(os.environ["API_TOKEN"])
logger = logging.getLogger("WhatisBot")
redis = None


@asyncio.coroutine
def search_duck(text):
    url = "http://api.duckduckgo.com/?format=json&pretty=1&q=" + text
    response = yield from aiohttp.get(url)
    return (yield from response.json())


@asyncio.coroutine
def search_wiki(text, lang="en"):
    url = "https://{0}.wikipedia.org/w/api.php".format(lang)
    params = {
        'titles': text,
        'action': 'query',
        'exintro': '',
        'format': 'json',
        'prop': 'extracts',
        'explaintext': '',
        'redirects': ''
    }
    response = yield from aiohttp.get(url, params=params)
    assert response.status == 200
    return (yield from response.json())


@asyncio.coroutine
def wiki(message, text, lang=None, not_found="I don't know :("):

    plang = (yield from redis.hget(message.sender, "lang")) or "en"
    if not lang:
        lang = plang
    if lang != plang:
        yield from redis.hset(message.sender, "lang", lang)

    logger.info("%s:\t%s (%s)", message.sender, text, lang)

    wiki = yield from search_wiki(text, lang)
    pages = wiki["query"]["pages"]

    for pid, page in pages.items():
        if pid == '-1':
            return (yield from message.reply(not_found))

        title = page["title"].replace(" ", "_")
        wiki_link = "https://{0}.wikipedia.org/wiki/{1}".format(lang, title)
        result = "{0}\n{1}".format(page['extract'], wiki_link)

        yield from message.reply(result)


@bot.command(r"/?(whatis|what is|who is|define|wiki) ([^\?]+)\??")
def wiki_en(message, match):
    return wiki(message, match.group(2), "en")


@bot.command(r"/?(что такое|что за|опредиление|вики|кто такой) ([^\?]+)\??")
def wiki_ru(message, match):
    return wiki(message, match.group(2), "ru", "Не знаю :(")


@bot.command(r"/?(que es|qué es|que significa|qué significa|quien es|quién es) ([^\?]+)\??")
def wiki_es(message, match):
    return wiki(message, match.group(2), "es", "No sé :(")


@bot.command(r"/?(was ist|wo ist) ([^\?]+)\??")
def wiki_de(message, match):
    return wiki(message, match.group(2), "de", "Nicht wissen :(")


@bot.command(r"/duck (.+)")
@asyncio.coroutine
def duck(message, match):
    result = yield from search_duck(match.group(1))
    if not result["Results"]:
        yield from message.reply("Nothing found :(")
        return

    text = "{Heading}\n{AbstractText}\n{AbstractURL}".format(**result)
    yield from message.reply(text)


@bot.command("(/start|/?help)")
def usage(message, match):
    text = """
Hi! I can search Wikipedia for you and your chat friends.

Here is how you can talk to me:
/define independence
/whatis love
what is love
who is Nikola Tesla?
что такое счастье
что за черт?
que es tequila
was ist liebe?

Created by @stepanz

If you like this bot, please rate it at: https://telegram.me/storebot?start=whatisbot
    """
    return message.reply(text)


@bot.command("/botfamily_verification_code")
def botfamily(message, match):
    return message.reply("F8FF7D52FF9889DE6D6BA0A93A09D768")


@bot.default
def default(message):
    return wiki(message, message.text)


@asyncio.coroutine
def main():
    global redis
    redis = yield from aioredis.create_redis(('localhost', 6379), encoding="utf-8")
    yield from bot.loop()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, filename="WhatisBot.log")

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        bot.stop()
