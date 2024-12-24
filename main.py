import argparse
import logging
from classes import ApiClient, DataProcessor, Visualizer, CliAppManager, CacheAppManager

# FLAGS
VERBOSE = True
GUI = False

# PARAMETERS
USER_AGENT = "RdtTrends/1.0 (Linux;Python/3.13) (by /u/SpktLaban)"
RESPONSE_FILE = "response.txt"



def print_usage():
    ...

def setup_logger(name: str = __name__) -> logging.Logger:
    logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logging.root.setLevel(logging.INFO)
    return logging.getLogger(name)

def main():
    """Parse arguments and launch correct Manager class"""
    ac = ApiClient()
    dp = DataProcessor()
    log = setup_logger("main")
    parser = argparse.ArgumentParser()

    parser.add_argument("--cachemode", nargs='*',help="Have redditanalyzer continously run and save posts")
    args = parser.parse_args()
    if args.cachemode is not None:
        app = CacheAppManager(ac, dp, args.cachemode)
        app.run()

    #vs = Visualizer('dark_background')
    #app = CliAppManager(ApiClient=ac, DataProcessor=dp, Visualizer=vs)
    #app.run()


if __name__ == "__main__":
    main()