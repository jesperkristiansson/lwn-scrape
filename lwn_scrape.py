import requests
import re
import time
import argparse
import html

from datetime import datetime, timedelta

#@profile
def main():
    parser = argparse.ArgumentParser(description='Scrapes all articles from lwn.net and presents them in chronological order')

    parser.add_argument('--url', default='https://lwn.net/Kernel/Index/', type=str, help='The URL to the page containing links to articles')
    parser.add_argument('--reverse', '-r', action='store_true', help='Reverse order of articles (newest first)')

    args = parser.parse_args()

    page = requests.get(args.url)

    article_multiline_regex = re.compile(r'class="IndexEntry".*\n.*<a href="(.*)/">(.*)</a> \((.*)\)</p>')
    articles = {
            (link, title, datetime.strptime(date, "%B %d, %Y").date())
            for link, title, date in article_multiline_regex.findall(page.text)}

    sorted_articles = sorted(articles, key=lambda t: t[2],reverse=args.reverse)

    def twoThursdaysAgo():
        today = datetime.today().date()
        daysSinceThursday = (today.weekday() - 3) % 7
        daysBack = daysSinceThursday + 7
        targetThursday = today - timedelta(days=daysBack)
        return targetThursday

    subscriptionCutoffDatetime = twoThursdaysAgo()
    cutoffIndex = 0
    if args.reverse:
        for i, e in list(enumerate(sorted_articles)):
            articleDate = e[2]
            if articleDate < subscriptionCutoffDatetime:
                cutoffIndex = i
                break
    else:
        for i, e in reversed(list(enumerate(sorted_articles))):
            articleDate = e[2]
            if articleDate < subscriptionCutoffDatetime:
                cutoffIndex = i + 1
                break

    preCutoffArticles = sorted_articles[:cutoffIndex]
    postCutoffArticles = sorted_articles[cutoffIndex:]

    def articleToString(article):
        link, title, date = article
        return f'{title}\nhttps://lwn.net{link}\n{date}'

    delimiter = '\n\n'

    preCutoffArticlesString = delimiter.join(articleToString(art) for art in preCutoffArticles)
    postCutoffArticlesString = delimiter.join(articleToString(art) for art in postCutoffArticles)
    estimatedCutoffString = '----------------- Estimated subscription cutoff -----------------'
    out = delimiter.join((preCutoffArticlesString, estimatedCutoffString, postCutoffArticlesString))
    out = html.unescape(out)
    print(out)
main()
