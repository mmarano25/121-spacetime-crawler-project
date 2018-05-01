from bs4 import BeautifulSoup
from lxml.html import parse, make_links_absolute, tostring

url = "/home/matt/Desktop/documentation/python3.6/python-3.6.3-docs-html/installing/index.html"
with open(url, "r") as html:
    html2 = parse(html)
    html2 = make_links_absolute(html2.getroot(), url)
    html2 = tostring(html2)
    
    soup = BeautifulSoup(html2, "lxml")
    print soup.prettify()
    links = soup.find_all("a")
    for l in links:
        print l['href']
