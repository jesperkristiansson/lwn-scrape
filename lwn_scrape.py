import requests
import re
import time
import argparse
import threading
import html

LWN_BASE_URL = 'https://lwn.net'


class AtomicCounter():
    def __init__(self, n):
        self._val = n
        self._lock = threading.Lock()
        
    def inc(self):
        with self._lock:
            val = self._val
            self._val += 1
        return val

def multithread_comment_get_helper(input, output, n, counter, regex):
    while (i := counter.inc()) < n:
        print(input[i][0])
        url = LWN_BASE_URL + input[i][0]
        page = requests.get(url)
        comment_cnt = len(re.findall(regex, page.text))
        output[i] = (comment_cnt, input[i])
        

        
def multithread_comment_get(articles):
    n_threads = 10
    article_comment_regex = re.compile(r'CommAnchor')
    counter = AtomicCounter(0)
    articles = list(articles)
    articles_comment_count = [None]*len(articles)
    print(articles)
    
    threads = []
    for _ in range(n_threads):
        t = threading.Thread(target=multithread_comment_get_helper, args=[articles, articles_comment_count, 10, counter, article_comment_regex])
        t.start()
        threads.append(t)
        
    for t in threads:
        t.join()
        
    sorted_articles = sorted(articles_comment_count)
    return sorted_articles

#@profile
def main():
    parser = argparse.ArgumentParser(description='Scrapes all articles from lwn.net and presents them in chronological order')

    parser.add_argument('--url', default='https://lwn.net/Kernel/Index/', type=str, help='The URL to the page containing links to articles')
    parser.add_argument('--reverse', '-r', action='store_true', help='Reverse order of articles (newest first)')
    parser.add_argument('--comments', '-c', action='store_true', help='Sort by number of comments')

    args = parser.parse_args()

    page = requests.get(args.url)

    article_multiline_regex = re.compile(r'class="IndexEntry".*\n.*<a href="(.*)/">(.*)</a> \((.*)\)</p>')
    articles = set(re.findall(article_multiline_regex, page.text))

    if args.comments:
        sorted_articles = multithread_comment_get(articles)
        article_string_generator = ('' for e in sorted_articles)
    else:
        sorted_articles = sorted(articles, key=lambda t: int(t[0][10:]),reverse=args.reverse)
        article_string_generator = (f'{title}\nhttps://lwn.net{link}\n{date}' for link, title, date in sorted_articles)
    out = '\n\n'.join(article_string_generator)
    out = html.unescape(out)
    print(out)
main()
