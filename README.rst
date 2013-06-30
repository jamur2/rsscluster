rsscluster
==========

Gensim document similarity demonstration using RSS feeds as document sources


About
-----

`Gensim <http://radimrehurek.com/gensim/>`_ is a Python library used to perform
"topic modeling".  The most practical purpose for topic modelling is finding
similar documents.  This simple script serves as an example of the usage and
power of this library.  Given a list of RSS feeds (in OPML format), the
script will create a database of all stories contained in those feeds, and
show some sample clusters of similar stories.

For example, if an OPML file contains both The Washington Post and New York
Times feeds, a good cluster would include stories from both papers on the same
event, such as a recent presidential tour of Africa.


Installation
------------

First off, you'll need `virtualenv <http://www.virtualenv.org/en/latest/>`_.
Depending on your operating system and your tolerance for system packages, you
have a choice of installation methods.  Install it the way you want (or just
follow the `directions <http://www.virtualenv.org/en/latest/#installation>`_.

Once you're done with that, you can set up your environment.  From this
directory, run::

    $ virtualenv --no-site-packages .
    $ bin/pip install -r requirements.txt

Usage
-----

First, you'll need an OPML file.  Most readers allow you to export your feeds
as OPML.  If you can't, or you don't have enough feeds to generate interesting
output, feel free to use my sample file in this directory, named "feeds.opml"

The basic usage of rsscluster.py is::
    Usage: rsscluster.py [options] OPML_FILE

    Options:
    -h, --help            show this help message and exit
    -t THRESHOLD, --threshold=THRESHOLD
                            Documents whose similarity is larger than this
                            threshold will be considered similar (0-1,
                            default=0.6)
    -d DATE, --date=DATE  Publication date of stories to base clusters around
                            (format=YYY-MM-DD, default=today)
    -s, --skip-training   Skip training (if you already have an existing
                            database, you may want to skip the training step)
    -m, --html            HTML output
    -f OUTPUT_FILE, --output-file=OUTPUT_FILE
                            Output file (default=stdout)

For example, if you want to generate HTML output of feeds.opml in feeds.html,
you would run::

    $ bin/python rsscluster.py --html --output-file=feeds.html feeds.opml

By default, rsscluster will generate clusters around stories published on
the current day.  If you want to generate clusters around stories published
on other days, you would run::

    $ bin/python rsscluster.py --date=2013-06-29 feeds.opml

Also, rsscluster keeps the database around between runs.  This way, as older
stories fall off RSS feeds, they can still be indexed for similiarity in
the future.  Because the database sticks around, you don't really need to
retrain it on each run; you just need to index the new documents.  To skip
the training phase, you run::

    $ bin/python rsscluster.py --skip-training feeds.opml
