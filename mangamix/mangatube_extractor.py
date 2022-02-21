import hashlib
from io import BytesIO
import logging
import re
from minio import Minio

from pytube import Playlist
from mangamix.settings import S3_ACCESS_KEY, S3_BUCKET, S3_HOST, S3_SECRET_KEY

from utils.http_utils import HttpUtils


class MangatubeExtractor:

    def __init__(self):
        self.s3 = Minio(S3_HOST, S3_ACCESS_KEY, S3_SECRET_KEY, secure=False)
        self.logger = logging.getLogger(f'{__name__}.{__class__.__name__}')
        self.query_keywords = ['ost', 'soundtrack', 'music']

    async def search(self, anime: str):
        youtube_url = 'https://www.youtube.com/'
        playlist_prefix = f'{youtube_url}playlist?list='

        for query_keyword in self.query_keywords:
            anime_with_keyword = anime + ' ' + query_keyword
            format_query = anime_with_keyword.replace(' ', '+')
            status, response = await HttpUtils.send(method='GET', url=f'{youtube_url}results?search_query={format_query}')

            if status == 200:
                match_playlist = re.search(r'playlist\?list=(\S*?)"', response.decode())
                if match_playlist:
                    playlist_full_url = f'{playlist_prefix}{match_playlist.group(1)}'
                    playlist = Playlist(url=playlist_full_url)
                    if self.valid(playlist.title):
                        self.logger.info(f'Anime: "{anime}" Playlist: "{playlist.title}", number of ost: {playlist.length}, query: "{format_query}"')

                        index = 1
                        for video in playlist.videos:
                            if index > 10: # Store only 10 soundtracks for the moment
                                break
                            self.store_audio(anime, video)
                            index += 1
                        break
                    else:
                        self.logger.debug(f'Invalid playlist: "{playlist.title}" for anime "{anime}", query: "{format_query}"')
                else:
                    self.logger.debug(f'no playlist found for anime "{anime}", query: "{format_query}"')

    def valid(self, playlist: str):
        for query_keyword in self.query_keywords:
            if query_keyword in playlist.lower():
                return True
        return False

    def store_audio(self, anime: str, video):
        buffer = BytesIO()
        object_path = f'audio/{MangatubeExtractor.hash_name(anime)}/{MangatubeExtractor.hash_name(video.title)}.mp4'
        video.streams.get_audio_only().stream_to_buffer(buffer)
        buffer.seek(0)
        filename = MangatubeExtractor.encode_filename(video.title)
        self.s3.put_object(bucket_name=S3_BUCKET, object_name=object_path, data=buffer, length=buffer.getbuffer().nbytes, metadata={"filename": {filename}})
        self.logger.debug(f'Anime: "{anime}", Audio: "{video.title}" stored in s3. (path: "{object_path}")')
        buffer.close()

    @staticmethod
    def encode_filename(filename):
        return filename.encode('ascii', 'ignore').decode().replace(' ', '_')

    @staticmethod
    def hash_name(name: str):
        return hashlib.sha256(name.encode('utf-8')).hexdigest()
