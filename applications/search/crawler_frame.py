import logging
from bs4 import BeautifulSoup
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
    
# format of log_dict: (number of out links, number of times linked to)
log_dict = dict()
pages_raising_parse_error = set()

def log_page(was_parsed, rawDataObj, outputLinks): # -> None
    if not was_parsed:
        pages_raising_parse_error.add(rawDataObj.url)
        return

    num_out_links = len(outputLinks)
    url = rawDataObj.url

    if url not in log_dict.keys():
        log_dict[url] = (num_out_links, 0)

    for link in outputLinks:
        if link in log_dict.keys():
            log_dict[link] = (log_dict[link][0], log_dict[link][1] + 1)
        else:
            log_dict[link] = (0, 1)
    #print log_dict



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

    except:
        was_parsed = False


    log_page(was_parsed, rawDataObj, outputLinks)
    return outputLinks

def is_valid(url):
    '''
    Function returns True or False based on whether the url has to be
    downloaded or not.
    Robot rules and duplication rules are checked separately.
    This is a great place to filter out crawler traps.
    '''
    # Note that the frontier takes care of duplicates. 
    #print >> sys.stderr, url
    parsed = urlparse(url)
    if parsed.scheme not in set(["http", "https"]):
        return False
    lowerPath = parsed.path.lower()
    if len(lowerPath)/(lowerPath.count("/") + 1) > 20:
		return False
    if parsed.query.count("=") > 2:
        return False
    if re.match("^.*calendar.*$", parsed.path.lower()):
        return False
    if re.match("^.*?(\/.+?\/).*?\1.*$|^.*?\/(.+?\/)\2.*$", parsed.path.lower()):
        return False
    if re.match("^.*(/misc|/sites|/all|/themes|/modules|/profiles|/css|/field|/node|/theme){3}.*$", parsed.path.lower()):
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

