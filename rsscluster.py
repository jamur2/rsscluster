import HTMLParser
import datetime
import feedparser
import gensim
import logging
import opml
import simserver

class MLStripper(HTMLParser.HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def tokenize_html(html):
    s = MLStripper()
    s.feed(html)
    stripped_html = s.get_data().replace('\n', '')
    return gensim.utils.simple_preprocess(stripped_html)

def get_documents(feed):
    logging.info("Getting %s..." % feed)
    documents = []
    try:
        parsed_feed = feedparser.parse(feed)
    except Exception:
        logging.error("Problem parsing %s !" % feed)
        return []
    for entry in parsed_feed.entries:
        body = []
        if hasattr(entry, 'content'):
            for content in entry.content:
                body += tokenize_html(content.value)
        if hasattr(entry, 'summary'):
            body += tokenize_html(entry.summary)
            document = {
                'id': entry.link,
                'tokens': body,
                'payload': {'feed': feed, 'title': entry.title},
                'date': None
            }
            if hasattr(entry, 'published_parsed'):
                document['date'] = entry.published_parsed
        documents.append(document)
    return documents

def recurse_opml(outline):
    feeds = []
    for item in outline:
        if hasattr(item, 'xmlUrl'):
            feeds.append(item.xmlUrl)
        if len(item) > 0:
            feeds.extend(recurse_opml(item))
    return feeds

def get_feeds(path):
    outline = opml.parse(path)
    return recurse_opml(outline)

def main():
    logging.basicConfig(
        format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    feeds = get_feeds('foo.opml')
    logging.info("Getting documents...")
    documents = []
    for feed in feeds:
        documents.extend(get_documents(feed))
    server = simserver.SessionServer("gensim_server")
    logging.info("Training...")
    server.train(documents, method='lsi')
    print "Indexing..."
    server.index(documents)
    for document in documents:
        published = document['date']
        now = datetime.datetime.now()
        if (published and
                published[0] == now.year and
                published[1] == now.month and
                published[2] == now.day):
            similar_docs = [doc for doc in server.find_similar(document)
                if (doc[1] > 0.6 and doc[0] != document['id'] and
                    document['payload']['feed'] != doc[2]['feed'])]
            if len(similar_docs) > 0:
                print '-' * 79
                print "If you liked %s - %s" % (
                    document['payload']['title'], document['id'])
                print "You may also like:"
                for similar_doc in similar_docs:
                    print "             %s - %s" % (
                        similar_doc[2]['title'], similar_doc[0])


if __name__ == '__main__':
    main()
