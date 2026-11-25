"""Bounded RSS discovery; never infer employer or experience from a feed title."""
from xml.etree import ElementTree as ET
from urllib.parse import urlsplit
import re
from html import unescape

def rss_entries(raw):
    if not isinstance(raw,str) or len(raw)>2_000_000 or re.search(r'<!DOCTYPE|<!ENTITY',raw,re.I):
        raise ValueError('Unsafe or oversized feed')
    root=ET.fromstring(raw)
    if root.tag!='rss' or root.find('channel') is None:
        raise ValueError('Not an RSS channel')
    rows=[]; seen=set()
    for item in root.findall('./channel/item')[:100]:
        title=unescape(item.findtext('title','')).strip()
        link=item.findtext('link','').strip()
        p=urlsplit(link)
        if not title or p.scheme!='https' or not p.hostname or p.username or p.password or link in seen: continue
        seen.add(link)
        rows.append((link,title))
    return rows


# Only links explicitly supplied by the publisher in RSS, and only to known
# employer vacancy routes. No fetching the aggregator's HTML catalogue.
from html.parser import HTMLParser
from urllib.parse import urljoin

class OriginalLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag=='a':
            self.links.append(dict(attrs).get('href',''))

OFFICIAL_ROUTES={
    'Т-Банк': [('tbank.ru',r'/career/it/vacancy/.+/[0-9a-f-]{36}'),('www.tbank.ru',r'/career/it/vacancy/.+/[0-9a-f-]{36}')],
    'Точка': [('hr.tochka.com',r'/vacancies/catalog/[^/]+')],
    'Кинопоиск': [('yandex.ru',r'/jobs/vacancies/[^/]+-\d+')],
    'Dodo Brands': [],
    'Авиасейлс': [('www.aviasales.ru',r'/about/vacancies/\d+'),('aviasales.ru',r'/about/vacancies/\d+')],
}
def official_url(company,url):
    try: p=urlsplit(url)
    except ValueError: return None
    if p.scheme!='https' or p.username or p.password or p.port not in (None,443): return None
    for host,route in OFFICIAL_ROUTES.get(company,[]):
        if p.hostname==host and re.fullmatch(route,p.path.rstrip('/')):
            return 'https://'+host+p.path.rstrip('/')
    return None

def rss_originals(raw,company):
    rows=rss_entries(raw)
    valid={link:title for link,title in rows}
    root=ET.fromstring(raw)
    out=[]
    for item in root.findall('./channel/item')[:100]:
        link=item.findtext('link','').strip()
        if link not in valid: continue
        urls=[link]
        for child in item:
            tag=child.tag.rsplit('}',1)[-1].casefold()
            if tag in ('sourceurl','originalurl','original_url','applyurl','apply_url'):
                urls.append((child.text or '').strip())
            if tag in ('description','encoded','summary','content'):
                parser=OriginalLinks()
                parser.feed(child.text or '')
                urls.extend(parser.links)
        originals=set(filter(None,(official_url(company,u) for u in urls)))
        if len(originals)==1:
            out.append((link,valid[link],originals.pop()))
    return out
