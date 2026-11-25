"""Vacancy lifecycle and source helpers. No external dependencies."""
from datetime import datetime, timezone, date
from urllib.parse import urlsplit, parse_qsl, urlencode
import re

CLOSED=re.compile(r'(?:эта\s+)?вакансия\s+(?:находится\s+)?в архиве|вакансия перенесена в архив|вакансия (?:была )?снята с публикации|вакансия больше недоступна|прием откликов (?:завершен|закрыт)|приём откликов (?:завершён|закрыт)|набор по вакансии закрыт|вакансия (?:уже )?(?:закрыта|архивирована|неактуальна|не актуальна)|данная вакансия.{0,40}не актуальна|вакансия больше не доступна|no longer accepting applications|this job is no longer available|this vacancy is closed',re.I)
def is_closed(text, postings=(), today=None):
    text=re.sub(r'\s+',' ',str(text or ''))
    if CLOSED.search(text): return True
    today=today or datetime.now(timezone.utc).date()
    for posting in postings:
        if str(posting.get('employmentStatus','')).lower() in ('closed','expired','archived'): return True
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


def archived_label(chunks,title):
    """Short archive badge near a job title, never arbitrary archive mentions."""
    clean=[re.sub(r'\s+',' ',str(c)).strip().casefold() for c in chunks if str(c).strip()]
    title=re.sub(r'\s+',' ',title).strip().casefold()
    for i,c in enumerate(clean):
        if c==title:
            return any(x in ('в архиве','архивная вакансия','архив','vacancy archived','closed','expired') for x in clean[max(0,i-3):i+10])
    return False


def posting_experience(postings):
    """Schema.org minimum months are candidate requirements."""
    result=[]
    for p in postings:
        x=p.get('experienceRequirements')
        if isinstance(x,dict):
            months=x.get('monthsOfExperience')
            try:
                if isinstance(months,bool): continue
                n=float(months)
                if not 0<=n<=600: continue
                result.append(('REVIEW_3_PLUS' if n>24 else 'POSSIBLE_MATCH',f'{n/12:g} years'))
            except (TypeError,ValueError): continue
        elif isinstance(x,str):
            from radar_experience import experience
            result.append(experience(x))
    from radar_experience import combine_experience
    return combine_experience(*result)

def active_application(chunks,links,title):
    """Conservative positive evidence for public application availability."""
    clean=[re.sub(r'\s+',' ',str(x)).strip().casefold() for x in chunks]
    if archived_label(chunks,title) or is_closed(' '.join(clean)): return False
    if any(re.fullmatch(r'(?:откликнуться(?: на вакансию)?|отправить отклик|apply(?: now)?|подать заявку)',x) for x in clean): return True
    return any(re.fullmatch(r'(?:откликнуться(?: на вакансию)?|отправить отклик|apply(?: now)?|подать заявку)',str(label).strip().casefold()) for _,label in links)
