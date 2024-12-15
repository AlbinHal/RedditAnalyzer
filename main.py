import json
import requests
from requests.auth import HTTPBasicAuth
from classes import Aggregator
from datetime import datetime, timedelta
import config

# FLAGS
VERBOSE = True

# PARAMETERS 
USER_AGENT = "RdtTrends/1.0 (Linux;Python/3.13) (by /u/SpktLaban)"
RESPONSE_FILE = "response.txt"




def main():
    """Main"""
    start = datetime.today() - timedelta(days=20)
    aggr = Aggregator(Subreddit="nsfw", Start=start)    
    while True:
        print("Search for a word >>")
        search_term = input()
        count = aggr.map.get(search_term.lower())
        print(f'There were {count} uses of {search_term.lower()} between {start} and now!')



if __name__ == "__main__":
    main()


def test():
    token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IlNIQTI1NjpzS3dsMnlsV0VtMjVmcXhwTU40cWY4MXE2OWFFdWFyMnpLMUdhVGxjdWNZIiwidHlwIjoiSldUIn0.eyJzdWIiOiJ1c2VyIiwiZXhwIjoxNzM0MzU3MzUwLjEyNDgyNywiaWF0IjoxNzM0MjcwOTUwLjEyNDgyNywianRpIjoicFFrWWF2bjNoRVR3ZzlsREl2X09ybERqUGdZTkp3IiwiY2lkIjoiTHpKdGNxdXVmQnlnOEJIdFlKbGh6QSIsImxpZCI6InQyXzFlcmFiejVpN2wiLCJhaWQiOiJ0Ml8xZXJhYno1aTdsIiwibGNhIjoxNzMzODY1NDYyMjMxLCJzY3AiOiJlSnlLVnRKU2lnVUVBQURfX3dOekFTYyIsImZsbyI6OX0.cppHpH31JIWx6er31MbRxDJwpYds1n9BmhCOJ7xvEb8SIzPN6UiUvLXkAxkErKj7h374WbQptqC_oFIRMdzQJWrUVW4MhRnWBh4cJTHr3EedozvztEj5DEMy1AqyD5ASO-i_wtvCXVIcBWG6dcK-WR3YoKDZGbP03tFFa3Lyql_bsoZKa1L6R6GNCYRP2qndLsvWCq9Zmk3pgXC6Fn5fssja2ga9U-2_JLenTEjFZIVLoqVbbLoyFvgudT8dC-7gwjnes7z-RDAt0YtjCPmE2QwVBMZjCn-xzdTC3HBDziGLHPkUe5zwjXU1pUmbi6OVLOn5B4iOQGBsEhA0OxOFtg"
    headers = {
        "Authorization": f'bearer {token}',
        "User-Agent" : "RdtTrends/1.0 (Linux;Python/3.13) (by /u/SpktLaban)"
    }
    url = "https://oauth.reddit.com/r/Python/new"

    response = requests.get(url, headers=headers, params={"limit": 1})
    data = response.json() 
    print(data)