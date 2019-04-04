import CachedTodoQueries
import numpy as np
import pandas as pd
from shutil import copyfile
import datetime
import pickle

session = CachedTodoQueries.authorize()
ids = CachedTodoQueries.query_todos(session)
# Run this, but discard metadata after, to force cache file to update
msgs = CachedTodoQueries.fetch_metadata(session, ids)

# Copy and timestamp metadata cache
copyfile('messagecache.pkl', 'messagecache-archive-{}.pkl'.format(datetime.datetime.now().strftime('%Y%m%d-%H%M%S')))

# Pickle and timestamp list of ids
with open('todo-query-archive-{}.pkl'.format(datetime.datetime.now().strftime('%Y%m%d-%H%M%S')), 'w+b') as cachefile:
    pickle.dump(ids, cachefile)