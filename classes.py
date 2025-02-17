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
from wordcloud import WordCloud

import matplotlib.pyplot as plt
import pandas as pd
import requests
import os
import warnings

BASE_URL = "https://oauth.reddit.com/"

CACHE_FILEPATH = "saved"

def cached_csv_exists(sub:str) -> bool:
    if sub is None:
        return False
    return os.path.isfile(f'{CACHE_FILEPATH}/{sub}.csv')


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

    def word_count(self, n : int | None = None) -> pd.DataFrame:
        words = []
        for _, post in self.dataset.iterrows():
            title = post['title']
            selftext = post['selftext']
            words.extend(self._clean_str(title).split())
            words.extend(self._clean_str(selftext).split())
        wc = Counter(words)
        if n is None:
            n = len(wc)
        return pd.DataFrame(wc.items(), columns=["Word", "Count"]).sort_values(by="Count", ascending=False)

    def avg_posts_per_user(self) -> float:
        return self.dataset["author"].value_counts().mean()

    def submission_times_by_hour(self):
        self.dataset['hour_of_day'] = pd.to_datetime(self.dataset['created_utc'], unit='s').dt.hour
        posts_by_hour = self.dataset['hour_of_day'].value_counts().sort_index()
        return posts_by_hour
    
    def word_cloud(self, key:str) -> WordCloud:
        words = " ".join(self.dataset[key]).lower().split()
        word_counts = Counter(words)
        wordcloud = WordCloud(width=800, height=400, background_color="black").generate_from_frequencies(word_counts)
        return wordcloud

    def num_posts(self) -> int:
        return len(self.dataset)

    def avg_vote_ratio(self) -> float:
        return self.dataset['upvote_ratio'].mean()
    
    def avg_num_upvotes(self) -> float:
        return self.dataset['ups'].mean()
    
    def avg_title_length(self) -> float:
        return self.dataset["title"].apply(lambda x: len(x.split())).mean()

    def avg_post_length(self) -> float: 
        return self.dataset["selftext"].apply(lambda x: len(x.split())).mean()

    def unique_authors(self) -> int:
        return self.dataset["author"].nunique()

    def newest_timestamp(self) -> str:
        return self.dataset.loc[self.dataset['created_utc'].idxmax(), 'created_utc']

    def _clean_str(self, s: str) -> str:
        if not self.__clean_str:
            return s
        new_str = ''.join(c.lower() for c in s if c.isalpha() or c == " ")
        return new_str

    def load_dataset_from_list(self, fp: FilePath | list[dict]) -> bool:
        """Loads a .csv into a Dataframe, store in Dataprocessor"""
        try:
            self.dataset = pd.DataFrame(fp).sort_values(
            by="created_utc", ascending=False)
            return True
        except:
            return False
        
    def load_dataset_from_file(self, fp: FilePath) -> bool:
        if not isfile(fp):
            return False
        try:
            self.dataset = pd.read_csv(fp).sort_values(
                by="created_utc", ascending=False
            )
            return True
        except:
            return False


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
            self.load_dataset_from_list(dataset)
            self.dataset.to_csv(f'{CACHE_FILEPATH}/{name}.csv', index=False)

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

    def draw_wordcloud(self, wc: WordCloud, title: str) -> None:
        plt.figure(figsize=(10,5))
        plt.imshow(wc, interpolation="bilinear")
        plt.axis("off")
        plt.title(title)
        plt.show()
