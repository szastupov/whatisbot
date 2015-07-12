import logging
import asyncio
import os
from aiotg import TgBot

bot = TgBot(os.environ["API_TOKEN"])
logger = logging.getLogger("WhatisBot")


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
    response = yield from bot.session.request('GET', url, params=params)
    assert response.status == 200
    return (yield from response.json())


@asyncio.coroutine
def wiki(message, text, lang="en", not_found="I don't know :("):
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


@bot.command(r"/?(что такое|что за|опредиление|вики) ([^\?]+)\??")
def wiki_ru(message, match):
    return wiki(message, match.group(2), "ru", "Не знаю :(")


@bot.command(r"/?(que es|qué es|que significa|qué significa|quien es|quién es) ([^\?]+)\??")
def wiki_es(message, match):
    return wiki(message, match.group(2), "es", "No sé :(")


@bot.command(r"/?(was ist|wo ist) ([^\?]+)\??")
def wiki_de(message, match):
    return wiki(message, match.group(2), "de", "Nicht wissen :(")


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


@bot.default
def default(message):
    return wiki(message, message.text)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, filename="WhatisBot.log")

    bot.run()
