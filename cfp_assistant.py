import urllib2
import urllib
import urlparse
import logging
import time
import os
import re
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.ERROR,format="%(asctime)s:%(message)s",\
        filename="fetch.log",filemode="w")

BAD_INFO_URL = "./.bad_conf_info_page_tmp"
BAD_INDEX_URL = "./.url_processing_tmp"
CONTENT_FILE = "./conf_list.txt"

class RetrieveError(Exception):
    None

def cleanup_tmp_files():
    if os.path.isfile(BAD_INDEX_URL):
        os.remove(BAD_INDEX_URL)
    if os.path.isfile(BAD_INFO_URL):
        os.remove(BAD_INFO_URL)

def retrieve_page(url):
    '''
    retrieve the html from a certain url.
    '''
    user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'
    values = dict(name = "Jacob Van",location="Shenzhen",language='python')
    headers = {'User-Agent':user_agent}
    data = urllib.urlencode(values)
    req = urllib2.Request(url,data,headers)
    try:
        response = urllib2.urlopen(req)
        page = response.read()
        return page
    except urllib2.HTTPError as e:
        logging.error("{0}:HTTPError errorcode:{1}".format(url,e.code))
        raise RetrieveError
    except urllib2.URLError as e:
        logging.error("{0}:URLError error code:{1[0]} error resone:{1[1]}".format(url,list(e.reason)))
        raise RetrieveError

def process_conf_info_page(conf_info_page_url):
    try:
        conf_info_page = retrieve_page(conf_info_page_url)
        bs = BeautifulSoup(conf_info_page,"lxml")
        content_div_tag = bs.find('div',class_='contsec')    #find the div with contsec class
        real_conf_link_tag = content_div_tag.find('a',target="_newtab")
        if real_conf_link_tag:
            real_conf_link_url = real_conf_link_tag['href']
            with open(CONTENT_FILE,'a') as af:
                af.write(real_conf_link_url)
                af.write('\n')
                print "retrive conf link {}".format(real_conf_link_url)
    except RetrieveError as e:
        with open(BAD_INFO_URL,"a") as af:
            af.write(conf_info_page_url)
            af.write("\n")


def process_index_page(index_page_url):
    #retrieve the index pages and turn it to be BeautifulSoup
    try:
        index_page = retrieve_page(index_page_url)
        bs = BeautifulSoup(index_page,"lxml")

        #construct the base url
        index_page_netloc = urlparse.urlparse(index_page_url).netloc
        base_url = urlparse.ParseResult(scheme="http",netloc=index_page_netloc,path='', params='', query='', fragment='').geturl()

        #retrieve the conference information from the table in contsec css class
        content_div_tag = bs.find('div',class_='contsec')    #find the div with contsec class
        conf_table_tag = content_div_tag.find('table')      #the table in this div block contains the conferences' information
        conf_link_tag_filter = re.compile(".*event.*")
        #iterate the links in the table and process them
        for conf_link_tag in conf_table_tag.find_all('a',href=conf_link_tag_filter):
            conf_info_page_url = urlparse.urljoin(base_url,conf_link_tag['href'])
            process_conf_info_page(conf_info_page_url)

        #find the next index page
        next_link_tag = bs.find('a',string='next')
        if next_link_tag :
            #join the base url and the next link path
            next_link_url= urlparse.urljoin(base_url,next_link_tag['href'])
            #process the next index page
            process_index_page(next_link_url)
    except RetrieveError as e:
        with open(BAD_INDEX_URL,'w') as wf:
            wf.write(index_page_url)


def init_retrieval():
    #prepare the conference link file
    if not os.path.isfile(CONTENT_FILE):
        with open(CONTENT_FILE,"w"):
            None        #if there isn't a conf_list file, touch a empty one
    init_url = "http://www.wikicfp.com/cfp/allcfp" #the recent posted conferences
    if os.path.isfile(BAD_INDEX_URL):
        with open("./.index_url_processing_tmp") as f:    #check whether the script was interupted last time
            init_url = f.readline().strip()
    print "script will start using url {}".format(init_url)
    process_index_page(init_url)


if __name__ == '__main__':
    init_retrieval()
