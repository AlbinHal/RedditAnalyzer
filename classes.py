"""Classes for the RedditAnalyzer"""
from datetime import datetime, timedelta
from utils import SubRedditMode, FilePath, read_file, update_json, save_json, get_input, makedir
from requests.auth import HTTPBasicAuth
from time import sleep
from collections import Counter
from os.path import isfile
import matplotlib
from rich.console import Console
from rich import print as rprint
import matplotlib.pyplot as plt
import pandas as pd
import requests
import os
import warnings

CONFIG = "config.json"

BASE_URL = "https://oauth.reddit.com/"

CACHE_FILEPATH = "saved"

def cached_csv_exists(sub:str) -> bool:
    if sub is None:
        return False
    return os.path.isfile(f'{CACHE_FILEPATH}/{sub}.csv')

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
        self.update_token()

    def __str__(self):
        s = "ApiClient\n" + \
            f'Username: {self.__username}\n' + \
            f'Token-expires: {self.oauth_expires}'

        return s

    def get_posts_by_subreddit(self,
                               subreddit: str = "sweden",
                               subredditmode: SubRedditMode = "new",
                               count: int = 1000,
                               before: str | None = None
                               ) -> list[dict]:
        """Get posts from a subreddit of choice"""
        self.update_token()
        n = 0
        posts = []
        url = f'{BASE_URL}r/{subreddit}/{subredditmode}'
        params = {"limit": 100 if count > 100 else count}

        if before is not None:
            page_key = 'before'
            params[page_key] = before
        else:
            page_key = 'after'

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
            if params.get(page_key, "") == data['data'].get(page_key, ""):
                break
            params[page_key] = data['data'].get(page_key, {})
            self._limit_rate(response.headers)
        ret = []
        [ret.append(post) for post in posts[:count] if post not in ret]
        return ret

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

    def subreddit_exists(self, query: str) -> bool:
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
        token = resp.get("access_token")
        time_remaining = resp['expires_in']
        new_expires = datetime.today() + timedelta(seconds=time_remaining)
        # Update config.json
        updates = {"token": token, "token_expires": new_expires.isoformat()}
        update_json(CONFIG, updates)
        self.__oauth_token = token
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
    def _generate_header(self) -> dict:
        """Returns Auth header used in _get_oauth_token"""
        return {"Authorization": f'bearer {self.__oauth_token}',
                "User-Agent": self.__user_agent}

    def _limit_rate(self, header: dict) -> None:
        """Simply sleep if we are getting close to exceeding rate."""
        self.remaining = header.get("x-ratelimit-remaining", 0)
        refresh = header.get("x-ratelimit-reset", 600)
        if float(self.remaining) < 100:
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
        """Returns a DataFrame mapping each user to their posts and the number of posts."""
        grouped = self.dataset.groupby('author')['title'].apply(list).reset_index()
        grouped.columns = ['user', 'posts']
        grouped['num_posts'] = grouped['posts'].str.len()
        grouped = grouped.sort_values(by='num_posts', ascending=False).reset_index(drop=True)

        return grouped

    def submission_times_by_hour(self):
        self.dataset['hour_of_day'] = pd.to_datetime(self.dataset['created_utc'], unit='s').dt.hour
        posts_by_hour = self.dataset['hour_of_day'].value_counts().sort_index()
        return posts_by_hour

    def num_posts(self) -> int:
        return len(self.dataset)

    def vote_ratio(self):
        return self.dataset['upvote_ratio'].sort_values(ascending=False)

    def newest_timestamp(self) -> str:
        return self.dataset.loc[self.dataset['created_utc'].idxmax(), 'created_utc']

    def _clean_str(self, s: str) -> str:
        if not self.__clean_str:
            return s
        new_str = ''.join(c.lower() for c in s if c.isalpha() or c == " ")
        return new_str

    def load_dataset(self, fp: FilePath | list[dict]) -> None:
        """Loads a .csv into a Dataframe, store in Dataprocessor"""
        if type(fp) is list:
            self.dataset = pd.DataFrame(fp).sort_values(
                by="created_utc", ascending=False)
            return
        if not isfile(fp):
            # Error msg
            return None
        self.dataset = pd.read_csv(fp).sort_values(
            by="created_utc", ascending=False)

    def append_dataset(self, dataset: pd.DataFrame) -> None:
        # TODO, fix (probable) bug where we try to append an all N/A dataframe.
        # Suppress warning for now.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=FutureWarning)
            dataset = dataset.reindex(columns=self.dataset.columns)
            self.dataset = pd.concat([self.dataset, dataset], ignore_index=True).sort_values(
                by="created_utc", ascending=False)

    def store_dataset(self, dataset: pd.DataFrame | None = None, name: str = "out"):
        """Store Dataframe into .csv, if none specified, store main dataframe"""
        if dataset is None:
            self.dataset.to_csv(f'{CACHE_FILEPATH}/{name}.csv', index=False)
        else:
            dataset.to_csv(f'{CACHE_FILEPATH}/{name}.csv', index=False)

    def dataset_remove_duplicates(self):
        self.dataset.drop_duplicates()


class Visualizer():
    """Handles graph creation"""
    def __init__(self, style = 'dark_background'):
        matplotlib.use('TkAgg')
        plt.style.use(style)
        return

    def draw_histogram(self, dataset: pd.DataFrame,
                       title) -> None:
        dataset.plot(kind='hist', bins=20, title=title)

    def draw_bargraph(self, dataset: pd.DataFrame, title: str = None) -> None:
        dataset.plot(kind='bar', title=title)
        plt.show()

class CliAppManager():
    def __init__(self, ApiClient: ApiClient, DataProcessor: DataProcessor, Visualizer: Visualizer, Subreddit: str | None= None):
        self.ApiClient = ApiClient
        self.DataProcessor = DataProcessor
        self.Visualizer = Visualizer
        self.Parameters = Parameters(Subreddit)
        self.Cli = Console()


    def run(self):
        self._load_subreddit()    
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
        rprint(
            f'Number of posts fetched: [bold blue]{self.DataProcessor.num_posts()}')
        rprint("Most active users:")
        rprint(self.DataProcessor.posts_by_users())
        self.Visualizer.draw_bargraph(
            self.DataProcessor.submission_times_by_hour(), "Submission times by hour")
        self._hold()

    def _change_subreddit(self):
        self.Parameters.subreddit = get_input("Enter subreddit")
        self._load_subreddit()

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
        rprint(f'Current Subreddit: r/[{sub_color}]{self.Parameters.subreddit}')

    def _load_subreddit(self):
         with self.Cli.status("Fetching posts..."):
            if cached_csv_exists(self.Parameters.subreddit):
                self.DataProcessor.load_dataset(f'{CACHE_FILEPATH}/{self.Parameters.subreddit}.csv')
            else:
                data = self.ApiClient.get_posts_by_subreddit(
                    subreddit=self.Parameters.subreddit)
                self.DataProcessor.load_dataset(data)
    def _hold(self) -> None:
        input("Press ENTER to continue")


class CacheAppManager():
    def __init__(self, ApiClient: ApiClient, DataProcessor: DataProcessor, subreddits: list[str]):
        self.ApiClient = ApiClient
        self.DataProcessor = DataProcessor
        self.subreddits = subreddits

    def run(self) -> None:
        makedir(CACHE_FILEPATH)
        count_gen = self._count_gen()
        self._check_subreddits_valid()
        for sub in [sub for sub in self.subreddits if sub not in self._get_cached()]:
            self._cache_initial(sub)
        latest = {}
        for sub in self.subreddits:
            self.DataProcessor.load_dataset(f'{CACHE_FILEPATH}/{sub}.csv')
            latest[sub] = self.DataProcessor.newest_timestamp()
        while True:
            print(datetime.now())
            max: int = 0
            count: int = next(count_gen)
            for sub, latest_timestamp in latest.items():
                newer = []
                data: list[dict] = self.ApiClient.get_posts_by_subreddit(
                    sub, count=count)
                for post in data:
                    if post['created_utc'] > latest_timestamp:
                        newer.append(post)
                if len(newer) > 0:
                    # TODO, optimize this!!
                    print(
                        f'\n{sub}: {[post.get("title", "") for post in newer]}\n')
                    self.DataProcessor.load_dataset(
                        f'{CACHE_FILEPATH}/{sub}.csv')
                    self.DataProcessor.append_dataset(pd.DataFrame(newer))
                    self.DataProcessor.store_dataset(name=sub)
                    latest[sub] = newer[0]['created_utc']
                max = len(newer) if len(newer) > max else max
                print(f'Fetched {len(newer)} newer posts from r/{sub}')
            print(f'----------')
            sleep(300)  # Sleep for 5 minutes
        print("Done")

    def _cache_initial(self, subreddit: str) -> None:
        print(f'Caching r/{subreddit}...')
        data = self.ApiClient.get_posts_by_subreddit(
            subreddit=subreddit, count=1000)
        self.DataProcessor.load_dataset(data)
        self.DataProcessor.store_dataset(name=subreddit)

    def _check_subreddits_valid(self) -> None:
        print("Checking subreddit validity...")
        new = [subreddit for subreddit in
               self.subreddits if self.ApiClient.subreddit_exists(subreddit)]

    def _get_cached(self) -> list[str]:
        """Lists subreddits that have an entry in CACHE_FILEPATH"""
        """Files need to conform to the naming convention of <SUBREDDIT>.csv"""
        cached = [file.split(".")[0] for file in os.listdir(CACHE_FILEPATH)]
        return cached

    def _count_gen(self):
        count = 0
        while True:
            yield 1000 if count < 1 else 20
            count += 1


class Parameters():
    def __init__(self, subreddit: str | None = None):
        self.subreddit = subreddit
