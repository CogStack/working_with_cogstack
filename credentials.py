from typing import List
# CogStack login details
## Any questions on what these details are please contact your local CogStack administrator.

hosts: List[str] = [ 
    # "https://cogstack-es-1:9200",  # This is an example of a CogStack ElasticSearch instance.
 ]  # This is a list of your CogStack ElasticSearch instances.

## These are your login details (either via http_auth or API) Should be in str format
username = None
password = None
# If you are using API key authentication
# Use either "id" and "api_key" or "encoded" field, or both.
api_key = {
            "id": "", # This is the API key id issued by your cogstack administrator.
            "api_key": "", # This is the api key issued by your cogstack administrator.
            "encoded": ""  # This is the encoded api key issued by your cogstack administrator.
            }

# NLM authentication
# The UMLS REST API requires a UMLS account for the authentication described below. 
# If you do not have a UMLS account, you may apply for a license on the UMLS Terminology Services (UTS) website.
# https://documentation.uts.nlm.nih.gov/rest/authentication.html

# UMLS api key auth
umls_apikey = None

# SNOMED authentication from NHS TRUD. International releases will require different API access creds.
# api key auth from NHS TRUD
# For more information please see: https://isd.digital.nhs.uk/trud/users/guest/filters/0/api
snomed_apikey = None
