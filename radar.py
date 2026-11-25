import os, re, json, sqlite3, time, argparse, logging
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from html.parser import HTMLParser
from pathlib import Path

COMPANIES = json.loads(Path(__file__).with_name('companies.json').read_text())
ROLE = re.compile(r'product\s*(?:manager|owner)|продакт[ -]?менеджер|менеджер[а]?\s+(?:по развитию\s+)?продукт[а-я]*|стаж[её]р.*продукт', re.I)
EXCLUDE = re.compile(r'\b(senior|lead|head|cpo|principal)\b|старший|руководитель|директор|product marketing', re.I)
ANALYST = re.compile(r'product\s*analyst|продуктов\w*\s+аналитик|аналитик\s+продукт|growth\s+analyst', re.I)
GENERAL = re.compile(r'data\s*analyst|аналитик\s+данных|^(?:junior\s+|младший\s+|стаж[её]р[- ]*)?аналитик(?:\s|$)', re.I)
OTHER = re.compile(r'\bBI\b|системн\w*\s+аналитик|бизнес[- ]аналитик|финансов\w*\s+аналитик|маркетингов\w*\s+аналитик|business analyst|financial analyst|marketing analyst|system analyst',re.I)
SIGNALS = [r'воронк|funnel',r'когорт|cohort',r'retention|удержани',r'a/b|а/б|ab-тест',r'продуктов\w*\s+метрик|product metrics',r'продуктов\w*\s+гипотез',r'конверси|conversion']
SKILLS = {'SQL':r'\bSQL\b','Python':r'\bPython\b','A/B':r'a/b|а/б|ab-тест','Excel':r'\bExcel\b','ClickHouse':r'\bClickHouse\b','Tableau':r'\bTableau\b','Power BI':r'\bPower BI\b','Статистика':r'статистик|statistics'}
def direction(title, description=''):
    if EXCLUDE.search(title) or OTHER.search(title): return None
    if ANALYST.search(title): return 'Product Analytics'
    if GENERAL.search(title) and sum(bool(re.search(x,description,re.I)) for x in SIGNALS)>=2: return 'Product Analytics'
    if ROLE.search(title): return 'Product Management'
    return None

def candidate(title):
    return not EXCLUDE.search(title) and not OTHER.search(title) and bool(ROLE.search(title) or ANALYST.search(title) or GENERAL.search(title))

EXP = re.compile(r'(?:от\s*|не менее\s*|минимум\s*|более\s*|at least\s*|minimum\s*)?(\d+(?:[.,]\d+)?)\s*(?:[–—-]\s*\d+\s*)?\+?\s*(лет|года?|years?|месяц[а-я]*|months?)', re.I)
class Plain(HTMLParser):
    def __init__(self): super().__init__(); self.parts=[]
    def handle_data(self,d): self.parts.append(d)
    def handle_starttag(self,tag,attrs):
        if tag in ('li','p','br','div','h2','h3'): self.parts.append('\n')
def plain(s):
    p=Plain(); p.feed(s or ''); return ''.join(p.parts)
def classify(title, description, band=''):
    if not direction(title, description): return None
    evidence=[]; hard=[]; ambiguous=False
    for line in re.split(r'\n|(?<=[.!?])\s+',description):
        if not re.search(r'опыт|стаж|experience|worked|работал|работы',line,re.I): continue
        for m in EXP.finditer(line):
            n=float(m[1].replace(',','.')); n=n/12 if re.match(r'месяц|month',m[2],re.I) else n
            evidence.append(line.strip()[:350])
            if re.search(r'желатель|плюсом|преимуществ|preferred|nice to have|будет плюсом',line,re.I): ambiguous=True; continue
            hard.append(n)
    if not hard and re.search(r'без опыта|опыт не требуется|no experience required',description,re.I): return ('P1','Опыт не требуется','Без обязательного опыта')
    if hard and min(hard)>2: return None
    if hard and max(hard)>2: return ('P3','Противоречивые требования к стажу', ' / '.join(evidence)[:700])
    if hard: return ('P1' if max(hard)<=1 else 'P2','Минимальный опыт соответствует', ' / '.join(evidence)[:700])
    if band in ('between3And6','moreThan6') and not ambiguous: return None
    return ('P3','Точный обязательный стаж не установлен; проверь описание', ' / '.join(evidence)[:700] or 'Не найдено точной формулировки')
def norm(s): return re.sub(r'[^\w]+','',s.casefold()).replace('ё','е')
def employer(name):
    n=norm(name)
    for company, aliases in COMPANIES.items():
        if n in [norm(x) for x in [company,*aliases]]: return company
    return None

def api(path,params=None):
    headers={'User-Agent':os.getenv('HH_USER_AGENT','CareerRadar/0.2 (personal vacancy monitor)')}
    if os.getenv('HH_TOKEN'): headers['Authorization']='Bearer '+os.environ['HH_TOKEN']
    req=Request('https://api.hh.ru/'+path+('?' + urlencode(params) if params else ''),headers=headers)
    with urlopen(req,timeout=30) as r: return json.load(r)
def collect():
    seen=set()
    for term in ['product manager','product owner','продакт менеджер','менеджер продукта','менеджер по развитию продукта','стажер продукт','product analyst','продуктовый аналитик','аналитик продукта','growth analyst','data analyst','аналитик данных','аналитик','стажер аналитик']:
        page=0
        while True:
            data=api('vacancies',{'text':term,'search_field':'name','per_page':100,'page':page})
            for item in data.get('items',[]):
                vid=item['id']; company=employer(item.get('employer',{}).get('name',''))
                if vid in seen or not company or not candidate(item['name']): continue
                seen.add(vid); detail=api('vacancies/'+vid); time.sleep(.25)
                yield dict(id=vid,company=company,title=detail['name'],description=plain(detail.get('description')),band=(detail.get('experience') or {}).get('id',''),url=detail.get('alternate_url',''),published=detail.get('published_at',''))
            page+=1
            if page>=data.get('pages',0) or page>=20: break
            time.sleep(.5)
def send(msg):
    token=os.environ['TELEGRAM_BOT_TOKEN']; chat=os.environ['TELEGRAM_CHAT_ID']
    req=Request('https://api.telegram.org/bot'+token+'/sendMessage',data=json.dumps({'chat_id':chat,'text':msg[:4000],'link_preview_options':{'is_disabled':True}}).encode(),headers={'Content-Type':'application/json'})
    try:
        with urlopen(req,timeout=30) as r:
            if not json.load(r).get('ok'): raise RuntimeError('Telegram rejected message')
    except Exception: raise RuntimeError('Telegram delivery failed; check credentials and connectivity') from None

def run(dry=False, fixture=None, db='radar.sqlite'):
    con=sqlite3.connect(db); con.execute('CREATE TABLE IF NOT EXISTS sent (id TEXT PRIMARY KEY, sent_at TEXT DEFAULT CURRENT_TIMESTAMP)'); con.commit()
    vacancies=json.loads(Path(fixture).read_text()) if fixture else collect()
    for v in vacancies:
        result=classify(v['title'],v['description'],v.get('band',''))
        if not result or con.execute('SELECT 1 FROM sent WHERE id=?',(v['id'],)).fetchone(): continue
        priority,reason,quote=result
        msg=f"{priority} | {v['title']}\nКомпания: {v['company']}\n{reason}\nТребования: {quote}\n{v['url']}"
        role=direction(v['title'],v['description'])
        msg=role+'\n'+msg
        if role=='Product Analytics':
            skills=[name for name,pattern in SKILLS.items() if re.search(pattern,v['description'],re.I)]
            msg+='\nУпомянутые навыки (не обязательно обязательные): '+(', '.join(skills) or 'не выявлены')
        if dry: print(msg+'\n---')
        else:
            send(msg); con.execute('INSERT INTO sent(id) VALUES (?)',(v['id'],)); con.commit(); time.sleep(1.1)
    con.close()
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--dry-run',action='store_true'); p.add_argument('--fixture'); p.add_argument('--db',default='radar.sqlite'); a=p.parse_args(); run(a.dry_run,a.fixture,a.db)
