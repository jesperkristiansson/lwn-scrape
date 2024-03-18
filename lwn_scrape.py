import requests
import re
import time
import argparse

#@profile
def main():
    parser = argparse.ArgumentParser(description='Scrapes all articles from lwn.net and presents them in chronological order')

    parser.add_argument('--url', default='https://lwn.net/Kernel/Index/', type=str, help='The URL to the page containing links to articles')
    parser.add_argument('--reverse', '-r', action='store_true', help='Reverse order of articles (newest first)')

    args = parser.parse_args()

    page = requests.get(args.url)

    lines = page.text.split('\n')

    article_multiline_regex = re.compile(r'class="IndexEntry".*\n.*<a href="(.*)/">(.*)</a> \((.*)\)</p>')
    articles = set(re.findall(article_multiline_regex, page.text))

    sorted_articles = sorted(articles, key=lambda t: int(t[0][10:]),reverse=args.reverse)
    article_string_generator = (f'{title}\nhttps://lwn.net{link}\n{date}' for link, title, date in sorted_articles)
    print('\n\n'.join(article_string_generator))
main()
