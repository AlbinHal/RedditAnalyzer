from rich.console import Console
from rich import print as rprint
from rich.columns import Columns
from rich.panel import Panel
from utils import get_input, cached_csv_exists
from api import DataService
from classes import DataProcessor, Visualizer
from collections import Counter

CACHE_FILEPATH = "saved"
SCOLOR = "yellow"

class CliAppManager():
    def __init__(self, DataService: DataService, Dataprocessor: DataProcessor, Visualizer: Visualizer, Subreddit: str = "python"):
        self.ApiClient = DataService
        self.dp = Dataprocessor
        self.Visualizer = Visualizer
        self.Parameters = Parameters(Subreddit)
        self.Cli = Console()


    def run(self):
        if self.Parameters.subreddit:
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
                case "4" :
                    rprint("Goodbye")
                    break
                case _: rprint("Input Error")
        return

    def _display_stats(self):
        self.Cli.clear()
        self.Cli.rule("[bold red]RedditAnalyzer")
        self.Cli.print(f'[yellow]/r/[bold green]{self.Parameters.subreddit}', justify="center")
        rprint(
            f'Fetched [b][cyan]{self.dp.num_posts()}[/b][white] posts from {self.dp.unique_authors()} unique users')
        self.Cli.print(f'[b][green]Averages:')
        self.Cli.print(f'Number of posts per user: [b][{SCOLOR}]{self.dp.avg_posts_per_user():.2f} ', end="")
        self.Cli.print(f'Number of upvotes: [b][{SCOLOR}]: {self.dp.avg_num_upvotes()}')
        self.Cli.print(f'Title length: [b][{SCOLOR}]: {self.dp.avg_title_length()} ', end="")
        self.Cli.print(f'Post length: [b][{SCOLOR}]: {self.dp.avg_post_length()}')
        self.Visualizer.draw_wordcloud(self.dp.word_cloud("title"), "Most Common Words in Titles")
        self.Visualizer.draw_wordcloud(self.dp.word_cloud("selftext"), "Most Common Words in Posts")
        self.Visualizer.draw_bargraph(
            self.dp.submission_times_by_hour(), "Submission times by hour")
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
        with self.Cli.status(f'Fetching posts from r/{self.Parameters.subreddit}...'):
            if cached_csv_exists(self.Parameters.subreddit):
                print("it exists")
                self.dp.load_dataset_from_file(f'{CACHE_FILEPATH}/{self.Parameters.subreddit}.csv')
            else:
                data = self.ApiClient.get_posts_by_subreddit(
                    subreddit=self.Parameters.subreddit)
                self.dp.store_dataset(data, self.Parameters.subreddit)

    def _hold(self) -> None:
        input("Press ENTER to continue")

    def cprint(self, *args) -> None:
        self.cli.print(args)


class Parameters():
    def __init__(self, subreddit: str | None = None):
        self.subreddit = subreddit
