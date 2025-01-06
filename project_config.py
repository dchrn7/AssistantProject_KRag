# Imports
# Env var
import os
import sys
from dotenv import load_dotenv, find_dotenv

# Env variables
sys.path.append('../..')
_ = load_dotenv(find_dotenv())
dotenv_path = find_dotenv()

OPENAI_API_KEY = os.environ['OPENAI_API_KEY']  # Change to your space name
PATH_NAME_SPLITTER = './splitted_docs.jsonl'
PERSIST_DIRECTORY = './db/chroma/'
EVALUATION_DATASET = '../data/evaluation_dataset.tsv'
