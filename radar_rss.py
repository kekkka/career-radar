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
