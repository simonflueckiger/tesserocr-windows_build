import urllib.request
import json
import os
import sys

repo = sys.argv[1]

url = "https://api.github.com/repos/{}/releases/latest".format(repo)
with urllib.request.urlopen(url) as url:
    data = json.loads(url.read().decode())
    sys.stdout.write(data['name'])