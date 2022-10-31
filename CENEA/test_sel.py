
import time


from lxml import html, etree
import requests

user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36'
headers = {'User-Agent': user_agent}

url = "https://cenea.org.pl/2020/"
r = requests.get(url, headers=headers, timeout=20)
tree = html.fromstring(r.text)

urls = tree.xpath("//header[@class='article-header']/h2/a/@href")
print(urls)
titles  = tree.xpath("//header[@class='article-header']/h2/a/text()")
print(titles)

date = tree.xpath("//header[@class='article-header']/p")
for i in date:
    print(i.text)
    pub = etree.tostring(i, encoding='utf-8').strip().decode('utf-8')
    print(pub)

