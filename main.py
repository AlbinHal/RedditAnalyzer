import json
import requests
from requests.auth import HTTPBasicAuth
from classes import Aggregator, ApiClient
from config import TOKEN

# FLAGS
VERBOSE = True

# PARAMETERS 
USER_AGENT = "RdtTrends/1.0 (Linux;Python/3.13) (by /u/SpktLaban)"
RESPONSE_FILE = "response.txt"



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
    #agr = Aggregator(Debug=True, DebugPaths=[RESPONSE_FILE])
    client = ApiClient(TOKEN)
    client.subreddit()

if __name__ == "__main__":
    main()

# DEBUGGING
def dLog(s):
    if VERBOSE:
        print(s)