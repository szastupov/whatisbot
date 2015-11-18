import logging
import asyncio
import aioredis
import aiohttp
import os
import json
from aiotg import TgBot

with open("config.json") as cfg:
    config = json.load(cfg)

bot = TgBot(**config)

logger = logging.getLogger("WhatisBot")
redis = None


async def search_wiki(text, lang="en"):
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
    response = await aiohttp.get(url, params=params)
    assert response.status == 200
    return (await response.json())


async def wiki(chat, text, lang=None, not_found="I don't know :("):

    plang = (await redis.hget(chat.sender["id"], "lang")) or "en"
    if not lang:
        lang = plang
    if lang != plang:
        await redis.hset(chat.sender["id"], "lang", lang)

    logger.info("%s:\t%s (%s)", chat.sender, text, lang)

    wiki = await search_wiki(text, lang)
    pages = wiki["query"]["pages"]

    for pid, page in pages.items():
        if pid == '-1':
            return (await chat.reply(not_found))

        title = page["title"].replace(" ", "_")
        wiki_link = "https://{0}.wikipedia.org/wiki/{1}".format(lang, title)
        result = "{0}\n{1}".format(page['extract'], wiki_link)

        await chat.reply(result)


@bot.command(r"/?(whatis|what is|who is|define|wiki) ([^\?]+)\??")
def wiki_en(chat, match):
    return wiki(chat, match.group(2), "en")


@bot.command(r"/?(что такое|что за|опредиление|вики|кто такой) ([^\?]+)\??")
def wiki_ru(chat, match):
    return wiki(chat, match.group(2), "ru", "Не знаю :(")


@bot.command(r"/?(que es|qué es|que significa|qué significa|quien es|quién es) ([^\?]+)\??")
def wiki_es(chat, match):
    return wiki(chat, match.group(2), "es", "No sé :(")


@bot.command(r"/?(was ist|wo ist) ([^\?]+)\??")
def wiki_de(chat, match):
    return wiki(chat, match.group(2), "de", "Nicht wissen :(")


@bot.command("(/start|/?help)")
def usage(chat, match):
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
    return chat.reply(text)


@bot.default
def default(chat, message):
    return wiki(chat, message["text"])


async def main():
    global redis
    host = os.environ.get('REDIS_HOST', 'localhost')
    redis = await aioredis.create_redis((host, 6379), encoding="utf-8")
    await bot.loop()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        bot.stop()
