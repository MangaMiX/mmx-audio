import logging

import elastic_transport
import elasticsearch
from elasticsearch import AsyncElasticsearch

from mangamix.settings import ES_INDEX, ES_HOST, ES_USER, ES_PASSWORD

ES_SIZE = 10

class Mangasearch:

    def __init__(self, start_index=-ES_SIZE):
        self.logger = logging.getLogger(f'{__name__}.{__class__.__name__}')
        self.es = AsyncElasticsearch(hosts=ES_HOST, http_auth=(ES_USER, ES_PASSWORD), retry_on_timeout=True)
        self.num = start_index

    async def get_next_animes(self) -> list[str]:
        self.logger.info(f'Try to get animes')
        try:
            response = await self.es.search(index=ES_INDEX, size=ES_SIZE, from_=self.get_anime_index())
            hits = response.body['hits']['hits']
            self.logger.info(f'Found {len(hits)} animes from ES')
            if len(hits) > 0:
                return self.get_anime_names(hits)
        except (elastic_transport.ConnectionError, elasticsearch.AuthenticationException) as e:
            self.logger.warning(e)
        return []
    
    def get_anime_index(self):
        self.num += ES_SIZE
        return self.num

    def get_anime_names(self, hits):
        return list(map(lambda hit: hit['_source']['name'], hits))
