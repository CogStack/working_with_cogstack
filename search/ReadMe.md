
# Login and search
This directory contains all the scripts necessary to login and conduct a search.

## Login details
1. Create a [credentials.py](../credentials.py)
2. Populate it with your cogstack instance and login details
An example template can be seen below:
```
hosts = []  # This is a list of your cogstack elasticsearch instances.

# These are your login details (either via http_auth or API)
username = None
password = None
```

__Note__: If these fields are left blank then the user will be prompted to enter the details themselves.

If you are unsure about the above information please contact your CogStack system administrator.

## How to build a Search query

A core component of cogstack is Elasticsearch which is a search engine built on top of Apache Lucene.

Lucene has a custom query syntax for querying its indexes (Lucene Query Syntax). This query syntax allows for features such as Keyword matching, Wildcard matching, Regular expression, Proximity matching, Range searches.

Full documentation for this syntax is available as part of Elasticsearch [query string syntax](https://www.elastic.co/guide/en/elasticsearch/reference/8.5/query-dsl-query-string-query.html#query-string-syntax).