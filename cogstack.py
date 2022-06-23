import getpass
import elasticsearch
import elasticsearch.helpers
import pandas as pd
from typing import Dict, List
from tqdm.notebook import tqdm

import warnings
warnings.filterwarnings("ignore")


class CogStack(object):
    """
    :param hosts: List of CogStack host names
    :param username: basic_auth username
    :param password: basic_auth password
    :param api_username: api username
    :param api_password: api password
    :param api: bool
        If True then api credentials will be used
    """
    def __init__(self, hosts: List, username: str=None, password: str=None,
                 api_username: str=None, api_password: str=None, api=False):

        if api:
            api_username, api_password = self._check_api_auth_details(api_username, api_password)
            self.elastic = elasticsearch.Elasticsearch(hosts=hosts,
                                                       api_key=(api_username, api_password),
                                                       verify_certs=False)
        else:
            username, password = self._check_auth_details(username, password)
            self.elastic = elasticsearch.Elasticsearch(hosts=hosts,
                                                       basic_auth=(username, password),
                                                       verify_certs=False)

    def _check_api_auth_details(self, api_username=None, api_password=None):
        if api_username is None:
            api_username = input("API Username: ")
        if api_password is None:
            api_password = getpass.getpass("API Password: ")
        return api_username, api_password

    def _check_auth_details(self, username=None, password=None):
        if username is None:
            username = input("Username: ")
        if password is None:
            password = getpass.getpass("Password: ")
        return username, password

    def get_docs_generator(self, index: List, query: Dict, es_gen_size: int=800, request_timeout: int=300):
        """

        :param query: search query
        :param index: List of ES indices to search
        :param es_gen_size:
        :param request_timeout:
        :return: search generator object
        """
        docs_generator = elasticsearch.helpers.scan(self.elastic,
                                                    query=query,
                                                    index=index,
                                                    size=es_gen_size,
                                                    request_timeout=request_timeout)
        return docs_generator

    def cogstack2df(self, query: Dict, index: str, column_headers=None, es_gen_size: int=800, request_timeout: int=300):
        """
        Returns DataFrame from a CogStack search

        :param query: search query
        :param index: index or list of indices
        :param column_headers: specify column headers
        :param es_gen_size:
        :param request_timeout:
        :return: DataFrame
        """
        docs_generator = elasticsearch.helpers.scan(self.elastic,
                                                    query=query,
                                                    index=index,
                                                    size=es_gen_size,
                                                    request_timeout=request_timeout)
        temp_results = []
        results = self.elastic.count(index=index, query=query['query'], request_timeout=30)
        for hit in tqdm(docs_generator, total=results['count'], desc="CogStack retrieved..."):
            row = dict()
            row['_index'] = hit['_index']
            row['_type'] = hit['_type']
            row['_id'] = hit['_id']
            row['_score'] = hit['_score']
            row.update(hit['_source'])
            temp_results.append(row)
        if column_headers:
            df_headers = ['_index', '_type', '_id', '_score']
            df_headers.extend(column_headers)
            df = pd.DataFrame(temp_results, columns=df_headers)
        else:
            df = pd.DataFrame(temp_results)
        return df


