from typing import TypeAlias, Literal
from datetime import datetime, timedelta, date
from utils import read_file, parse_text

AggrMode: TypeAlias = Literal["COMMENT", "SELFTEXT", "BOTH"]
Key: TypeAlias = str

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
        print(m)
        return m



class NestedDict:
    def __init__(self, 
            keytype: any = Key,
            valuetype: any = int
                 ):
        self.keytype = keytype
        self.valuetype = valuetype
        self.dict : dict[any, dict[any,any]] = {}


