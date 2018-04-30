from bs4 import BeautifulSoup

url = "/home/matt/Desktop/documentation/python3.6/python-3.6.3-docs-html/installing/index.html"
with open(url, "r") as html:
    soup = BeautifulSoup(html, "lxml")
    # print soup.prettify()
    links = soup.find_all("a")
    for l in links:
        print l['href']
