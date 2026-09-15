import requests
import re
import time
import argparse
import html

from datetime import datetime, timedelta

def isRead(readArticlesNumbers, article):
    articleLink = article[0]
    lastSlashIndex = articleLink.rfind('/')
    if lastSlashIndex == -1:
        print(f'Error: could not find article number in {articleLink}')
        return False

    articleNumber = int(articleLink[lastSlashIndex+1:])
    return articleNumber in readArticlesNumbers

def loadReadArticles(path):
    with open(path, 'r') as f:
        data = f.read()
    return {int(line) for line in data.splitlines() if line}

#@profile
def main():
    parser = argparse.ArgumentParser(description='Scrapes all articles from lwn.net and presents them in chronological order')

    parser.add_argument('--url', default='https://lwn.net/Kernel/Index/', type=str, help='The URL to the page containing links to articles')
    parser.add_argument('--reverse', '-r', action='store_true', help='Reverse order of articles (newest first)')
    parser.add_argument('--pastArticles', '-p', default='pastArticles.dat', help='File which contains the id of articles which have already been read')

    args = parser.parse_args()

    readArticles = loadReadArticles(args.pastArticles)

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
        hasBeenRead = isRead(readArticles, article)
        return f'{title}{" (read)" if hasBeenRead else ""}\nhttps://lwn.net{link}\n{date}'

    delimiter = '\n\n'

    preCutoffArticlesString = delimiter.join(articleToString(art) for art in preCutoffArticles)
    postCutoffArticlesString = delimiter.join(articleToString(art) for art in postCutoffArticles)
    estimatedCutoffString = '----------------- Estimated subscription cutoff -----------------'
    out = delimiter.join((preCutoffArticlesString, estimatedCutoffString, postCutoffArticlesString))
    out = html.unescape(out)
    print(out)
main()
