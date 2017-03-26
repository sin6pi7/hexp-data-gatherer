import time

import bs4 as bs
from urllib2 import urlopen
import re
import nltk
from geograpy import places
import json


def nltk_extraction ( test ):
    sentences = nltk.sent_tokenize( test )
    tokenized_sentences = [nltk.word_tokenize(sentence) for sentence in sentences]
    tagged_sentences = [nltk.pos_tag(sentence) for sentence in tokenized_sentences]
    chunked_sentences = nltk.batch_ne_chunk(tagged_sentences, binary=True)

    entity_names = []
    for tree in chunked_sentences:
        # Print results per sentence
        # print extract_entity_names(tree)

        entity_names.extend(extract_entity_names(tree))

    #print set(entity_names)
    return entity_names



def extract_entity_names(t):
    entity_names = []

    if hasattr(t, 'node') and t.node:
        if t.node == 'NE':
            entity_names.append(' '.join([child[0] for child in t]))
        else:
            for child in t:
                entity_names.extend(extract_entity_names(child))

    return entity_names



def get_places ( names_set ):

    pc = places.PlaceContext( names_set )

    pc.set_countries()
    contries = pc.countries
    pc.set_regions()
    regions = pc.regions
    pc.set_cities()
    cities = pc.cities

    return { 'countries':contries ,'regions':regions,'cities':cities}



main_source = 'https://en.wikipedia.org'

source = urlopen( main_source + '/wiki/List_of_historical_period_drama_films_and_series' ).read()
soup = bs.BeautifulSoup(source,'lxml')

##get all table from movies
tables = soup.findAll("table", class_='wikitable')

films_list = []

for table in tables[0:]:
    #go to all tables

    if table.findParent("table") is None:
        #get every row
        table_rows = table.find_all('tr')
        #execept the first
        for tr in table_rows[1:3]:
            tds = tr.find_all('td')
            if tds:
                ##extract vars for name and wiki entry
                name = tds[0].text
                try:
                    wiki_link = main_source + tds[0].a["href"]
                except:
                    wiki_link = "none"

                release_date = tds[1].text

                #split dates from-to
                time_period = re.sub(r'\W+', '-', tds[2].text)
                time_period = time_period.split("-",1)
                time_period_from_to = tuple(time_period)

                #get small historical description and links
                plot_desc = tds[3].text
                plot_desc_links = []
                for a in tds[3].find_all('a', href=True):
                    plot_desc_links.append( main_source + a['href'] )

                #fill the movie fields
                film_info = {'name': name,
                             'wiki_link': wiki_link,
                             'release_date': release_date,
                             'time_period_from_to': time_period_from_to,
                             'plot_desc': plot_desc,
                             'plot_desc_links': plot_desc_links,
                             }
                films_list.append(film_info)


for film in films_list:
    link = film["wiki_link"]

    plot_description = ""

    movie_source = urlopen( link ).read()
    soup_wiki = bs.BeautifulSoup(movie_source, 'lxml')

    #wikipedia is not divided in clean divs everything is parallel
    teste = soup_wiki.find('span', id="Plot" )
    #verify if wiki entry as "plot" paragraph
    if teste:
        #concatenated all <p> tags from a max of 10
        #TODO have to find a way of getting sibling from h2 tag to next h2 tag
        for i in teste.parent.find_next_siblings('p', limit=10):
            plot_description += i.text

        #runs the NLTK stuff to extract locations
        film.update({'locations': get_places (nltk_extraction(plot_description))})

    #print (json.dumps(film, indent=3))


with open('data.txt', 'w') as outfile:
    json.dump(films_list, outfile)

