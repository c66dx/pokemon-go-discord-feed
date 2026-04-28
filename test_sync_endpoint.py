#!/usr/bin/env python
"""Test the sync endpoint via POST request."""
import subprocess
import sys
import time

# Wait for server to start
time.sleep(4)

# Use the system python to make a POST request
test_code = """
import urllib.request
import json
url = 'http://localhost:8000/sync-feeds'
req = urllib.request.Request(url, method='POST')
try:
    with urllib.request.urlopen(req, timeout=30) as response:
        print(response.read().decode())
except Exception as e:
    print(f'Error: {e}')
"""

subprocess.run([sys.executable, '-c', test_code])
