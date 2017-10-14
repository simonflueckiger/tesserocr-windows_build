import urllib.request
import json
import os
import sys
with urllib.request.urlopen("https://api.github.com/repos/sirfz/tesserocr/releases/latest") as url:
    data = json.loads(url.read().decode())
    # os.environ['BUILD_NAME'] = data['name']
    sys.stdout.write(data['name'])