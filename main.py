import argparse
import logging
from api import DataService
from classes import DataProcessor, Visualizer
from appmanager import CliAppManager
from cacheappmanager import CacheAppManager

# FLAGS
VERBOSE = True
GUI = False

def print_usage():
    ...

def setup_logger(name: str = __name__) -> logging.Logger:
    logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logging.root.setLevel(logging.INFO)
    return logging.getLogger(name)

def main():
    """Parse arguments and launch correct Manager class"""
    ac = DataService()
    dp = DataProcessor()
    vi = Visualizer('dark_background')
    parser = argparse.ArgumentParser()

    parser.add_argument("--cachemode", nargs='*',help="Have redditanalyzer continously run and save posts")
    parser.add_argument("--sub", type=str, help="This subreddit will be fetched on startup")
    args = parser.parse_args()
    if args.cachemode is not None:
        app = CacheAppManager(ac, dp, args.cachemode)
    elif args.sub is not None:
        app = CliAppManager(ac,dp,vi, args.sub)
    else:
        app = CliAppManager(ac,dp,vi)
    app.run()

    #vs = Visualizer('dark_background')
    #app = CliAppManager(ApiClient=ac, DataProcessor=dp, Visualizer=vs)
    #app.run()


if __name__ == "__main__":
    main()