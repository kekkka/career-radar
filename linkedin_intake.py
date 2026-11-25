"""Conservative LinkedIn intake: only public identifiers and normalized vacancy facts."""
import json
import re

def linkedin_records(raw, companies):
    if not raw or len(raw)>20000:
        return []
    try: items=json.loads(raw)
    except (ValueError,TypeError): return []
    if not isinstance(items,list) or len(items)>30: return []
    result=[]
    for item in items:
        if not isinstance(item,dict) or set(item)!={'id','company','title','years'}: continue
        jid,company,title,years=(item[k] for k in ('id','company','title','years'))
        if not isinstance(jid,str) or not re.fullmatch(r'\d{5,20}',jid): continue
        if not isinstance(company,str) or company not in companies: continue
        if not isinstance(title,str) or not 3<=len(title)<=180 or re.search(r'[\r\n@<>]|https?://',title,re.I): continue
        if isinstance(years,bool) or not isinstance(years,(int,float)) or not 0<=years<=2: continue
        result.append((company,title,'https://www.linkedin.com/jobs/view/'+jid,years))
    return result
