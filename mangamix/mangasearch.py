import logging
import hashlib

import elastic_transport
import elasticsearch
from elasticsearch import AsyncElasticsearch

from mangamix.settings import ES_INDEX, ES_HOST, ES_USER, ES_PASSWORD


class Mangasearch:

    def __init__(self):
        self.logger = logging.getLogger(f'{__name__}.{__class__.__name__}')
        self.es = AsyncElasticsearch(hosts=ES_HOST, http_auth=(ES_USER, ES_PASSWORD), retry_on_timeout=True)

    async def get_animes(self) -> list[str]:
        self.logger.info(f'Try to get all animes')
        result = []
        try:
            response = await self.es.search(index=ES_INDEX, size=100, from_=9000)
            print(response.body['hits']['hits'][0]['_source']['name'])
            print(response)
        except (elastic_transport.ConnectionError, elasticsearch.AuthenticationException) as e:
            self.logger.warning(e)

        return result