"""Classes for the RedditAnalyzer"""
from datetime import datetime, timedelta
from utils import SubRedditMode, FilePath, read_file, update_json, save_json, get_input, makedir
from requests.auth import HTTPBasicAuth
from time import sleep
from collections import Counter
from os.path import isfile
from matplotlib import style
from rich.console import Console
from rich import print as rprint
import matplotlib.pyplot as plt
import pandas as pd
import requests
import os

CONFIG = "config.json"

BASE_URL = "https://oauth.reddit.com/"

CACHE_FILEPATH = "saved"


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
        self.rate_remaining = 1000
        self.update_token

    def __str__(self):
        s = "ApiClient\n" + \
            f'Username: {self.__username}\n' + \
            f'Token-expires: {self.oauth_expires}'

        return s

    def get_posts_by_subreddit(self,
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
        return posts[:count + 1]
    
    def subreddit_autocomplete(self, query: str, show_nsfw: bool) -> list[str]:
        """Used to search for subreddits after a given query"""
        url = f'{BASE_URL}/api/subreddit_autocomplete'
        params = {"query": query, "include_over_18": show_nsfw,
                  "include_profiles": False}
        response = requests.get(url, headers=self._generate_header(),
                                params=params)
        data = response.json()
        save_json(data, f'searches/{query}_subr_search.json') 
        return [subreddit.get("name", "") for subreddit in data.get("subreddits", [])]
        
    def subreddit_exists(self, query:str) -> bool:
        self.update_token()
        url = f'{BASE_URL}/r/{query}/about.json'
        response = requests.get(url=url, headers=self._generate_header()) 
        data = response.json()
        if response.status_code == 200:
            return data.get("kind") == "t5"
        else:
            return False
    # OAUTH TOKENS
    def update_token(self) -> None:
        """Checks if the oauth token has expired and updates it accordingly."""
        if self.oauth_expires - timedelta(hours=1) > datetime.today():
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
        return  

    # HELPER METHODS
    def _generate_header(self) -> dict:
        """Returns Auth header used in _get_oauth_token"""
        return {"Authorization": f'bearer {self.__oauth_token}',
                "User-Agent": self.__user_agent}

    def _limit_rate(self, header: dict | None = None) -> None:
        """Simply sleep if we are getting close to exceeding rate."""
        self._remaining = header.get("x-ratelimit-remaining", 0)
        refresh = header.get("x-ratelimit-reset", 600)
        if float(remaining) < 100:
            sleep(1)
        return


class DataProcessor():
    def __init__(self, clean_str: bool = True, dataset: list[dict] | FilePath | None = None):
        self.__clean_str: str = clean_str
        if type(dataset) is FilePath:
            self.dataset = self.load_dataset(dataset)
        elif type(dataset) is list[dict]:
            self.dataset = pd.DataFrame(dataset)
        else: 
            self.dataset = []

    def __str__(self):

        ...

    def word_count(self) -> pd.DataFrame:
        words = []
        for _, post in self.dataset.iterrows():
            title = post['title']
            selftext = post['selftext']
            words.extend(self._clean_str(title).split())
            words.extend(self._clean_str(selftext).split())
        wc = Counter(words)
        return pd.DataFrame(wc.items(), columns=["Word", "Count"]).sort_values(by="Count", ascending=False)

    def posts_by_users(self) -> pd.DataFrame:
        users: dict[str, list[str]]
        for _,post in self.dataset.iterrows():
            user = post['author']
            if user not in users:
                users[user] = []
            users[users].append(user)
        uc_df = pd.DataFrame(users, columns=["User", "Posts"])

    
    def num_posts(self) -> int:
        return len(self.dataset)
    
    def vote_ratio(self) -> float:
        self.dataset['vote_ratio'] = self.dataset['ups'] / (self.dataset['downs'] + 1)
        return self.dataset['vote_ratio'].sort_values(ascending=False)

    def newest_id(self) -> str:
        return self.dataset.loc[self.dataset['created_utc'].idxmax(), 'id']

    def _clean_str(self, s: str) -> str:
        if not self.__clean_str:
            return s
        new_str = ''.join(c.lower() for c in s if c.isalpha() or c == " ")
        return new_str

    def load_dataset(self, fp: FilePath | list[dict]) -> None:
        """Loads a .csv into a Dataframe, store in Dataprocessor"""
        if type(fp) is list:
            self.dataset = pd.DataFrame(fp).sort_values(by="created_utc", ascending=False)
            return
        if not isfile(fp):
            # Error msg
            return None
        self.dataset = pd.read_csv(fp).sort_values(by="created_utc", ascending=False)

    def store_dataset(self, dataset: pd.DataFrame | None = None, name: str = "out"):
        """Store Dataframe into .csv, if none specified, store main dataframe"""
        if dataset is None:
            self.dataset.to_csv(f'{CACHE_FILEPATH}/{name}.csv', index=False)
        else:
            dataset.to_csv(f'{CACHE_FILEPATH}/{name}.csv', index=False)


class Visualizer():
    """Handles graph creation"""
    def __init__(self, style):
        plt.style.use(style)
        return

    def draw_histogram(self, dataset: pd.DataFrame,
                       title, key: str = 'num_comments') -> None:
        dataset[key].plot(kind='hist', bins=20, title=title)
        plt.savefig(f'aita.png')


class CliAppManager():
    def __init__(self, ApiClient : ApiClient, DataProcessor : DataProcessor, Visualizer: Visualizer):
        self.ApiClient = ApiClient
        self.DataProcessor = DataProcessor
        self.Visualizer = Visualizer
        self.Parameters = Parameters()
        self.Cli = Console()

    def run(self):
        while True:
            self._draw_main_menu()
            match get_input():
                case "1":
                    self._change_subreddit()
                case "2":
                    self._search_subreddits()
                case "3":
                    self._display_stats()
                case "4":
                    rprint("Goodbye")
                    break
                case _: rprint("Input Error")
        return
    def _display_stats(self):
        self.Cli.clear()
        self.Cli.rule("[bold red]RedditAnalyzer")
        rprint(f'[yellow]/r/[bold blue]{self.Parameters.subreddit} ', end="")
        rprint(f'Number of posts fetched: [bold blue]{self.DataProcessor.num_posts()}')
        self._hold()
    def _change_subreddit(self):
        self.Parameters.subreddit = get_input("Enter subreddit")
        with self.Cli.status("Fetching posts..."):
            data = self.ApiClient.get_posts_by_subreddit(subreddit=self.Parameters.subreddit) 
        self.DataProcessor.load_dataset(data)

    def _search_subreddits(self):
        self.Cli.clear()
        self.Cli.rule("[bold red]Search Subreddits")
        rprint("Enter query")
        s = get_input()
        with self.Cli.status("Searching..."):
            subs = self.ApiClient.subreddit_autocomplete(s, True)
        rprint(subs)
        self._hold()


    def _draw_main_menu(self):
        self.Cli.clear()
        self.Cli.rule("[bold orange]RedditAnalyzer")
        self._draw_params()
        rprint("1. Change subreddit")
        rprint("2. Search Subreddits")
        rprint("3. Display subreddit stats")
        rprint("4. Exit")

    def _draw_params(self):
        sub_color = "bold red" if self.Parameters.subreddit is None else "bold blue"
        rprint(f'Current Subreddit: [{sub_color}]{self.Parameters.subreddit}' )


    def _hold(self) -> None:
        input("Press ENTER to continue")

class CacheAppManager():
    def __init__(self, ApiClient: ApiClient, DataProcessor: DataProcessor, subreddits:list[str]):
        self.ApiClient = ApiClient
        self.DataProcessor = DataProcessor
        self.subreddits = subreddits 

    def run(self) -> None:
        makedir(CACHE_FILEPATH)
        self._check_subreddits_valid()
        for sub in [sub for sub in self.subreddits if sub not in self._get_cached()]:
            self._cache_initial(sub)
        latest = {}
        for sub in self.subreddits:
           self.DataProcessor.load_dataset(f'{CACHE_FILEPATH}/{sub}.csv')
           latest[sub] = self.DataProcessor.newest_id()
        print(latest)
        print("Done")

    def _cache_initial(self, subreddit:str) -> None:
        print(f'Caching {subreddit}...')
        data = self.ApiClient.get_posts_by_subreddit(subreddit=subreddit, count=1000)
        self.DataProcessor.load_dataset(data)
        self.DataProcessor.store_dataset(name = subreddit)

    def _check_subreddits_valid(self) -> None:
        print("Checking subreddit validity...")
        new = [subreddit for subreddit in 
                           self.subreddits if self.ApiClient.subreddit_exists(subreddit)]

    def _get_cached(self) -> list[str]:
        """Lists subreddits that have an entry in CACHE_FILEPATH"""
        cached = [file.split(".")[0] for file in os.listdir(CACHE_FILEPATH)]
        return cached
class Parameters():
    def __init__(self, subreddit: str | None = None):
        self.subreddit = subreddit