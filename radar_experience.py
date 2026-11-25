"""Extract candidate experience, not company age or benefit durations."""
import re

WORDS={'один':1,'одного':1,'одной':1,'два':2,'двух':2,'три':3,'трех':3,'четыре':4,'четырех':4,'пять':5,'пяти':5,'шесть':6,'шести':6,'семь':7,'семи':7,'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7}
NUM=r'(?:\d+(?:[.,]\d+)?|'+'|'.join(WORDS)+r')'
DURATION=re.compile(r'(?<![\w.,])(?P<n>'+NUM+r')\s*(?:(?:[-–—−]|до|to)\s*'+NUM+r'\s*)?\+?\s*(?P<unit>лет|год(?:а|ов)?|years?|yrs?|месяц(?:а|ев)?|months?)\b')
LEFT=re.compile(r'(?:опыт(?:а|ом)?(?:\s+\w+){0,7}|стаж(?:а)?(?:\s+\w+){0,5}|работал[аи]?(?:\s+\w+){0,6}|работаете(?:\s+\w+){0,6}|experience(?:\s+\w+){0,5}|worked(?:\s+\w+){0,6}|at least|minimum|не менее|не меньше)\s*[:—-]?\s*$',re.I)
RIGHT=re.compile(r'^\s*(?:опыта\b|стажа\b|of\s+(?:relevant\s+|professional\s+|work\s+)?experience\b|experience\b|работал[аи]?\b|работаете\b|развивал[аи]?\b|управлял[аи]?\b|занимал[аи]сь\b)',re.I)
OPTIONAL=re.compile(r'^\s*(?:опыта\s*)?(?:буд(?:ет|ут)|является)\s+(?:плюсом|преимуществом)|^\s*(?:of experience\s+)?(?:is\s+)?preferred\b',re.I)
def experience(text):
    text=str(text or '').lower().replace('ё','е')
    found=[]; optional=False
    for clause in re.split(r'(?<!\d)\.(?!\d)|[;\n!?•]|\.\s+|,\s*(?=(?:опыт|работал|желательно|компания|мы\b))',text):
        clause=re.sub(r'\s+',' ',clause).strip()
        for m in DURATION.finditer(clause):
            left=clause[max(0,m.start()-110):m.start()]
            right=clause[m.end():m.end()+90]
            if re.search(r'(?:компания|на рынке|наша история|company|since|основан[ао]?|существует|работаем|лет на рынке)\s*(?:уже\s*)?$',left) or re.match(r'\s*(?:на рынке|компании|company history|in business)',right): continue
            # A duration must be tied to a candidate experience phrase, or marked optional.
            optional_here=bool(OPTIONAL.search(right) or re.search(r'(?:желательно|будет плюсом|nice to have|preferred)\s*[:—-]?\s*(?:опыт\s*(?:работы\s*)?)?(?:от\s*)?$',left))
            if optional_here:
                optional=True
                continue
            if not (LEFT.search(left) or RIGHT.search(right)): continue
            n=m.group('n'); years=WORDS[n] if n in WORDS else float(n.replace(',','.'))
            if m.group('unit').startswith(('месяц','month')): years/=12
            if years>2 or (years==2 and re.search(r'(?:(?<!не )более|свыше|(?<!не )больше|more than|over)\s*$',left)):
                return 'REVIEW_3_PLUS',m.group(0)
            found.append(years)
    if found: return 'POSSIBLE_MATCH',f'{max(found):g} years'
    if re.search(r'без опыта|опыт не обязателен|no experience required',text): return 'POSSIBLE_MATCH','0 years'
    return 'UNKNOWN','Optional experience only' if optional else 'No reliable evidence'


HEADER=re.compile(r'^(?:опыт(?: работы)?\s*[:—-]?\s*)?(?:от|не менее|не меньше|более|больше|свыше|at least|minimum|more than|over)\s+|^(?:без опыта|no experience required)$',re.I)
def header_experience(chunks, title):
    """Use only exact duration labels near the actual vacancy heading."""
    clean=[re.sub(r'\s+',' ',str(c)).strip().lower().replace('ё','е') for c in chunks if str(c).strip()]
    title=re.sub(r'\s+',' ',title).strip().lower().replace('ё','е')
    start=next((i for i,c in enumerate(clean) if c==title),None)
    if start is None: return 'UNKNOWN','No verified heading'
    found=[]
    for i in range(start+1,min(start+13,len(clean))):
        for width in range(1,4):
            label=' '.join(clean[i:i+width])
            if len(label)>75: continue
            if label in ('без опыта','no experience required'): found.append(('POSSIBLE_MATCH','0 years')); continue
            if not HEADER.search(label): continue
            m=DURATION.search(label)
            if not m: continue
            # Header labels must contain only a duration or duration range.
            if not re.fullmatch(r'\s*(?:опыт(?: работы)?\s*[:—-]?\s*)?(?:от|не менее|не меньше|более|больше|свыше|at least|minimum|more than|over)\s+'+DURATION.pattern+r'(?:\s+до\s+'+NUM+r'\s+(?:лет|год(?:а|ов)?|years?))?\s*',label,re.I): continue
            found.append(experience('опыт '+label))
    return combine_experience(*found)

def combine_experience(*results):
    for state,evidence in results:
        if state=='REVIEW_3_PLUS': return state,evidence
    valid=[(state,evidence) for state,evidence in results if state=='POSSIBLE_MATCH']
    if valid:
        return max(valid,key=lambda x:float(x[1].split()[0]) if re.fullmatch(r'\d+(?:\.\d+)? years',x[1]) else -1)
    return 'UNKNOWN','No reliable evidence'

def requirements_text(chunks):
    """Preserve bullet boundaries; exclude optional and benefits sections when identifiable."""
    start=re.compile(r'^(?:мы\s+ждем,?\s+что\s+вы|что\s+мы\s+ждем|что\s+ожидаем|наши\s+ожидания|требования(?: к кандидату)?|что\s+нужно|requirements|what you bring|qualifications)\s*[:.!]?$')
    end=re.compile(r'^(?:будет плюсом|будет преимуществом|бенефиты|условия|мы предлагаем|что мы предлагаем|узнать больше|nice to have|benefits|what we offer)')
    cleaned=[re.sub(r'\s+',' ',str(c)).strip() for c in chunks if str(c).strip()]
    for i,chunk in enumerate(cleaned):
        if start.search(chunk.lower().replace('ё','е')):
            selected=[]
            for value in cleaned[i+1:]:
                if end.search(value.lower().replace('ё','е')): break
                selected.append(value)
            if selected: return '\n'.join(selected)
    return '\n'.join(cleaned)
