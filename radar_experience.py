"""Extract candidate experience, not company age or benefit durations."""
import re

WORDS={'один':1,'одного':1,'одной':1,'два':2,'двух':2,'три':3,'трех':3,'четыре':4,'четырех':4,'пять':5,'пяти':5,'шесть':6,'шести':6,'семь':7,'семи':7,'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7}
NUM=r'(?:\d+(?:[.,]\d+)?|'+'|'.join(WORDS)+r')'
DURATION=re.compile(r'(?<![\w.,])(?P<n>'+NUM+r')\s*(?:(?:[-–—−]|до|to)\s*'+NUM+r'\s*)?\+?\s*(?P<unit>лет|год(?:а|ов)?|years?|yrs?|месяц(?:а|ев)?|months?)\b')
LEFT=re.compile(r'(?:опыт(?:а|ом)?(?:\s+\w+){0,7}|стаж(?:а)?(?:\s+\w+){0,5}|работал[аи]?(?:\s+\w+){0,6}|работаете(?:\s+\w+){0,6}|experience(?:\s+\w+){0,5}|worked(?:\s+\w+){0,6}|at least|minimum)\s*[:—-]?\s*$',re.I)
RIGHT=re.compile(r'^\s*(?:опыта\b|стажа\b|of\s+(?:relevant\s+|professional\s+|work\s+)?experience\b|experience\b)',re.I)
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
            if years>2 or (years==2 and re.search(r'(?:более|свыше|больше|more than|over)\s*$',left)):
                return 'REVIEW_3_PLUS',m.group(0)
            found.append(years)
    if found: return 'POSSIBLE_MATCH',f'{max(found):g} years'
    if re.search(r'без опыта|опыт не обязателен|no experience required',text): return 'POSSIBLE_MATCH','0 years'
    return 'UNKNOWN','Optional experience only' if optional else 'No reliable evidence'
