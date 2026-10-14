# このファイルの役割：画面内のリンク・表示部品・JavaScript設定をテストから読み取ります。

import json
import re
from html.parser import HTMLParser


class Elements(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.elements = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


def hydro_js_config(html):
    match = re.search(r"window.HYDROPONICS_CONFIG = (.*?);", html)
    return json.loads(match.group(1))
