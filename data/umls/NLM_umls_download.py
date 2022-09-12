"""
Automating UMLS Terminology Services (UTS) Downloads
The following instructions will allow you to automate the download of RxNorm, UMLS, or SNOMED CT files.


Step 1: Get your API key from your UTS profile.
        You can find the API key in the UTS ‘My Profile’ area after signing in. An API key remains active as long as
        the associated UTS account is active.
        https://uts.nlm.nih.gov/uts/?_gl=1*veo3ht*_ga*MTkwNzE1ODcyOC4xNjYyOTcxNDg3*_ga_P1FPTH9PL4*MTY2Mjk3MTQ4Ni4xLjEuMTY2Mjk3MzA0OS4wLjAuMA..

"""
import requests
import sys

apikey = ''  # please add apikey
DOWNLOAD_URL = 'https://download.nlm.nih.gov/umls/kss/2022AA/umls-2022AA-full.zip'  # Change this to service required
PATH_TO_DOWNLOAD = ''

print(DOWNLOAD_URL)
value = DOWNLOAD_URL.split('/')

if not apikey:
    sys.exit("Please enter you api key ")

if not DOWNLOAD_URL:
    print("Usage: curl-uts-downloads-apikey.sh  download_url ")
    print("  For full UMLS:")
    print("  e.g.   curl-uts-download-apikey.sh https://download.nlm.nih.gov/umls/kss/2022AA/umls-2022AA-full.zip")
    print("  For RxNorm:")
    print("  e.g.   curl-uts-download-apikey.sh https://download.nlm.nih.gov/umls/kss/rxnorm/RxNorm_full_current.zip")
    print("         curl-uts-download-apikey.sh https://download.nlm.nih.gov/umls/kss/rxnorm/RxNorm_weekly_current.zip")
    sys.exit("Download_url is empty")

url = 'https://utslogin.nlm.nih.gov/cas/v1/api-key'
param = {'apikey': apikey}
headers = {'Content-type': 'application/x-www-form-urlencoded'}

TGTresponse = requests.post(url, headers=headers, data=param)
first, second = TGTresponse.text.split('api-key/')
TGTTicket, fourth = second.split('" method')

print(TGTTicket)

url = 'https://utslogin.nlm.nih.gov/cas/v1/tickets/'+TGTTicket
param = {'service': DOWNLOAD_URL}
headers = {'Content-type': 'application/x-www-form-urlencoded'}

STResponse = requests.post(url, headers=headers, data=param)

print(STResponse.text)

url = DOWNLOAD_URL+'?ticket='+STResponse.text
r = requests.get(url, allow_redirects=True)
open('2022AA_UMLS_full_current.zip', 'wb').write(r.content)

with open(PATH_TO_DOWNLOAD + value[len(value)-1], 'wb') as f:
    f.write(r.content)

# Retrieve HTTP meta-data
print(r.status_code)
print(r.headers['content-type'])
print(r.encoding)

print(f'File saved to: {str(PATH_TO_DOWNLOAD + value[len(value)-1])}')
print('Download completed')
