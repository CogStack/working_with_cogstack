import getpass
import elasticsearch
import elasticsearch.helpers
import pandas as pd
from typing import Dict, List
from tqdm.notebook import tqdm
import eland as ed

import warnings
warnings.filterwarnings("ignore")

from credentials import *


class CogStack(object):
    """
    A class for interacting with Elasticsearch.
    
    Args:
        hosts (List[str]): A list of Elasticsearch host URLs.
        username (str, optional): The username to use when connecting to Elasticsearch. If not provided, the user will be prompted to enter a username.
        password (str, optional): The password to use when connecting to Elasticsearch. If not provided, the user will be prompted to enter a password.
        api (bool, optional): A boolean value indicating whether to use API keys or basic authentication to connect to Elasticsearch. Defaults to False (i.e., use basic authentication).
    """
    def __init__(self, hosts: List, username: str=None, password: str=None, api=False):

        if api:
            api_username, api_password = self._check_auth_details(username, password)
            self.elastic = elasticsearch.Elasticsearch(hosts=hosts,
                                                       api_key=(api_username, api_password),
                                                       verify_certs=False)
        else:
            username, password = self._check_auth_details(username, password)
            self.elastic = elasticsearch.Elasticsearch(hosts=hosts,
                                                       basic_auth=(username, password),
                                                       verify_certs=False)


    def _check_auth_details(self, username=None, password=None):
        """
        Prompt the user for a username and password if the values are not provided as function arguments.
        
        Args:
            api_username (str, optional): The API username. If not provided, the user will be prompted to enter a username.
            api_password (str, optional): The API password. If not provided, the user will be prompted to enter a password.
        
        Returns:
            Tuple[str, str]: A tuple containing the API username and password.
        """
        if username is None:
            username = input("Username: ")
        if password is None:
            password = getpass.getpass("Password: ")
        return username, password

    def get_docs_generator(self, index: List, query: Dict, es_gen_size: int=800, request_timeout: int=300):
        """
        Retrieve a generator object that can be used to iterate through documents in an Elasticsearch index.
        
        Args:
            index (List[str]): A list of Elasticsearch index names to search.
            query (Dict): A dictionary containing the search query parameters.
            es_gen_size (int, optional): The number of documents to retrieve per batch. Defaults to 800.
            request_timeout (int, optional): The time in seconds to wait for a response from Elasticsearch before timing out. Defaults to 300.

        Returns:
            generator: A generator object that can be used to iterate through the documents in the specified Elasticsearch index.
    """
        docs_generator = elasticsearch.helpers.scan(self.elastic,
                                                    query=query,
                                                    index=index,
                                                    size=es_gen_size,
                                                    request_timeout=request_timeout)
        return docs_generator

    def cogstack2df(self, query: Dict, index: str, column_headers=None, es_gen_size: int=800, request_timeout: int=300):
        """
        Retrieve documents from an Elasticsearch index and convert them to a Pandas DataFrame.
        
        Args:
            query (Dict): A dictionary containing the search query parameters.
            index (str): The name of the Elasticsearch index to search.
            column_headers (List[str], optional): A list of column headers to use for the DataFrame. If not provided, the DataFrame will have default column names.
            es_gen_size (int, optional): The number of documents to retrieve per batch. Defaults to 800.
            request_timeout (int, optional): The time in seconds to wait for a response from Elasticsearch before timing out. Defaults to 300.

        Returns:
            pandas.DataFrame: A DataFrame containing the retrieved documents.
    """
        docs_generator = elasticsearch.helpers.scan(self.elastic,
                                                    query=query,
                                                    index=index,
                                                    size=es_gen_size,
                                                    request_timeout=request_timeout)
        temp_results = []
        results = self.elastic.count(index=index, query=query['query'], request_timeout=300)
        for hit in tqdm(docs_generator, total=results['count'], desc="CogStack retrieved..."):
            row = dict()
            row['_index'] = hit['_index']
            row['_id'] = hit['_id']
            row['_score'] = hit['_score']
            row.update(hit['_source'])
            temp_results.append(row)
        if column_headers:
            df_headers = ['_index', '_id', '_score']
            df_headers.extend(column_headers)
            df = pd.DataFrame(temp_results, columns=df_headers)
        else:
            df = pd.DataFrame(temp_results)
        return df
    
    def DataFrame(self, index: str, columns=None):
        """
        Fast method to return a pandas dataframe from a CogStack search.
        :param index: List of indices
        :return: A dataframe object
        """
        return ed.DataFrame(es_client=self.elastic, es_index_pattern=index, columns=columns)

