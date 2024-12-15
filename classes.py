from typing import TypeAlias, Literal
from datetime import datetime, timedelta, date
from utils import read_file, parse_text, update_json, limit_rate
from requests.auth import HTTPBasicAuth
from requests.compat import urljoin
import requests
import json
import time

CONFIG = "config.json"
AggrMode: TypeAlias = Literal["COMMENT", "SELFTEXT", "BOTH"]
SubRedditMode : TypeAlias = Literal["old", "new", "hot"]
Key: TypeAlias = str

BASE_URL = "https://oauth.reddit.com/"

class Aggregator:
    def __init__(self, 
                 Interval: int = 1000,
                 Mode: AggrMode = "SELFTEXT",
                 Subreddit: str | None = None,
                 Start: datetime = date.today() - timedelta(30),
                 Debug: bool = False,
                 DebugPaths: list[str] | None = None
                 ):
        self.Interval = Interval
        self.Mode = Mode
        self.Subreddit = Subreddit
        self.Start = Start
        self.Debug = Debug
        self.DebugPaths = DebugPaths
        self.client = ApiClient()

        self.map = self.crawl()

    def __str__(self):
        print(f'Aggregator\nMode: {self.Mode}\nSubreddit: {self.Subreddit}\nStart: {self.Start}\nEnd: {self.End}')

    def crawl(self):
        completed = False
        count = 0
        after = None
        m : dict[Key,int] = {}
        words = []
        while not completed:
            response = self.client.subreddit(subreddit=self.Subreddit, limit=100, count=count, after=after)
            after = response.json()['data']['after']
            for post in response.json()['data']['children']:
                count += 1
                date = datetime.fromtimestamp(post['data']['created'])
                if date <  self.Start or count > 1000:
                    completed = True
                    break
                words.extend(parse_text(post['data']['title'] + post['data']['selftext']))
            for word in words:
                m[word] = m.get(word,0) + 1
            time.sleep(limit_rate(response.headers))
        return m



class NestedDict:
    def __init__(self, 
            keytype: any = Key,
            valuetype: any = int
                 ):
        self.keytype = keytype
        self.valuetype = valuetype
        self.dict : dict[any, dict[any,any]] = {}


class ApiClient():
    def __init__(self):
        self.cfg = read_file(CONFIG)
        self.__user_agent = self.cfg['user_agent'] 
        self.__username = self.cfg['username']
        self.__password = self.cfg['password'] 
        self.__client_id = self.cfg['client_id'] 
        self.__client_secret = self.cfg['client_secret'] 
        self.oauth_token = self.cfg['token']
        self.oauth_expires = datetime.fromisoformat(self.cfg['token_expires'])
        self.latest = None
    
    def subreddit(self, 
                  subreddit: str = "sweden",
                  subredditmode: SubRedditMode = "new",
                  limit: int = 10,
                  count: int = 0,
                  after: str | None = None
                  ):
        url = f'{BASE_URL}r/{subreddit}/{subredditmode}'
        params = {"limit":limit, "count":count}
        if after is not None:
            params["after"] = after
        response = requests.get(url, headers = self._generate_header() , params=params)
        if response.status_code != 200:
            print(f'ApiClient.subreddit: Received {response.status_code}')
            return response
        self.latest = response
        return self.latest
        

    # OAUTH TOKENS
    def _update_token(self):
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
        self.oauth_token = token
        self.oauth_expires = new_expires

    def _get_oauth_token(self):
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
    def _generate_header(self):
        return {"Authorization": f'bearer {self.oauth_token}',"User-Agent" : self.__user_agent}

""" class Post(raw):
    def __init__(self):
         """