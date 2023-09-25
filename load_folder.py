import os
import redis
import re

r = redis.Redis(host='localhost', port=6379, db=0)

def load_folder(path):
    files = os.listdir(path)
    print(files)
    for file in files:
        match = re.match(r'^book(\d+).html$', file)
        if match:
            with open(os.path.join(path, file), 'r', encoding='utf-8') as f:
                html_content = f.read()
                book_id = match.group(1)
                r.set(f"book_{book_id}", html_content)
                print(f"Loaded book_{book_id} into Redis")

load_folder('html/books/')
