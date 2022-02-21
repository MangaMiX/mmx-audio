import asyncio
import logging
from logging import config
import os
import platform

from mangamix.mangasearch import Mangasearch
from mangamix.mangatube_extractor import MangatubeExtractor

config.fileConfig(os.path.join(os.getcwd(), 'log.conf'))
logger = logging.getLogger(f'{__name__}')


async def run():
    mangasearch = Mangasearch()
    mangatube_extractor = MangatubeExtractor()
    found_anime = True
    while found_anime:
        anime_names = await mangasearch.get_next_animes()
        if len(anime_names) > 0:
            for anime_name in anime_names:
                await mangatube_extractor.search(anime_name)
        else:
            found_anime = False

if __name__ == '__main__':
    if platform.system().lower().find('windows') != -1:  # For windows compatibility
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run())
