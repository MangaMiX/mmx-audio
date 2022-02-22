import hashlib
from io import BytesIO
import logging
import re
from minio import Minio

from pytube import Playlist, YouTube

from mangamix.mangasearch import Mangasearch
from mangamix.settings import S3_ACCESS_KEY, S3_BUCKET, S3_HOST, S3_SECRET_KEY, MMX_EXTRACT_LIMIT

from utils.http_utils import HttpUtils


class MangatubeExtractor:

    def __init__(self):
        self.s3 = Minio(S3_HOST, S3_ACCESS_KEY, S3_SECRET_KEY, secure=False)
        self.logger = logging.getLogger(f'{__name__}.{__class__.__name__}')
        self.query_keywords = ['ost', 'soundtrack']
        self.mangasearch = Mangasearch()

    async def search(self, anime: str):
        youtube_url = 'https://www.youtube.com/'
        playlist_prefix = f'{youtube_url}playlist?list='

        for query_keyword in self.query_keywords:
            try:
                anime_with_keyword = anime + ' ' + query_keyword
                format_query = anime_with_keyword.replace(' ', '+')
                status, response = await HttpUtils.send(method='GET', url=f'{youtube_url}results?search_query={format_query}')

                if status == 200:
                    match_playlist = re.search(r'playlist\?list=(\S*?)"', response.decode())
                    if match_playlist:
                        playlist_full_url = f'{playlist_prefix}{match_playlist.group(1)}'
                        playlist = Playlist(url=playlist_full_url)
                        if self.__valid(playlist.title):
                            self.logger.info(f'Anime: "{anime}" Playlist: "{playlist.title}", '
                                             f'number of ost: {playlist.length}, query: "{format_query}"')
                            await self.__extract_audio(anime, playlist.videos)
                            break
                        else:
                            self.logger.debug(f'Invalid playlist: "{playlist.title}" for anime "{anime}", query: "{format_query}"')
                    else:
                        self.logger.debug(f'no playlist found for anime "{anime}", query: "{format_query}"')
            except (KeyError, TimeoutError, ValueError) as e:
                self.logger.error(f'An exception of type {type(e)} with arguments: {e.args} occurred. '
                                  f'Anime "{anime}", query: "{format_query}".')

    async def __extract_audio(self, anime: str, videos: list[YouTube]):
        index = 1
        for video in videos:
            if index > MMX_EXTRACT_LIMIT:
                return
            s3_path = self.__store_audio(anime, video)
            await self.mangasearch.update_audio(anime, s3_path)
            index += 1

    def __valid(self, title: str):
        for query_keyword in self.query_keywords:
            if query_keyword in title.lower().replace(' ', ''):
                return True
        return False

    def __store_audio(self, anime: str, video: YouTube) -> str:
        buffer = BytesIO()
        s3_path = f'{MangatubeExtractor.__hash_name(anime)}/audio/{MangatubeExtractor.__hash_name(video.title)}.mp4'
        video.streams.get_audio_only().stream_to_buffer(buffer)
        buffer.seek(0)
        filename = MangatubeExtractor.__encode_filename(video.title)
        self.s3.put_object(bucket_name=S3_BUCKET, object_name=s3_path, data=buffer,
                           length=buffer.getbuffer().nbytes, metadata={"filename": {filename}})
        self.logger.debug(f'Anime: "{anime}", Audio: "{video.title}" stored in s3. (path: "{s3_path}")')
        buffer.close()
        return s3_path

    @staticmethod
    def __encode_filename(filename):
        return filename.encode('ascii', 'ignore').decode().replace(' ', '_')

    @staticmethod
    def __hash_name(name: str):
        return hashlib.sha256(name.encode('utf-8')).hexdigest()
