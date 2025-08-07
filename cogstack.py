import getpass
import traceback
from typing import Dict, List, Any, Optional, Iterable, Sequence, Tuple
import elasticsearch
import elasticsearch.helpers as es_helpers
from IPython.display import display, HTML
import pandas as pd
import tqdm

import warnings
warnings.filterwarnings("ignore")

from credentials import *

class CogStack(object):
    """
    A class for interacting with Elasticsearch.
    
    Parameters
    ------------
        hosts : List[str]
            A list of Elasticsearch host URLs.
    """
    ES_TIMEOUT = 300
    
    def __init__(self, hosts: List[str]):
        self.hosts = hosts

    @classmethod
    def with_basic_auth(cls, hosts: List[str], username: Optional[str] = None, password: Optional[str] = None) -> 'CogStack':
        """
        Create an instance of CogStack using basic authentication.

        Parameters
        ----------
        hosts : List[str]
            A list of Elasticsearch host URLs.
        username : str, optional
            The username to use when connecting to Elasticsearch. If not provided, the user will be prompted to enter a username.
        password : str, optional
            The password to use when connecting to Elasticsearch. If not provided, the user will be prompted to enter a password.
        Returns 
        -------
            CogStack: An instance of the CogStack class.
        """
        cs = cls(hosts)
        cs.use_basic_auth(username, password)
        return cs
    
    @classmethod
    def with_api_key_auth(cls, hosts: List[str], api_key: Optional[Dict] = None) -> 'CogStack':
        """
        Create an instance of CogStack using API key authentication.

        Parameters
        ----------
        hosts : List[str]
            A list of Elasticsearch host URLs.
        apiKey : Dict, optional

            API key object with "id" and "api_key" or "encoded" strings as fields. Generated in Elasticseach or Kibana
            and provided by your CogStack administrator.
            
            If not provided, the user will be prompted to enter API key "encoded" value.
            
            Example:  
                .. code-block:: json
                        {
                            "id": "API_KEY_ID",
                            "api_key": "API_KEY",
                            "encoded": "API_KEY_ENCODED_STRING"
                        }
        Returns
        -------
            CogStack: An instance of the CogStack class.
        """
        cs = cls(hosts)
        cs.use_api_key_auth(api_key)
        return cs

    def use_basic_auth(self, username: Optional[str] = None, password:Optional[str] = None) -> 'CogStack':
        """
        Create an instance of CogStack using basic authentication.
        If the `username` or `password` parameters are not provided, the user will be prompted to enter them.

        Parameters
        ----------
        username : str, optional 
            The username to use when connecting to Elasticsearch. If not provided, the user will be prompted to enter a username.
        password : str, optional 
            The password to use when connecting to Elasticsearch. If not provided, the user will be prompted to enter a password.
        
        Returns
        -------
            CogStack: An instance of the CogStack class.
        """
        if username is None:
            username = input("Username: ")
        if password is None:
            password = getpass.getpass("Password: ")

        return self.__connect(basic_auth=(username, password) if username and password else None)
    
    def use_api_key_auth(self,  api_key: Optional[Dict] = None) -> 'CogStack':
        """
        Create an instance of CogStack using API key authentication.

        Parameters
        ----------
        apiKey : Dict, optional

            API key object with "id" and "api_key" or "encoded" strings as fields. Generated in Elasticsearch or Kibana
            and provided by your CogStack administrator.
            
            If not provided, the user will be prompted to enter API key "encoded" value.
            
            Example:  
             .. code-block:: json
                    {
                        "id": "API_KEY_ID",
                        "api_key": "API_KEY",
                        "encoded": "API_KEY_ENCODED_STRING"
                    }
        
        Returns
        -------
            CogStack: An instance of the CogStack class.
        """
        if not api_key:
            api_key = {"encoded": input("Encoded API key: ")}
        
        if api_key is not None:
            if isinstance(api_key, str):
                # If api_key is a string, it is assumed to be the encoded API key
                encoded = api_key
                hasEncodedValue = True
            elif isinstance(api_key, Dict):
                # If api_key is a dictionary, check for "encoded", "id" and "api_key" keys
                if "id" in api_key.keys() and api_key["id"] != '' and "api_key" in api_key.keys() and api_key["api_key"] != '':
                # If both "id" and "api_key" are present, use them
                    encoded = None
                    hasEncodedValue = False
                else:
                    # If "encoded" is present, use it; otherwise prompt for it
                    encoded = api_key["encoded"] if "encoded" in api_key.keys() and api_key["encoded"] != '' else input("Encoded API key: ")
                    hasEncodedValue = encoded is not None and encoded != ''

            if(not hasEncodedValue):
                api_Id = api_key["id"] if "id" in api_key.keys() and api_key["id"] != '' else input("API Id: ")
                api_key = api_key["api_key"] if "api_key" in api_key.keys() and api_key["api_key"] != '' else getpass.getpass("API Key: ")

            return self.__connect(api_key=encoded if hasEncodedValue else (api_Id, api_key))
    
    def __connect(self, basic_auth : Optional[Tuple[str,str]] = None, api_key: Optional[str | Tuple[str, str]] = None) -> 'CogStack':
        """ Connect to Elasticsearch using the provided credentials.
        Parameters
        ----------
            basic_auth : Tuple[str, str], optional
                A tuple containing the username and password for basic authentication.
            api_key : str or Tuple[str, str], optional
                The API key or a tuple containing the API key ID and API key for API key authentication.
        Returns
        -------
            CogStack: An instance of the CogStack class.
        Raises
        ------
            Exception: If the connection to Elasticsearch fails.
        """
        self.elastic = elasticsearch.Elasticsearch(hosts=hosts,
                                                  api_key=api_key,
                                                  basic_auth=basic_auth,
                                                  verify_certs=False,
                                                  request_timeout=self.ES_TIMEOUT)
        if not self.elastic.ping():
            raise Exception("CogStack connection failed. Please check your host list and credentials and try again.") 
        print("CogStack connection established successfully.")
        return self
    
    def get_indices_and_aliases(self):
        """
        Retrieve indices and their aliases

        Returns:
        ---------
            A table of indices and aliases to use in subsequent queries
        """
        all_aliases = self.elastic.indices.get_alias().body
        index_aliases_coll = []
        for index in all_aliases:
            index_aliases = dict()
            index_aliases['Index'] = index 
            aliases=[]
            for alias in all_aliases[index]['aliases']:
                aliases.append(alias)
            index_aliases['Aliases'] = ', '.join(aliases)
            index_aliases_coll.append(index_aliases)
        with pd.option_context('display.max_colwidth', None):
            return pd.DataFrame(index_aliases_coll, columns=['Index', 'Aliases'])

    def get_index_fields(self,  index: str | Sequence[str]):
        """
        Retrieve indices and their fields with data type

        Parameters
        ----------
         index: str | Sequence[str] 
            Name(s) of indices or aliases for which the list of fields is retrieved

        Returns
        ----------
            pandas.DataFrame 
                A DataFrame containing index names and their fields with data types
        
        Raises
        ------
            Exception
                If the operation fails for any reason.
        """
        try:
            all_mappings = self.elastic.indices.get_mapping(index=index, allow_no_indices=False).body
            columns= ['Field', 'Type']
            if (isinstance(index, List)):
                columns.insert(0, 'Index')
            index_mappings_coll = []
            for index in all_mappings:
                for property in all_mappings[index]['mappings']['properties']:
                    index_mapping = dict()
                    index_mapping['Index'] = index
                    index_mapping['Field'] = property
                    index_mapping['Type'] = all_mappings[index]['mappings']['properties'][property]['type'] if "type" in all_mappings[index]['mappings']['properties'][property].keys() else '?' 
                    index_mappings_coll.append(index_mapping)
        except Exception as err: 
            raise Exception(f"Unexpected {err=}, {type(err)=}")
        with pd.option_context('display.max_rows', len(index_mappings_coll) + 1):
            return display(pd.DataFrame(data= index_mappings_coll, columns=columns))

    def count_search_results(self, index: str | Sequence[str], query: dict):
          """
           Count number of documents returned by the query
           
           Parameters
           ----------
                index : str or Sequence[str]
                        The name(s) of the Elasticsearch indices or their aliases to search.
                        
                query : dict
                        A dictionary containing the search query parameters.  
                        Query can start with `query` key and contain other query options which will be ignored 

                            .. code-block:: json 
                                {"query": {"match": {"title": "python"}}}}
                        or only consist of content of `query` block
                            .. code-block:: json 
                                {"match": {"title": "python"}}}
          """
          query = self.__extract_query(query=query)
          count = self.elastic.count(index=index, query=query)['count']
          return f"Number of documents: {format(count, ',')}"
    
    def read_data_with_scan(self, 
                            index: str, 
                            query: dict, 
                            include_fields: list[str]=None, 
                            size: int=1000, 
                            request_timeout: int=ES_TIMEOUT,
                            show_progress: bool = True):
        """
        Retrieve documents from an Elasticsearch index using search query and elasticsearch scan helper function.
        The function converts search results to a Pandas DataFrame and does not return current scroll id if the process fails.
        
        Parameters
        ----------
            index : str or Sequence[str]
                    The name(s) of the Elasticsearch indices or their aliases to search.
            query : dict
                    A dictionary containing the search query parameters.    
                    Query can start with `query` key and contain other query options which will be used in the search 

                        .. code-block:: json 
                            {"query": {"match": {"title": "python"}}}}
                    or only consist of content of `query` block (preferred method to avoid clashing with other parameters)
                        .. code-block:: json 
                            {"match": {"title": "python"}}}
                
            include_fields : list[str], optional
                    A list of fields to be included in search results and presented as columns in the DataFrame. 
                    If not provided, only _index, _id and _score fields will be included.
                    Columns <strong>_index, _id, _score</strong> are present in all search results
            size : int, optional, default = 1000
                    The number of documents to be returned by the query or scroll API during each iteration. 
                    <strong>MAX: 10,000</strong>.
            request_timeout : int, optional, default=300
                    The time in seconds to wait for a response from Elasticsearch before timing out.
            show_progress : bool, optional, default=True
                    Whether to show the progress in console.
        Returns
        ------
        pandas.DataFrame 
            A DataFrame containing the retrieved documents.
        
        Raises
        ------
        Exception
            If the search fails or cancelled by the user.    
        """
        try:
            self.__validate_size(size=size)
            if "query" not in query.keys():
                temp_query =  query.copy()
                query.clear()
                query["query"] = temp_query

            scan_results = es_helpers.scan(self.elastic,
                                             index=index,
                                             query=query,
                                             size=size,
                                             request_timeout=request_timeout,
                                             source=False, 
                                             fields = include_fields)
            all_mapped_results = []
            results = self.elastic.count(index=index, query=query["query"], request_timeout=request_timeout) 
            pr_bar = tqdm.tqdm(scan_results, total=results["count"], desc="CogStack retrieved...", disable=not show_progress, colour='green')
            all_mapped_results = self.__map_search_results(hits=pr_bar)
        except BaseException as err: 
            if(type(err) is KeyboardInterrupt):
                pr_bar.bar_format = "%s{l_bar}%s{bar}%s{r_bar}" % ("\033[0;33m", "\033[0;33m", "\033[0;33m")
                pr_bar.set_description("CogStack read cancelled! Processed", refresh=True)
                print("Request cancelled and current search_scroll_id deleted...")
            else:
                pr_bar.bar_format = "%s{l_bar}%s{bar}%s{r_bar}" % ("\033[0;31m", "\033[0;31m", "\033[0;31m")
                pr_bar.set_description("CogStack read failed! Processed", refresh=True)
                print(Exception(f"Unexpected {err=},\n {traceback.format_exc()}, {type(err)=}"))
        finally:
           return self.__create_dataframe(all_mapped_results, include_fields)
        
    def read_data_with_scroll(self, 
                  index: str | Sequence[str], 
                  query: dict, 
                  include_fields:Optional[list[str]]=None, 
                  size: int=1000, 
                  search_scroll_id: Optional[str] = None,
                  request_timeout: Optional[int]=ES_TIMEOUT,
                  show_progress: Optional[bool] = True):
            
        """
        Retrieves documents from an Elasticsearch index using search query and scroll API.
        Default scroll timeout is set to 10 minutes.
        The function converts search results to a Pandas DataFrame.
        
        Parameters
        ----------
            index : str or Sequence[str]
                    The name(s) of the Elasticsearch indices or their aliases to search.
            query : dict
                    A dictionary containing the search query parameters.  
                    Query can start with `query` key and contain other query options which will be ignored 

                        .. code-block:: json 
                            {"query": {"match": {"title": "python"}}}}
                    or only consist of content of `query` block
                        .. code-block:: json 
                            {"match": {"title": "python"}}}
            include_fields : list[str], optional
                    A list of fields to be included in search results and presented as columns in the DataFrame. 
                    If not provided, only _index, _id and _score fields will be included.
                    Columns <strong>_index, _id, _score</strong> are present in all search results
            size : int, optional, default = 1000
                    The number of documents to be returned by the query or scroll API during each iteration. 
                    <strong>MAX: 10,000</strong>.
            search_scroll_id : str, optional
                    The value of the last <strong>scroll_id</strong> returned by scroll API and used to continue the search if the current search fails.  
                    The value of <strong>scroll_id</strong> times out after <strong>10 minutes</strong>. After which the search will have to be restarted.  
                    <strong>Note:</strong> Absence of this parameter indicates a new search.
            request_timeout : int, optional, default=300
                    The time in seconds to wait for a response from Elasticsearch before timing out.
            show_progress : bool, optional, default=True
                    Whether to show the progress in console.  
                    <strong>IMPORTANT:</strong> The progress bar displays the total hits for the query even if continuing the search using `search_scroll_id`.
        Returns
        ------
        pandas.DataFrame 
            A DataFrame containing the retrieved documents.
        
        Raises
        ------
        Exception
            If the search fails or cancelled by the user.    
            If the search fails, error message includes the value of current `search_scroll_id` which can be used as a function parameter to continue the search.  
            <strong>IMPORTANT:</strong> If the function fails after `scroll` request, the subsequent request will skip results of the failed scroll by the value of `size` parameter.
        """
        try:
            self.__validate_size(size=size)
            query = self.__extract_query(query=query)
            result_count = size
            all_mapped_results =[]
            search_result=None
            pr_bar = tqdm.tqdm(desc="CogStack retrieved...", disable=not show_progress, colour='green') 

            if search_scroll_id is None:
                search_result = self.elastic.search(index=index, 
                                               size=size,
                                               query=query, 
                                               fields=include_fields, 
                                               source=False, 
                                               scroll="10m",
                                               timeout=f"{request_timeout}s",
                                               rest_total_hits_as_int=True) 
                
                pr_bar.total = search_result.body['hits']['total']
                hits = search_result.body['hits']['hits']
                result_count = len(hits)
                search_scroll_id = search_result.body['_scroll_id']
                all_mapped_results.extend(self.__map_search_results(hits=hits))
                pr_bar.update(len(hits))

            while search_scroll_id and result_count == size:
                # Perform ES scroll request
                search_result = self.elastic.scroll(scroll_id=search_scroll_id, scroll="10m", rest_total_hits_as_int=True)
                hits = search_result.body['hits']['hits']
                pr_bar.total = pr_bar.total if pr_bar.total else search_result.body['hits']['total']
                all_mapped_results.extend(self.__map_search_results(hits=hits))
                search_scroll_id = search_result.body['_scroll_id']
                result_count = len(hits)
                pr_bar.update(result_count)
                
            self.elastic.clear_scroll(scroll_id = search_scroll_id)
        except BaseException as err: 
            if(type(err) is KeyboardInterrupt):
                pr_bar.bar_format = "%s{l_bar}%s{bar}%s{r_bar}" % ("\033[0;33m", "\033[0;33m", "\033[0;33m")
                pr_bar.set_description("CogStack read cancelled! Processed", refresh=True)
                self.elastic.clear_scroll(scroll_id = search_scroll_id)
                print("Request cancelled and current search_scroll_id deleted...")
            else:
                pr_bar.bar_format = "%s{l_bar}%s{bar}%s{r_bar}" % ("\033[0;31m", "\033[0;31m", "\033[0;31m")
                pr_bar.set_description("CogStack read failed! Processed", refresh=True)
                print(Exception(f"Unexpected {err=},\n {traceback.format_exc()}, {type(err)=}"), f"{search_scroll_id=}", sep='\n')
        finally:
            return self.__create_dataframe(all_mapped_results, include_fields)

    def read_data_with_sorting(self, 
                               index: str | Sequence[str], 
                               query: dict, 
                               include_fields: Optional[list[str]]=None, 
                               size: Optional[int]=1000, 
                               sort: Optional[dict|list[str]] = {"id": "asc"},
                               search_after: Optional[list[str|int|float|Any|None]] = None,
                               request_timeout: Optional[int]=ES_TIMEOUT,
                               show_progress: Optional[bool] = True):
        """
        Retrieve documents from an Elasticsearch index using search query and convert them to a Pandas DataFrame.
        
        Parameters
        ----------
            index : str or Sequence[str]
                    The name(s) of the Elasticsearch indices or their aliases to search.
            query : dict
                    A dictionary containing the search query parameters.  
                    Query can start with `query` key and contain other query options which will be ignored 

                        .. code-block:: json 
                            {"query": {"match": {"title": "python"}}}}
                    or only consist of content of `query` block
                        .. code-block:: json 
                            {"match": {"title": "python"}}}
            include_fields : list[str], optional
                    A list of fields to be included in search results and presented as columns in the DataFrame. 
                    If not provided, only _index, _id and _score fields will be included.
                    Columns <strong>_index, _id, _score</strong> are present in all search results
            size : int, optional, default = 1000
                    The number of documents to be returned by the query or scroll API during each iteration. 
                    <strong>MAX: 10,000</strong>.
            sort : dict|list[str], optional, default = {"id": "asc"}
                    Sort field name(s) and order (`asc` or `desc`) in dictionary format or list of field names without order. 
                    `{"id":"asc"}` or `id` is added if not provided as a tiebreaker field. 
                    Default sorting order is `asc`
                    ><strong>Example:</strong>
                    - `dict : {"filed_Name" : "desc", "id" : "asc"}`
                    - `list : ["filed_Name", "id"]`
            search_after : list[str|int|float|Any|None], optional
                    The sort value of the last record in search results.   
                    Can be provided if the a search fails and needs to be restarted from the last successful search.  
                    Use the value of `search_after_value` from the error message
            request_timeout : int, optional, default = 300
                    The time in seconds to wait for a response from Elasticsearch before timing out.
            show_progress : bool, optional
                    Whether to show the progress in console. Defaults to true.

        Returns
        ------
            pandas.DataFrame 
                A DataFrame containing the retrieved documents.
                
        Raises
        ------
            Exception 
                If the search fails or cancelled by the user.  
                Error message includes the value of current `search_after_value` which can be used as a function parameter to continue the search.
    """
        try:
            result_count = size
            all_mapped_results =[]
            search_after_value = search_after

            self.__validate_size(size=size)
            query = self.__extract_query(query=query)

            if ((type(sort) is dict and 'id' not in sort.keys()) or (type(sort) is list and 'id' not in sort)):
                if type(sort) is dict:
                    sort['id'] = 'asc' 
                else:
                    sort.append('id')
            
            pr_bar = tqdm.tqdm(desc="CogStack retrieved...", disable=not show_progress, colour='green') 

            while result_count == size:
                search_result = self.elastic.search(index=index, 
                                               size=size,
                                               query=query, 
                                               fields=include_fields, 
                                               source=False, 
                                               sort=sort,
                                               search_after=search_after_value,
                                               timeout=f"{request_timeout}s",
                                               track_scores=True,
                                               allow_no_indices=False,
                                               rest_total_hits_as_int=True)
                
                hits = search_result['hits']['hits']
                all_mapped_results.extend(self.__map_search_results(hits=hits))
                result_count = len(hits)
                pr_bar.update(result_count)
                search_after_value = hits[-1]['sort']
                pr_bar.total = pr_bar.total if pr_bar.total else search_result.body['hits']['total']
        except BaseException as err: 
            if(type(err) is KeyboardInterrupt):
                pr_bar.bar_format = "%s{l_bar}%s{bar}%s{r_bar}" % ("\033[0;33m", "\033[0;33m", "\033[0;33m") 
                pr_bar.set_description("CogStack read cancelled! Processed", refresh=True)
                print("Request cancelled.")
            else:
                pr_bar.bar_format = "%s{l_bar}%s{bar}%s{r_bar}" % ("\033[0;31m", "\033[0;31m", "\033[0;31m")
                pr_bar.set_description("CogStack read failed! Processed", refresh=True)
                print(f"Unexpected {err=},\n {traceback.format_exc()}, {type(err)=}")
            print(f"The last {search_after_value=}")
        finally:
            return self.__create_dataframe(all_mapped_results, include_fields)

    def __extract_query(self, query: dict):
        if "query" in query.keys():
            query = query['query']
        return query

    def __validate_size(self, size):
        if size > 10000:
            raise ValueError('Size must not be greater then 10000')
        
    def __map_search_results(self, hits: Iterable):
        hit: dict
        for hit in hits:
            row = dict()
            row['_index'] = hit['_index']
            row['_id'] = hit['_id']
            row['_score'] = hit['_score']
            if 'fields' in hit.keys():
                row.update({k: ', '.join(map(str, v)) for k,v in dict(hit['fields']).items()})
            yield row

    def __create_dataframe(self, all_mapped_results, column_headers):
            """
            Create a Pandas DataFrame from the search results.

            Parameters
            ----------
                all_mapped_results : list
                    The list of mapped search results.
                column_headers : list or None
                    The list of column headers to include in the DataFrame.

            Returns
            -------
                pandas.DataFrame
                    A DataFrame containing the search results.
            """
            df_headers = ['_index', '_id', '_score']
            if column_headers and "*" not in column_headers:
                df_headers.extend(column_headers)
                return pd.DataFrame(data=all_mapped_results, columns=df_headers)
            return pd.DataFrame(data=all_mapped_results)

def print_dataframe(df : pd.DataFrame, separator : str = '\\n'):
    """
      Replace <strong>separator</strong> string with HTML <strong>&lt;br/&gt;</strong> tag for printing in Notebook 

      Parameters:
      -----------
        df : DataFrame 
            Input DataFrame
        separator : str
            Separator to be replaced with HTML <strong>&lt;br/&gt;</strong>
    """
    return display(HTML(df.to_html().replace(separator, '<br/>')))

def list_chunker(user_list: List[Any], n: int) -> List[List[Any]]:
    """
    Divide a list into sublists of a specified size.
    
    Parameters:
    ----------
        user_list : List[Any]
            The list to be divided.
        n : int
            The size of the sublists.
    
    Returns:
    --------
        List[List[Any]]: A list of sublists containing the elements of the input list.
    """
    n=max(1, n)
    return [user_list[i:i+n] for i in range(0, len(user_list), n)]


