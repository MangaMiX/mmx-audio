import logging
import re

from pytube import Playlist

from utils.http_utils import HttpUtils


class MangatubeExtractor:

    def __init__(self):
        self.logger = logging.getLogger(f'{__name__}.{__class__.__name__}')

    async def search(self, anime: str):
        youtube_url = 'https://www.youtube.com/'
        playlist_prefix = f'{youtube_url}playlist?list='

        format_query = anime.replace(' ', '+') + '+OST'
        status, response = await HttpUtils.send(method='GET', url=f'{youtube_url}results?search_query={format_query}')

        match_playlist = re.search(r'playlist\?list=(\S*?)"', response.decode())
        if match_playlist:
            playlist_full_url = f'{playlist_prefix}{match_playlist.group(1)}'
            playlist = Playlist(url=playlist_full_url)
            self.logger.info(f'Anime: "{anime}" Playlist: "{playlist.title}", number of ost: {playlist.length}, query: "{format_query}"')

            index = 1
            for video in playlist.videos:
                if index > 10:
                    break
                # self.logger.debug(f'Title: {video.title}')
                index += 1

            # for video in playlist.videos:
            #     print(video.title)
            # video.streams.get_audio_only().stream_to_buffer()
        else:
            self.logger.debug(f'no playlist found for anime "{anime}", query: "{format_query}"')
