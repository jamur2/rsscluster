import HTMLParser
import codecs
import datetime
import feedparser
import gensim
import logging
import opml
import optparse
import simserver
import sys


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

def text_output(doc, similar_docs, fi):
    if len(similar_docs) > 0:
        fi.write(u'-' * 79 + u'\n')
        fi.write(u"If you liked:\n")
        fi.write(u"    %s\n" % doc['payload']['title'])
        fi.write(u"        URL: %s\n" % doc['id'])
        fi.write(u"You may also like:\n")
        for similar_doc in similar_docs:
            fi.write(u"    %s\n" % similar_doc[2]['title'])
            fi.write(u"        URL: %s\n" % similar_doc[0])
        fi.flush()


def html_head(fi):
    fi.write(u'<html>\n')
    fi.write(u'    <head>\n')
    fi.write(u'        <meta charset="utf-8">\n')
    fi.write(u'    </head>\n')
    fi.write(u'<body>\n')
    fi.flush()


def html_foot(fi):
    fi.write(u'</body>\n')
    fi.flush()


def html_output(doc, similar_docs, fi):
    if len(similar_docs) > 0:
        fi.write(u"<p>If you liked:</p>")
        fi.write(u'<a href="%s">%s</a>' % (
            doc['id'],
            doc['payload']['title']))
        fi.write(u"<p>You may also like:</p>")
        fi.write(u"<ul>")
        for similar_doc in similar_docs:
            fi.write(u'<li><a href="%s">%s</a></li>' % (
                similar_doc[0],
                similar_doc[2]['title']))
        fi.write(u"</ul>")
        fi.flush()


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
        if hasattr(entry, 'summary') and hasattr(entry, 'link'):
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
    usage = "usage: %prog [options] OPML_FILE"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-t", "--threshold",
        action="store", type="float",
        help="Documents whose similarity is larger than this threshold will "
            "be considered similar (0-1, default=0.6)",
        default=0.6)
    parser.add_option("-d", "--date",
        action="store",
        help="Publication date of stories to base clusters around "
            "(format=YYY-MM-DD, default=today)",
        default=None)
    parser.add_option("-s", "--skip-training",
        action="store_true",
        help="Skip training (if you already have an existing database, "
            "you may want to skip the training step)")
    parser.add_option("-m", "--html",
        action="store_true",
        help="HTML output")
    parser.add_option("-f", "--output-file",
        action="store",
        help="Output file (default=stdout)")
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.print_help()
        return
    if options.output_file:
        output_file = codecs.open(
            options.output_file, 'w', encoding='utf-8',
            errors='')
    else:
        output_file = sys.stdout
    logging.basicConfig(
        format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    feeds = get_feeds(args[0])
    logging.info("Getting documents...")
    documents = []
    for feed in feeds:
        documents.extend(get_documents(feed))
    server = simserver.SessionServer("gensim_server")
    if options.skip_training:
        logging.info("Skipping training")
    else:
        logging.info("Training...")
        server.train(documents, method='lsi')
    logging.info("Indexing...")
    server.index(documents)
    if options.date is None:
        date = datetime.datetime.now()
    else:
        date = datetime.datetime.strptime(options.date, "%Y-%m-%d")
    if options.html:
        html_head(output_file)
    for document in documents:
        published = document['date']
        if (published and
                published[0] == date.year and
                published[1] == date.month and
                published[2] == date.day):
            similar_docs = [doc for doc in server.find_similar(document)
                if (doc[1] > options.threshold and doc[0] != document['id'])]
            if len(similar_docs) > 0:
                if options.html:
                    html_output(document, similar_docs, output_file)
                else:
                    text_output(document, similar_docs, output_file)
    if options.html:
        html_foot(output_file)
    output_file.close()


if __name__ == '__main__':
    main()
