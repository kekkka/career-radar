"""Offline quality helpers; no credentials or private data."""
import hashlib
import re
import time
from urllib.parse import urlsplit, parse_qsl, urlencode
from urllib.error import HTTPError, URLError

def identity_keys(company, link):
    p=urlsplit(link)
    host=(p.hostname or '').lower()
    if p.scheme!='https' or not host or p.username or p.password:
        return set()
    path=p.path.rstrip('/')
    query=urlencode(sorted((k,v) for k,v in parse_qsl(p.query) if not k.lower().startswith('utm_') and k.lower() not in ('trk','trackingid','ref','referrer')))
    if host in ('www.linkedin.com','linkedin.com'):
        m=re.fullmatch(r'/jobs/view/(?:[^/]+-)?(\d+)',path)
        if m: return {'linkedin:'+m[1]}
    if company=='Авито' and host=='career.avito.com':
        m=re.fullmatch(r'/(?:publications|vacancies)/[^/]+/(\d+|[a-fA-F0-9-]{36})',path)
        if m: return {'avito:'+m[1].lower()}
    # Hash all URLs, including forwarded links. Do not store private URL text.
    normalized='https://'+p.netloc.lower()+path+('?' + query if query else '')
    return {'url:'+hashlib.sha256(normalized.encode()).hexdigest()}

def retry_fetch(request, stats, sleep=time.sleep):
    for attempt in range(3):
        try: return request()
        except HTTPError as e:
            # Do not retry blocked resources or rate limits in the same run.
            if e.code not in (408,500,502,503,504) or attempt==2: raise
            delay=5*(2**attempt)
            wait=e.headers.get('Retry-After') if e.headers else None
            if wait:
                if not wait.isdigit() or int(wait)>30: raise
                delay=max(delay,int(wait))
        except (URLError,TimeoutError,ConnectionError):
            if attempt==2: raise
            delay=5*(2**attempt)
        stats['retries']=stats.get('retries',0)+1
        sleep(delay)

def source_status(pages,cards,errors,partial=False):
    if errors and errors>=pages: return 'ERROR'
    if errors or partial: return 'PARTIAL'
    if not pages or not cards: return 'NO_CARDS_UNVERIFIED'
    return 'CARDS_FOUND'

def daily_message(stats):
    health=stats.get('latest_health',{})
    counts={k:sum(v==k for v in health.values()) for k in ('CARDS_FOUND','PARTIAL','ERROR','NO_CARDS_UNVERIFIED')}
    lines=['📊 Career Radar — диагностика за '+stats['day'],
           'Солнышко, вот отчёт по общему мониторингу 💗',
           'Завершённых проходов: '+str(stats['runs']),
           'Отправлено вакансий: '+str(stats['sent']),
           'Исключено повторов: '+str(stats['duplicates']),
           'Сетевых повторов: '+str(stats['retries']),
           'Последний проход: '+str(len(health))+' источников',
           'Карточки найдены: '+str(counts['CARDS_FOUND']),
           'Частично: '+str(counts['PARTIAL']),
           'Ошибки: '+str(counts['ERROR']),
           'Без карточек (не подтверждено): '+str(counts['NO_CARDS_UNVERIFIED']),
           'Авито и Gmail отдельно; этот отчёт не подтверждает их работу.']
    for key,status in sorted(health.items()):
        if status!='CARDS_FOUND': lines.append(key.split(' | ')[0]+': '+status)
    return '\n'.join(lines)[:3900]
