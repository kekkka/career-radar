"""Vacancy lifecycle and source helpers. No external dependencies."""
from datetime import datetime, timezone, date
from urllib.parse import urlsplit, parse_qsl, urlencode
import re

CLOSED=re.compile(r'эта вакансия в архиве|набор по вакансии закрыт|вакансия (?:уже )?(?:закрыта|архивирована|неактуальна|не актуальна)|данная вакансия.{0,40}не актуальна|вакансия больше не доступна|no longer accepting applications|this job is no longer available|this vacancy is closed',re.I)
def is_closed(text, postings=(), today=None):
    text=re.sub(r'\s+',' ',str(text or ''))
    if CLOSED.search(text): return True
    today=today or datetime.now(timezone.utc).date()
    for posting in postings:
        value=posting.get('validThrough')
        if not isinstance(value,str): continue
        try:
            if date.fromisoformat(value[:10]) < today: return True
        except ValueError: continue
    return False

def vacancy_key(url):
    p=urlsplit(url)
    params=urlencode(sorted((k,v) for k,v in parse_qsl(p.query,keep_blank_values=True) if not k.lower().startswith('utm_') and k.lower() not in {'trk','trackingid','ref','referrer'}))
    return p.scheme+'://'+p.netloc.lower()+p.path.rstrip('/')+('?' + params if params else '')

def belongs_to_habr(postings, aliases):
    for posting in postings:
        org=posting.get('hiringOrganization')
        if isinstance(org,dict) and isinstance(org.get('name'),str):
            if org['name'].strip().casefold() in {a.casefold() for a in aliases}: return True
    return False
