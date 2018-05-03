import logging
from bs4 import BeautifulSoup
from collections import Counter
from datamodel.search.MmaranoBhtruon1_datamodel import MmaranoBhtruon1Link, OneMmaranoBhtruon1UnProcessedLink
from spacetime.client.IApplication import IApplication
from spacetime.client.declarations import Producer, GetterSetter, Getter
from lxml import html,etree
import re, os
from time import time
from uuid import uuid4
import sys
from urlparse import urlparse, parse_qs
from uuid import uuid4
logger = logging.getLogger(__name__)
LOG_HEADER = "[CRAWLER]"
@Producer(MmaranoBhtruon1Link)
@GetterSetter(OneMmaranoBhtruon1UnProcessedLink)
class CrawlerFrame(IApplication):
    app_id = "MmaranoBhtruon1"

    def __init__(self, frame):
        self.app_id = "MmaranoBhtruon1"
        self.frame = frame

    def initialize(self):
        self.count = 0
        links = self.frame.get_new(OneMmaranoBhtruon1UnProcessedLink)
        if len(links) > 0:
            print "Resuming from the previous state."
            self.download_links(links)
        else:
            l = MmaranoBhtruon1Link("http://www.ics.uci.edu/")
            print l.full_url
            self.frame.add(l)

    def update(self):
        unprocessed_links = self.frame.get_new(OneMmaranoBhtruon1UnProcessedLink)
        if unprocessed_links:
            self.download_links(unprocessed_links)

    def download_links(self, unprocessed_links):
        for link in unprocessed_links:
            print "Got a link to download:", link.full_url
            downloaded = link.download()
            links = extract_next_links(downloaded)
            for l in links:
                if is_valid(l):
                    self.frame.add(MmaranoBhtruon1Link(l))

    def shutdown(self):
        print (
            "Time time spent this session: ",
            time() - self.starttime, " seconds.")


class MyAnalyticsLogger():
    # Logger keeps track of 4 things: 
    #   1. Page with the highest in degree, 
    #   2. Page with the highest out degree, 
    #   3. Pages that couldn't be parsed, and 
    #   4. Pages that were marked as traps
    def __init__(self):
        self.in_degree     = Counter()
        self.out_degree    = Counter()
        self.highest_in_degree_name    = ""
        self.highest_in_degree_number  = 0
        self.highest_out_degree_name   = ""
        self.highest_out_degree_number = 0
        self.error_parsing = set()
        self.traps = set()

    def log_links(self, was_parsed, rawDataObj, outputLinks):
        url = rawDataObj.url

        if not was_parsed:
            self.error_parsing.add(url)

        out_num = len(outputLinks)
        self.out_degree[url] = out_num
        if self.highest_out_degree_number < out_num:
            self.highest_out_degree_name   = url
            self.highest_out_degree_number = out_num

        for link in outputLinks:
            self.in_degree[link] += 1
        self.highest_in_degree_name, self.highest_in_degree_number = max(self.in_degree.items(), key=lambda x: x[1]) 
        
        self._write_to_file()

    def log_trap(self, url):
        self.traps.add(url)

    def _write_to_file(self):
        with open("log.txt", "w") as log:
            out_str = "Highest out degree: {}, {}\n".format(self.highest_out_degree_number, self.highest_out_degree_name)
            in_str  = "Highest  in degree: {}, {}\n".format(self.highest_in_degree_number,  self.highest_in_degree_name)
            log.write(out_str)
            log.write(in_str)

            in_set  = set(self.in_degree.viewkeys())
            out_set = set(self.out_degree.viewkeys())
            all_urls = in_set.union(out_set)

            for link in all_urls:
                body = "In: {},\tOut: {},\tURL: {}\n".format(self.in_degree[link], self.out_degree[link], link)
                log.write(body)

            log.write('\nPages that couldn\'t be parsed:\n')
            log.write(str(self.error_parsing))

            log.write('\n\nTraps:\n')
            log.write(str(self.traps))
    
my_logger = MyAnalyticsLogger()

def extract_next_links(rawDataObj):
    outputLinks = []
    was_parsed = True
    '''
    rawDataObj is an object of type UrlResponse declared at L20-30
    datamodel/search/server_datamodel.py
    the return of this function should be a list of urls in their absolute form
    Validation of link via is_valid function is done later (see line 42).
    It is not required to remove duplicates that have already been downloaded. 
    The frontier takes care of that.
    
    Suggested library: lxml
    '''

    if rawDataObj.is_redirected:
        outputLinks.append(rawDataObj.final_url)
       
    try:
        body = html.fromstring(rawDataObj.content)
        body = html.tostring(html.make_links_absolute(body, rawDataObj.url))

        soup = BeautifulSoup(body, "lxml")
        link_tags = soup.find_all("a")

        for link_tag in link_tags:
            if "href" in link_tag.attrs.keys():
                link = link_tag["href"]
                if "#" not in link and (link != rawDataObj.url): # avoid duplicates of the current page
                    outputLinks.append(link)

    except: # etree.XMLSyntaxError, etree.ParserError; changed to blanket except due to lack of understanding of possible errors in lxml
        was_parsed = False


    my_logger.log_links(was_parsed, rawDataObj, outputLinks)
    return outputLinks

def is_valid(url):
    # need to refactor so we don't write my_logger.log_trap(url) everywhere
    '''
    Function returns True or False based on whether the url has to be
    downloaded or not.
    Robot rules and duplication rules are checked separately.
    This is a great place to filter out crawler traps.
    '''
    parsed = urlparse(url)
    if parsed.scheme not in set(["http", "https"]):
        my_logger.log_trap(url)
        return False
    lowerPath = parsed.path.lower()
    if len(lowerPath)/(lowerPath.count("/") + 1) > 20:
        my_logger.log_trap(url)
        return False
    if parsed.query.count("=") > 2:
        my_logger.log_trap(url)
        return False
    if re.match("^.*calendar.*$", parsed.path.lower()):
        my_logger.log_trap(url)
        return False
    if re.match("^.*?(\/.+?\/).*?\1.*$|^.*?\/(.+?\/)\2.*$", parsed.path.lower()):
        my_logger.log_trap(url)
        return False
    if re.match("^.*(/misc|/sites|/all|/themes|/modules|/profiles|/css|/field|/node|/theme){3}.*$", parsed.path.lower()):
        my_logger.log_trap(url)
        return False
    try:
        return ".ics.uci.edu" in parsed.hostname \
            and not re.match(".*\.(css|js|bmp|gif|jpe?g|ico" + "|png|tiff?|mid|mp2|mp3|mp4"\
            + "|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf" \
            + "|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso|epub|dll|cnf|tgz|sha1" \
            + "|thmx|mso|arff|rtf|jar|csv"\
            + "|rm|smil|wmv|swf|wma|zip|rar|gz|pdf)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        return False

