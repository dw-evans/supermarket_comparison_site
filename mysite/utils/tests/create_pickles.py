from utils.query import to_pickle
from utils.main import *
from utils.query import *

from pathlib import Path

search_term = "oats"

b = WaitroseRequest(query=search_term, max_items=10)

path2 = Path(__file__).parent / "pickles/waitrose.pkl"

to_pickle(b, path2)
