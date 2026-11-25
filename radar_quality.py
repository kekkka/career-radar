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
    keys={'url:'+hashlib.sha256(normalized.encode()).hexdigest()}
    # Keep the historic URL key and add publisher-specific immutable IDs.
    # Never deduplicate solely by title/employer: distinct openings may share a title.
    patterns=[
        (('yandex.ru','www.yandex.ru'),r'/jobs/vacancies/[^/]+-(\d+)', 'yandex'),
        (('tbank.ru','www.tbank.ru'),r'/career/it/vacancy/.+/([0-9a-fA-F-]{36})','tbank'),
        (('aviasales.ru','www.aviasales.ru'),r'/about/vacancies/(\d+)','aviasales'),
        (('career.habr.com',),r'/vacancies/(\d+)','habr'),
        (('h.careers',),r'/job/([0-9a-fA-F-]{36})','hcareers'),
    ]
    for hosts,pattern,namespace in patterns:
        if host in hosts:
            m=re.fullmatch(pattern,path)
            if m: keys.add(namespace+':'+m[1].lower())
    return keys

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
    groups={}
    for key,status in health.items():
        company=key.split(' | ')[0]
        groups.setdefault(company,[]).append(status)
    available=[]; limited=[]; unavailable=[]
    for company,statuses in sorted(groups.items()):
        if all(s=='CARDS_FOUND' for s in statuses): available.append(company)
        elif 'CARDS_FOUND' in statuses or 'PARTIAL' in statuses: limited.append(company)
        else: unavailable.append(company)
    lines=['💗 Career Radar — итоги '+stats['day'],
           'Солнышко, вот результаты поиска!',
           '',
           'Новых вакансий: '+str(stats['sent']),
           'Повторов исключено: '+str(stats['duplicates']),
           'Проходов за день: '+str(stats['runs'])]
    outcomes=stats.get('outcomes',{})
    if outcomes:
        lines.extend(['Последний проход: стаж выше лимита — '+str(outcomes.get('REVIEW_3_PLUS',0))+'; не подтверждены требования или актуальность — '+str(outcomes.get('UNKNOWN',0))])
    avito=stats.get('avito',{})
    if avito:
        lines.extend(['','Авито: '+str(avito.get('cards',0))+' карточек, отправлено '+str(avito.get('sent',0))+' (последний проход).'])
        if avito.get('errors'): lines.append('Проверка Авито частичная.')
    lines.extend(['','Покрытие остальных работодателей:'])
    if available: lines.append('✅ Карточки получены: '+', '.join(available))
    if limited: lines.append('⚠️ Частичная проверка: '+', '.join(limited))
    if unavailable: lines.append('⚠️ Не удалось подтвердить покрытие: '+', '.join(unavailable))
    lines.append('Отсутствие карточек не означает отсутствие вакансий.')
    return '\n'.join(lines)[:3900]
