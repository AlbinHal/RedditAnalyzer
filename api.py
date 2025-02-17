from datetime import datetime, timedelta
from requests.auth import HTTPBasicAuth
from utils import read_file, SubRedditMode
from time import sleep

import requests

CONFIG = "config.json"

class Authenticator:
    """Handles API authentication"""
    BASE_URL = "https://ssl.reddit.com/api/v0/access_token" 
    def __init__(self):
        cfg: dict = read_file(CONFIG)
        self.user_agent = cfg['user_agent']
        self.username = cfg['username']
        self.__password = cfg['password']
        self.client_id = cfg['client_id']
        self.__client_secret = cfg['client_secret']
        self.token = cfg['token']
        self.token_expires = datetime.fromisoformat(cfg['token_expires'])

    def token_valid(self) -> bool:
       return self.token and self.token_expires - timedelta(hours=0) > datetime.today() 
    
    def update_token(self):
        if self.token_valid():
            return self.token
        response = requests.post(
            self.BASE_URL,
            auth = HTTPBasicAuth(self.client_id, self.__client_secret),
            data = {"grant_type": "password", "username": self.username, "password": self.__password},
            headers = {"User-Agent": self.user_agent}
        )        
        data = response.json()
        self.token = data.get("access_token")
        self.token_expires = datetime.now() + timedelta(seconds=data.get("expires_in"))

class ApiRequester:
    """Makes API calls, managers headers"""
    BASE_URL = "https://oauth.reddit.com/"
    def __init__(self):
        self.authenticator = Authenticator() 

    def make_request(self, endpoint, params=None):
        """No error handling"""
        token = self.authenticator.update_token()
        headers = {"Authorization": f'bearer {token}',
                "User-Agent": self.authenticator.user_agent}
        response = requests.get(f'{self.BASE_URL}{endpoint}',
                                params=params,
                                headers=headers)
        self._limit_rate(response.headers)
        return response
    
    def _limit_rate(self, header: dict) -> None:
        """Simply sleep if we are getting close to exceeding rate."""
        self.remaining = header.get("x-ratelimit-remaining", -1)
        refresh = header.get("x-ratelimit-reset", 600)
        if float(self.remaining) < 200:
            print("Limiting rate, sleeping...")
            sleep(60)
        return



class DataService:
    """Provides higher level methods for interacting with the API"""
    def __init__(self):
        self.api_requester = ApiRequester()

    def get_posts_by_subreddit(self, 
                               subreddit:str = "sweden",
                               subredditmode: SubRedditMode = "new",
                               count: int = 999,
                               ) -> list[dict]:
        """Get posts from a subreddit of choice"""
        posts = []
        endpoint = f'/r/{subreddit}/{subredditmode}'
        params = {"limit": 100 if count > 100 else count}
        page_key = 'after'

        while len(posts) < count:
            response = self.api_requester.make_request(
                endpoint, params
            )
            data = response.json()
            posts.extend([post["data"] for post in
                          data.get("data", {}).get("children", [])])
            
            # Stop fetching repeating content
            params[page_key] = data.get('data').get(page_key, {})
            if params[page_key] is None:
                break
            # Update "after" timestamp
        ret = []
        [ret.append(post) for post in posts[:count] if post not in ret]
        return ret

    def subreddit_exists(self, query: str) -> bool:
        endpoint = f'/r/{query}/about.json'
        response = self.api_requester.make_request(endpoint)
        
        if response.status_code == 200:
            return response.json().get("kind") == "t5"
        else:
            print(f'r/{query} was not found!')
            return False

    def subreddit_autocomplete(self, query: str, show_nsfw: bool) -> list[str]:
        """Used to search for subreddits after a given query"""
        """TODO: Caching"""
        endpoint = f'/api/subreddit_autocomplete'
        params = {"query": query, "include_over_17": show_nsfw,
                    "include_profiles": False}
        response = self.api_requester.make_request(
            endpoint, params
        )
        data = response.json()
        return [subreddit.get("name", "") for subreddit in data.get("subreddits", [])]

