import requests
import re
import time
import argparse
import html

from datetime import datetime, timedelta

def getArticleNumber(articleLink):
    lastSlashIndex = articleLink.rfind('/')
    if lastSlashIndex == -1:
        print(f'Error: could not find article number in {articleLink}')
        return -1

    articleNumber = int(articleLink[lastSlashIndex+1:])
    return articleNumber

def isRead(readArticlesNumbers, articleNumber):
    return articleNumber in readArticlesNumbers

def loadReadArticles(path):
    with open(path, 'r') as f:
        data = f.read()
    return {int(line) for line in data.splitlines() if line}

def getUserInput(message, validInputs):
    validInputsString = ",".join(validInputs)
    inp = ''
    while inp not in validInputs:
        print(f'{message} [{validInputsString}]: ', end='')
        inp = input()
    return inp

def articleToString(article):
    link, title, date, hasBeenRead = article
    return f'{title}{" (read)" if hasBeenRead else ""}\nhttps://lwn.net{link}\n{date}'

def readArticlesInteractively(articles):
    newlyReadArticles = set()
    quit = False
    for article in reversed(articles):
        if quit:
            break
        hasBeenRead = article[3]
        if not hasBeenRead:
            print(articleToString(article))

            action = getUserInput('Action', ['r', 's', 'q'])

            match action:
                case 'r':
                    articleNumber = getArticleNumber(article[0])
                    newlyReadArticles.add(articleNumber)
                case 's':
                    pass
                case 'q':
                    quit = True
                case _:
                    print(f'Error: invalid action {action}')

            print()
    return newlyReadArticles

#@profile
def main():
    parser = argparse.ArgumentParser(description='Scrapes all articles from lwn.net and presents them in chronological order')

    parser.add_argument('--url', default='https://lwn.net/Kernel/Index/', type=str, help='The URL to the page containing links to articles')
    parser.add_argument('--reverse', '-r', action='store_true', help='Reverse order of articles (newest first)')
    parser.add_argument('--pastArticles', '-p', default='pastArticles.dat', help='File which contains the id of articles which have already been read')
    parser.add_argument('--interactive', '-i', action='store_true', help='Go through all unread articles in reverse chronological order')

    args = parser.parse_args()

    readArticles = loadReadArticles(args.pastArticles)

    page = requests.get(args.url)

    article_multiline_regex = re.compile(r'class="IndexEntry".*\n.*<a href="(.*)/">(.*)</a> \((.*)\)</p>')
    articles = {
                (
                    link,
                    title,
                    datetime.strptime(date, "%B %d, %Y").date(),
                    isRead(readArticles, getArticleNumber(link))
                )
                for link, title, date in article_multiline_regex.findall(page.text)
               }

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

    if(args.interactive):
        newlyReadArticles = set()
        print("Articles needing subcription:\n")
        newlyReadArticles |= readArticlesInteractively(postCutoffArticles)
        print("Articles not needing subcription:\n")
        newlyReadArticles |= readArticlesInteractively(preCutoffArticles)

        print(f"Read articles {newlyReadArticles}")
        action = getUserInput(f'Add these articles as read to {args.pastArticles}', ['y', 'n'])
        if action == 'y':
            with open(args.pastArticles, 'a') as f:
                for articleNumber in newlyReadArticles:
                    f.write(f'{articleNumber}\n')
    else:
        delimiter = '\n\n'

        preCutoffArticlesString = delimiter.join(articleToString(art) for art in preCutoffArticles)
        postCutoffArticlesString = delimiter.join(articleToString(art) for art in postCutoffArticles)
        estimatedCutoffString = '----------------- Estimated subscription cutoff -----------------'
        out = delimiter.join((preCutoffArticlesString, estimatedCutoffString, postCutoffArticlesString))
        out = html.unescape(out)
        print(out)
main()
