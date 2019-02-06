# -*- coding: utf-8 -*-
# this script would be run as part of the initialisation of the web server, its purpose is to scrape the web, build a list of all new articles
# (not currently in the database) and scan their body for any mention of a sitting MP, having determined those that mention politicians, the
# rest are scrapped, and those remaining are added to an SQL database along with references to those mentioned for viewing with a Flask web server
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from politicsapp import db

import csv
import urllib
import urllib.request, json
import curses
from curses import wrapper
from tabulate import tabulate
from bs4 import BeautifulSoup
import requests
import newspaper
import uuid


### SOURCES (one example is shown here - the independent)
the_independent = ['The Independent','http://independent.co.uk/news/uk/politics/']
###


from politicsapp.models import Politician, Article, DiscardedArticle, NonDownloadableArticle, RedundantText
#urllib.request.urlretrieve("http://lda.data.parliament.uk/commonsmembers.json?_view=members&_pageSize=2000&_page=0", "westminster_mps_raw.json")

print('loading government database file')
with open('westminster_mps_raw.json') as westminster_json:
    print('scanning for changes')
    jsonraw = json.load(westminster_json)
    nresults = int(jsonraw['result']['totalResults'])
    for i in range(0, nresults):
        full_id = jsonraw['result']['items'][i]['_about']
        id = int(full_id[len('http://data.parliament.uk/members/'):])
        politician = Politician.query.filter_by(id=id).first()
        if not politician:
            full_name = jsonraw['result']['items'][i]['fullName']['_value']
            first_name = jsonraw['result']['items'][i]['givenName']['_value']
            last_name = jsonraw['result']['items'][i]['familyName']['_value']
            gender = jsonraw['result']['items'][i]['gender']['_value']
            party = jsonraw['result']['items'][i]['party']['_value']
            constituency = jsonraw['result']['items'][i]['constituency']['label']['_value']
            if jsonraw['result']['items'][i].get('homePage'):
                weburl = jsonraw['result']['items'][i]['homePage']
            if jsonraw['result']['items'][i].get('twitter'):
                twitterurl = jsonraw['result']['items'][i]['twitter']['_value']
                try:
                    print('downloading profile image for %s...' % full_name)
                    twitter_profile_response = requests.get(twitterurl, timeout=5)
                    soup = BeautifulSoup(twitter_profile_response.content, "html.parser")
                    img = soup.find("img", {"class":"ProfileAvatar-image"})
                    if img:
                        imgsrc = img.get('src')
                        if imgsrc:
                            jpeg = requests.get(imgsrc, allow_redirects=True)
                            if jpeg.status_code == 200:
                                with open('politicsapp/static/image/mp_pics/%d.jpg' % id, 'wb') as f:
                                    f.write(jpeg.content)
                                profile_image = 'politicsapp/static/image/mp_pics/%d.jpg' % id
                except:
                    print('profile image for %s failed to download!' % full_name)
            politicianNew = Politician(id=id, full_name=full_name, first_name=first_name,
                last_name=last_name, gender=gender, party=party, constituency=constituency, weburl=weburl,
                twitterurl=twitterurl, profile_image=profile_image)
            db.session.add(politicianNew)
            profile_image = None
            weburl = None
            twitterurl = None

print('politician database is up to date')

print('starting search for new articles from the independent')
politicians = Politician.query.all()

try:
    news_source = newspaper.build('http://independent.co.uk/news/uk/politics/')
    print('web link initialised')
except:
    print('failed to connect to \'{0}\''.format(the_independent[0]))

if news_source:
    print('starting scan new articles from {0}'.format(the_independent[0]))
    new_articles = 0
    announce_new_articles = 1
    for i in range(0,len(news_source.articles)):
            # loop through all the articles in the source
            article_data = news_source.articles[i]
            article_exist = Article.query.filter_by(url=article_data.url).first()
            article_discarded = DiscardedArticle.query.filter_by(url=article_data.url).first()
            article_nondownloadable = NonDownloadableArticle.query.filter_by(url=article_data.url).all()
            if not article_exist:
                if not article_discarded:
                    if len(article_nondownloadable) < 2:
                        # if the article is not in the database (anywhere)
                        if announce_new_articles == 1:
                            print('new articles discovered')
                            # print on the first iteration
                        announce_new_articles = 0
                        print('downloading article {0} of {1}'.format(i+1, len(news_source.articles)+1))
                        try:
                            # attempt download
                            article_data.download()
                            article_data.parse()
                            if article_data.publish_date:
                                #try:
                                    # attempt database submission
                                new_article = Article(url=str(article_data.url), source=str(the_independent[0]), title=str(article_data.title),
                                authors=', '.join(article_data.authors), publish_date=str(article_data.publish_date), text=str(article_data.text),
                                top_image=str(article_data.top_image), summary=str(article_data.summary))
                                new_articles = new_articles + 1
                                npoliticians = 0
                                # test is any politicians are mentioned
                                for politician in politicians:
                                    politician_name = '{0} {1}'.format(politician.first_name, politician.last_name)
                                    if politician_name in article_data.text:
                                        npoliticians = npoliticians +1
                                        #new_article.politicians.append(politician)
                                        #print('• match found - adding article to database ({0})'.format(politician_name))
                                if npoliticians:
                                    print('• {0} politicians mentioned - adding article to database'.format(npoliticians))
                                    db.session.add(new_article)
                                else:
                                    # discard if none are mentioned
                                    url_to_discard = DiscardedArticle(url=article_data.url)
                                    db.session.add(url_to_discard)
                                    new_articles = new_articles - 1
                                    print('no politicians mentioned - article discarded')

                                #except:
                                #    # catch a format error
                                #    url_to_discard = DiscardedArticle(url=article_data.url)
                                #    db.session.add(url_to_discard)
                                #    new_articles = new_articles - 1
                                #    print('there has been a format error - article discarded')

                            else:
                                db.session.remove(new_article)
                                url_to_discard = DiscardedArticle(url=article_data.url)
                                db.session.add(url_to_discard)
                                new_articles = new_articles - 1
                                print('this is not an article - article discarded')
                        except:
                            article_nondownloadable = NonDownloadableArticle.query.filter_by(url=article_data.url).all()
                            if len(article_nondownloadable) < 1:
                                print('download failed - skipping this time ')
                            else:
                                print('article failed to be downloaded twice - discarded as non-downloadable')
                            url_to_discard_as_nondownloadable = NonDownloadableArticle(url=article_data.url)
                            db.session.add(url_to_discard_as_nondownloadable)
                            new_articles = new_articles - 1

print('{0} new articles have been added'.format(new_articles))
db.session.commit()
print('changes have been committed to the dabase')


print('testing for duplicates')
all_articles = Article.query.all()
nduplicates= 0
for article in all_articles:
    duplicates = Article.query.filter_by(title=article.title).all()
    if len(duplicates) > 1:
        for i in range (1, len(duplicates)):
            duplicate = duplicates[i]
            url_to_discard = DiscardedArticle(url=article.url)
            db.session.add(url_to_discard)
            db.session.delete(duplicate)
            nduplicates = nduplicates + 1

if nduplicates > 1:
    print('{0} duplicate articles found - these have been discarded'.format(nduplicates))
else:
    print('no duplicate articles were found')


print('generating summaries')
for article in all_articles:
    #article.summary = (article.text[:500] + '...') if len(article.text) > 500 else article.text
    article.summary = article.text.split("\n")[0] + '...'

all_articles = Article.query.all()
print('removing unwanted paragraph blocks')
for article in all_articles:
    split_paragraphs = article.text.split("\n")
    nparagraphs = len(split_paragraphs)
    if nparagraphs > 2:
        for i in range (0, nparagraphs-1):
            paragraph = split_paragraphs[i]
            redundant_texts = RedundantText.query.all()
            for text in redundant_texts:
                if paragraph[:len(text.opening_string)] == text.opening_string:
                    del split_paragraphs[i]
        if split_paragraphs[i] == '' or ' ' or '  ' or '   ' or '    ' or '     ':
            del split_paragraphs[i]
        article.text = '\n'.join(split_paragraphs)

print('testing articles for mentioned politicians')
all_articles = Article.query.all()
politicians = Politician.query.all()
nremoved = 0
for article in all_articles:
    npoliticians = 0
    for politician in politicians:
        politician_name = '{0} {1}'.format(politician.first_name, politician.last_name)
        if politician_name in article.text:
            npoliticians = npoliticians + 1
            article.politicians.append(politician)
    if not npoliticians:
        Article.query.filter_by(id=article.id).delete()
        nremoved = nremoved + 1
if nremoved > 1:
    print('no politicians mentioned in {0} articles - these have been discarded'.format(nremoved))

print('article links up to date')

db.session.commit() # commits the session to site.db
print('changes have been committed to the dabase')

print('beginning boot sequence') # hands over to the Flask main method for initialising the server
