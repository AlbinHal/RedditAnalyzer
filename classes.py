from typing import TypeAlias, Literal
from datetime import datetime, timedelta, date
from utils import read_file, parse_text
from requests.auth import HTTPBasicAuth
from requests.compat import urljoin
import requests
import config 

AggrMode: TypeAlias = Literal["COMMENT", "SELFTEXT", "BOTH"]
SubRedditMode : TypeAlias = Literal["old", "new", "hot"]
Key: TypeAlias = str

BASE_URL = "https://oauth.reddit.com/"

class Aggregator:
    def __init__(self, 
                 Interval: int = 1000,
                 Mode: AggrMode = "SELFTEXT",
                 Subreddit: str | None = None,
                 Start: datetime | None = date.today() - timedelta(30),
                 End: datetime | None = date.today(),
                 Debug: bool = False,
                 DebugPaths: list[str] | None = None
                 ):
        self.Interval = Interval
        self.Mode = Mode
        self.Subreddit = Subreddit
        self.Start = Start
        self.Debug = Debug
        self.DebugPaths = DebugPaths
        self.map = self.crawl()

    def __str__(self):
        print(f'Aggregator\nMode: {self.Mode}\nSubreddit: {self.Subreddit}\nStart: {self.Start}\nEnd: {self.End}')

    def crawl(self):
        #map : NestedDict = NestedDict(Key, int)
        m : dict[Key,int] = {}
        if self.Debug:
            words = []
            for response in map(read_file ,self.DebugPaths):
                words.extend([parse_text(text['data']['selftext']) 
                         for text in response['data']['children']])
            for word in [i for row in words for i in row]:
                m[word] = m.get(word,0) + 1
            
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
    def __init__(self, oauth_token = None):
        self.__user_agent = config.USER_AGENT
        self.__username = config.USERNAME
        self.__password = config.PASSWORD
        self.__client_id = config.CLIENT_ID
        self.__client_secret = config.CLIENT_SECRET
        if oauth_token is None:
            self.oauth_token = self._get_oauth_token() 

    def subreddit(self, 
                  subreddit: str = "sweden",
                  subredditmode: SubRedditMode = "new"
                  ):
        url = f'{BASE_URL}/r/{subreddit}/{subredditmode}'
        print(url)


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
        return response.json()["access_token"]
