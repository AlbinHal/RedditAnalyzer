import json
import requests
import config
import utils
from requests.auth import HTTPBasicAuth
from classes import Aggregator

# FLAGS
VERBOSE = True

# PARAMETERS 
USER_AGENT = "RdtTrends/1.0 (Linux;Python/3.13) (by /u/SpktLaban)"
RESPONSE_FILE = "response.txt"

def get_oauth_token():
    """Requests oauth2 token from /api/v1/access-token"""
    auth = HTTPBasicAuth(config.CLIENT_ID, config.CLIENT_SECRET)
    data = {
        "grant_type": "password",
        "username": config.USERNAME,
        "password": config.PASSWORD
    }
    headers = {"User-Agent": USER_AGENT}
    response = requests.post(
        "https://www.reddit.com/api/v1/access_token",
        auth=auth,
        data=data,
        headers=headers
    ) 
    return response.json()["access_token"]


def limit_rate(header) -> int :
    """Returns sleep interval to prevent exceeding sending limit"""
    used, remaining = header['x-ratelimit-used'], header['x-ratelimit-used']
    print(f'Used: ')


def main():
    """Main"""""" 
    token = get_oauth_token()
    headers = {
        "Authorization": f'bearer {token}',
        "User-Agent" : USER_AGENT
    }
    url = "https://oauth.reddit.com/r/Python/new"

    response = requests.get(url, headers=headers, params={"limit": 1})
    data = response.json() """
    agr = Aggregator(Debug=True, DebugPaths=[RESPONSE_FILE])


if __name__ == "__main__":
    main()

# DEBUGGING
def dLog(s):
    if VERBOSE:
        print(s)