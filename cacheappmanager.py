
import datetime
import pandas as pd
from time import sleep
import os
from api import DataService
from classes import DataProcessor
from utils import makedir

CACHE_FILEPATH = "saved"

class CacheAppManager():
    def __init__(self, DataService : DataService, DataProcessor: DataProcessor, subreddits: list[str]):
        self.ApiClient = DataService 
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
            self.DataProcessor.load_dataset_from_file(f'{CACHE_FILEPATH}/{sub}.csv')
            latest[sub] = self.DataProcessor.newest_timestamp()
        while True:
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
                    self.DataProcessor.load_dataset_from_file(
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
        self.DataProcessor.load_dataset_from_list(data)
        self.DataProcessor.store_dataset(name=subreddit)

    def _check_subreddits_valid(self):
        print("Checking subreddit validity...")
        new = [subreddit for subreddit in
               self.subreddits if self.ApiClient.subreddit_exists(subreddit)]
        self.subreddits = new
        
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
