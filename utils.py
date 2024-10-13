import re

def clean_url(url):
    match = re.search(r'(BV\w+)', url)
    if match:
        return f"https://www.bilibili.com/video/{match.group(1)}"
    return url
