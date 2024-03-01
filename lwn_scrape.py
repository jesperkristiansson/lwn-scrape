import requests
import sys
import re
import time

#@profile
def main():
    URL = 'https://lwn.net/Kernel/Index/'

    if len(sys.argv) > 1:
        URL = sys.argv[1]

    page = requests.get(URL)

    lines = page.text.split('\n')

    article_multiline_regex = re.compile(r'class="IndexEntry".*\n.*<a href="(.*)/">(.*)</a> \((.*)\)</p>')
    articles = set(re.findall(article_multiline_regex, page.text))


    sorted_articles = sorted(articles, key=lambda t: int(t[0][10:]),reverse=True)
    article_string_generator = (f'{title}\nhttps://lwn.net{link}\n{date}' for link, title, date in sorted_articles)
    print('\n\n'.join(article_string_generator))
main()