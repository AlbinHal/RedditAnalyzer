"""Classes for the RedditAnalyzer"""
from typing import TypeAlias, Literal
from datetime import datetime, timedelta
from utils import read_file, update_json
from requests.auth import HTTPBasicAuth
from time import sleep
from collections import Counter
import pandas as pd
import requests

CONFIG = "config.json"
SubRedditMode: TypeAlias = Literal["old", "new", "hot"]
FilePath: TypeAlias = str
Key: TypeAlias = str

BASE_URL = "https://oauth.reddit.com/"


class ApiClient():
    """Responsible for interacting with the API, updating auth tokens."""

    def __init__(self):
        cfg: dict = read_file(CONFIG)
        self.__user_agent = cfg['user_agent']
        self.__username = cfg['username']
        self.__password = cfg['password']
        self.__client_id = cfg['client_id']
        self.__client_secret = cfg['client_secret']
        self.__oauth_token = cfg['token']
        self.oauth_expires = datetime.fromisoformat(cfg['token_expires'])

    def __str__(self):
        s = "ApiClient\n" + \
            f'Username: {self.__username}\n' + \
            f'Token-expires: {self.oauth_expires}'

        return s

    def subreddit(self,
                  subreddit: str = "sweden",
                  subredditmode: SubRedditMode = "new",
                  count: int = 1000,
                  ) -> list[dict]:
        """Get posts from a subreddit of choice"""
        n = 0
        posts = []
        url = f'{BASE_URL}r/{subreddit}/{subredditmode}'
        params = {"limit": 100 if count > 100 else count}
        self.update_token()
        while n < count:
            response = requests.get(
                url, headers=self._generate_header(), params=params)
            if response.status_code != 200:
                print(f'ApiClient.subreddit: Received {response.status_code}')
                return posts
            data = response.json()
            posts.extend([post["data"] for post in
                          data.get("data", {}).get("children", [])])
            n += len(posts) - n
            params['after'] = data['data'].get("after", {})
            self._limit_rate(response.headers)
        print(n)
        return posts[:count-1]

    # OAUTH TOKENS
    def update_token(self) -> None:
        """Checks if the oauth token has expired and updates it accordingly."""
        if self.oauth_expires - timedelta(hours=1) > datetime.today():
            print("No need to update token")
            return
        resp = self._get_oauth_token()
        token = resp['access_token']
        time_remaining = resp['expires_in']
        new_expires = datetime.today() + timedelta(seconds=time_remaining)
        # Update config.json
        updates = {"token": token, "token_expires": new_expires.isoformat()}
        update_json(CONFIG, updates)
        self.__oauth_token = token
        self.oauth_expires = new_expires

    def _get_oauth_token(self) -> None:
        """Requests oauth0 token from /api/v1/access-token"""
        auth = HTTPBasicAuth(self.__client_id, self.__client_secret)
        data = {
            "grant_type": "password",
            "username": self.__username,
            "password": self.__password
        }
        headers = {"User-Agent": self.__user_agent}
        response = requests.post(
            "https://ssl.reddit.com/api/v1/access_token",
            auth=auth,
            data=data,
            headers=headers
        )
        return response.json()

    # HELPER METHODS
    def _generate_header(self) -> dict:
        """Returns Auth header used in _get_oauth_token"""
        return {"Authorization": f'bearer {self.__oauth_token}',
                "User-Agent": self.__user_agent}

    def _limit_rate(self, header: dict) -> None:
        """Simply sleep if we are getting close to exceeding rate."""
        remaining = header.get("x-ratelimit-remaining", 0)
        if float(remaining) < 100:
            sleep(1)
        return


class DataProcessor():
    def __init__(self, clean_str: bool = True, dataset: list[dict] | FilePath = []):
        self.__clean_str: str = clean_str
        if type(dataset) is FilePath:
            self.dataset = self.load_dataset(dataset)
        else:
            self.dataset = pd.DataFrame(dataset)

    def __str__(self):

        ...

    def word_count(self, dataset: list[dict]) -> pd.DataFrame:
        words = []
        for post in dataset:
            title = post.get("title", "")
            selftext = post.get("selftext", "")
            words.extend(self.clean_str(title).split())
            words.extend(self.clean_str(selftext).split())
        wc = Counter(words)
        return pd.DataFrame(wc.items(), columns=["Word", "Count"]).sort_values(by="Count", ascending=False)

    def num_posts(self) -> int:
        return len(self.dataset)

    def vote_ratio(self, dataset: list[dict] | FilePath) -> float:
        data = pd.DataFrame(dataset)
        data['vote_ratio'] = data['ups'] / (data['downs'] + 1)
        return data['vote_ratio'].sort_values(ascending=False)

    def clean_str(self, s: str) -> str:
        if not self.__clean_str:
            return s
        new_str = ''.join(c.lower() for c in s if c.isalpha() or c == " ")
        return new_str

    def load_dataset(self, fp: FilePath):
        return pd.read_csv(fp)

    def store_dataset(self, name: str = "out"):
        self.dataset.to_csv(f'{name}.csv', index=False)


class Visualizer():
    """Handles graph creation"""

    def __init__(self):
        ...


class AppManager():
    def __init__(self, ApiClient, DataProcessor, Visualizer):
        ...
