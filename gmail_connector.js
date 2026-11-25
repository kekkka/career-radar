// Career Radar Gmail connector. Copy this entire file into Code.gs.
// No message bodies, email IDs, addresses, tracking URLs or tokens are sent to GitHub.
const CONFIG={
  owner:'kekkka',repo:'career-radar',workflow:'career-monitor.yml',branch:'main',
  query:'from:linkedin.com newer_than:7d {subject:job subject:jobs subject:вакансии subject:вакансия subject:alert} -in:spam -in:trash'
};
const EMPLOYERS={
 'Авито':['авито','avito'],'Яндекс':['яндекс','yandex'],'Самокат':['самокат','samokat'],
 'ВкусВилл':['вкусвилл','вкус вилл','vkusvill'],'Dodo Brands':['dodo brands','додо брандс','dodo engineering'],
 'Т-Банк':['т-банк','т банк','t-bank','tbank','тинькофф','tinkoff'],
 'Точка':['точка','банк точка','tochka'],'Авиасейлс':['авиасейлс','aviasales'],
 'Циан':['циан','cian'],'ЕАПТЕКА':['еаптека','eapteka','сбер еаптека'],
 'Skyeng':['skyeng','скайенг'],'Кинопоиск':['кинопоиск','kinopoisk'],
 'START':['start','start video'],'Wink':['wink','винк']
};
function norm(s){return String(s||'').replace(/\s+/g,' ').trim().toLowerCase().replace(/ё/g,'е');}
function decodeHtml(s){
 return String(s||'').replace(/&(?:amp|quot|apos|lt|gt|nbsp|#\d+|#x[0-9a-f]+);/gi,function(x){
  const named={'&amp;':'&','&quot;':'"','&apos;':"'",'&lt;':'<','&gt;':'>','&nbsp;':' '};
  if(named[x.toLowerCase()]!==undefined)return named[x.toLowerCase()];
  const n=x.slice(2,-1);const code=n[0].toLowerCase()==='x'?parseInt(n.slice(1),16):Number(n);
  return Number.isInteger(code)&&code>0&&code<=0x10ffff?String.fromCodePoint(code):' ';
 });
}
function jobId(href){
 const m=decodeHtml(href).match(/^https:\/\/(?:www\.)?linkedin\.com\/jobs\/view\/(?:[a-z0-9-]+-)?(\d{5,20})(?:[/?#]|$)/i);
 return m?m[1]:null;
}
function role(title){
 const t=norm(title).replace(/[-–—]/g,' ');
 if(!t||t.length>180||/[\r\n@<>]|https?:\/\//i.test(title))return false;
 if(/\b(?:senior|lead|head|principal|staff|bi|developer|designer)\b|старший|ведущий|руководитель|разработчик|дизайнер|project manager|менеджер проектов|business analyst|бизнес аналитик|system analyst|системный аналитик|data analyst|аналитик данных|product marketing|маркетолог/.test(t))return false;
 return /product manager|product owner|product intern|product management intern|product analyst|product analytics|продакт|продуктов\w* менеджер|менеджер(?:ы)? продукта|менеджер по продукт|менеджер по развитию продукта|продуктов[а-я]* аналитик|аналитик продукта|владелец продукта|\bapm\b/.test(t);
}
function companyOf(lines){
 const found=new Set();
 for(const line of lines){
  const s=norm(line).replace(/^(?:company|employer|компания|работодатель)\s*:\s*/,'');
  for(const [name,aliases] of Object.entries(EMPLOYERS))if(aliases.includes(s))found.add(name);
 }
 return found.size===1?[...found][0]:null;
}
// Only explicit required experience labels count; no inference from "Junior"/"Middle".
function yearsOf(lines){
 const matches=[];
 for(const line of lines){
  const s=norm(line);
  if(/желательно|плюсом|преимуществом|preferred|nice to have|optional/.test(s))continue;
  if(/^(?:без опыта|no experience required)$/.test(s)){matches.push(0);continue;}
  const m=s.match(/^(?:(?:опыт(?: работы)?|стаж|experience|required experience)\s*[:—-]?\s*)(?:(от|не менее|минимум|at least|minimum|более|больше|more than|over)\s+)?(\d+(?:[.,]\d+)?)\s*(?:[-–—]\s*\d+(?:[.,]\d+)?\s*)?\+?\s*(лет|год(?:а|ов)?|years?|yrs?|месяц(?:а|ев)?|months?)$/i);
  const en=s.match(/^(?:(at least|minimum|more than|over)\s+)?(\d+(?:[.,]\d+)?)\s*\+?\s*(years?|months?)\s+of\s+(?:relevant\s+|professional\s+|work\s+)?experience(?:\s+required)?$/i);
  const hit=m||en;if(!hit)continue;
  let n=Number(hit[2].replace(',','.'));if(/^(месяц|month)/i.test(hit[3]))n/=12;
  if(/более|больше|more than|over/.test(hit[1]||'')&&n>=2)n=3;
  matches.push(n);
 }
 return matches.length?Math.max(...matches):null;
}
// Small bounded HTML tree. Never follows redirects or requests LinkedIn URLs.
function parseTree(html){
 const root={tag:'root',children:[],parent:null,href:''};let current=root;
 const voids=new Set(['area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr']);
 const pieces=String(html||'').replace(/<!--[\s\S]*?-->/g,'').replace(/<(script|style)\b[^>]*>[\s\S]*?<\/\1\s*>/gi,'').match(/<[^>]*>|[^<]+/g)||[];
 if(pieces.length>100000)return root;
 for(const token of pieces){
  if(token[0]!=='<'){current.children.push(decodeHtml(token));continue;}
  const end=token.match(/^<\/\s*([a-z0-9]+)\s*>/i);
  if(end){let p=current;while(p.parent&&p.tag!==end[1].toLowerCase())p=p.parent;if(p.parent)current=p.parent;continue;}
  const start=token.match(/^<\s*([a-z0-9]+)/i);if(!start)continue;
  const tag=start[1].toLowerCase();
  const href=token.match(/\bhref\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))/i);
  const node={tag,children:[],parent:current,href:href?(href[1]||href[2]||href[3]||''):''};current.children.push(node);
  if(!voids.has(tag)&&!token.endsWith('/>'))current=node;
 }
 return root;
}
function walk(node,fn){if(typeof node==='string')return;fn(node);for(const c of node.children)walk(c,fn);}
function rawText(node){return typeof node==='string'?node:node.children.map(rawText).join(' ');}
function linesOf(node){
 const parts=[];
 function visit(n){
  if(typeof n==='string'){parts.push(n);return;}
  const block=/^(?:div|p|li|tr|td|th|br|h[1-6]|section|article)$/.test(n.tag);
  if(block)parts.push('\n');for(const c of n.children)visit(c);if(block)parts.push('\n');
 }
 visit(node);return parts.join(' ').split(/\n/).map(s=>s.replace(/\s+/g,' ').trim()).filter(Boolean);
}
function parseAlert(html){
 const result={records:[],held:0,ids:0};
 if(typeof html!=='string'||html.length>2000000)return result;
 const root=parseTree(html),anchors=[];
 walk(root,n=>{if(n.tag==='a'&&jobId(n.href)&&role(rawText(n).trim()))anchors.push(n);});
 const ids=new Set(),eligible=new Map(),conflicts=new Set();
 for(const a of anchors){
  const id=jobId(a.href);ids.add(id);
  const title=rawText(a).replace(/\s+/g,' ').trim();
  // Find the smallest self-contained card, not an email-wide association.
  for(let card=a.parent;card&&card.tag!=='root';card=card.parent){
   if(!/^(?:li|tr|td|table|div|section|article|p)$/.test(card.tag))continue;
   const cardText=rawText(card);if(cardText.length>1600)break;
   const links=new Set();let ambiguous=false;
   walk(card,n=>{if(n.tag==='a'&&n.href){const j=jobId(n.href);if(j)links.add(j);else if(/linkedin\.com\/(?:comm\/)?jobs\/|linkedin\.com\/redir|lnkd\.in\//i.test(n.href))ambiguous=true;}});
   if(ambiguous||links.size!==1||!links.has(id))break;
   const lines=linesOf(card);
   if(lines.length>20)break;
   const company=companyOf(lines);
   if(!company)continue;
   if(/вакансия\s+(?:закрыта|в архиве)|no longer accepting|job is no longer available/i.test(cardText)){conflicts.add(id);break;}
   const years=yearsOf(lines);
   if(years===null)continue;
   if(years>2){conflicts.add(id);break;}
   const record={id,company,title,years};
   if(eligible.has(id)&&JSON.stringify(eligible.get(id))!==JSON.stringify(record))conflicts.add(id);
   else eligible.set(id,record);
   // Do not stop at a shorter card if its enclosing card contains a stricter requirement.
  }
 }
 for(const [id,r] of eligible)if(!conflicts.has(id))result.records.push(r);
 result.ids=ids.size;result.held=ids.size-result.records.length;return result;
}
function collectLinkedIn(){
 const all=new Map(),conflicts=new Set();let messages=0,ids=0,held=0;
 for(const thread of GmailApp.search(CONFIG.query,0,100)){
  for(const msg of thread.getMessages()){
   if(!/@(?:[a-z0-9-]+\.)*linkedin\.com(?:>|$)/i.test(msg.getFrom().trim()))continue;
   if(!/job|ваканси|alert/i.test(msg.getSubject())||Date.now()-msg.getDate().getTime()>7*86400000)continue;
   messages++;const p=parseAlert(msg.getBody());ids+=p.ids;held+=p.held;
   for(const record of p.records){
    if(all.has(record.id)&&JSON.stringify(all.get(record.id))!==JSON.stringify(record))conflicts.add(record.id);
    else all.set(record.id,record);
   }
  }
 }
 const records=[...all.values()].filter(r=>!conflicts.has(r.id));
 // Logs stay in Apps Script; no mailbox metadata is sent.
 console.log('Messages: '+messages+' | Candidate IDs: '+ids+' | Held: '+held+' | Eligible: '+records.length);
 return records.slice(0,30);
}
function dispatchLinkedInVacancies(records,sendNotifications){
 if(!Array.isArray(records)||records.length>30)throw new Error('Invalid batch');
 const token=PropertiesService.getScriptProperties().getProperty('GITHUB_TOKEN');
 if(!token)throw new Error('GITHUB_TOKEN not found');
 const url='https://api.github.com/repos/'+CONFIG.owner+'/'+CONFIG.repo+'/actions/workflows/'+CONFIG.workflow+'/dispatches';
 const response=UrlFetchApp.fetch(url,{method:'post',contentType:'application/json',headers:{Authorization:'Bearer '+token,Accept:'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'},payload:JSON.stringify({ref:CONFIG.branch,inputs:{send_notifications:String(sendNotifications),linkedin_only:'true',linkedin_records:JSON.stringify(records)}}),muteHttpExceptions:true});
 const status=response.getResponseCode();console.log('GitHub HTTP status: '+status);
 if(status!==204&&status!==200)throw new Error('GitHub dispatch failed: '+status);
}
function monitorLinkedIn(){
 const lock=LockService.getScriptLock();if(!lock.tryLock(1000))return;
 try{const records=collectLinkedIn();if(records.length)dispatchLinkedInVacancies(records,true);else console.log('No confirmed vacancies; nothing sent.');}
 finally{lock.releaseLock();}
}
function testLinkedInParser(){collectLinkedIn();console.log('PARSER TEST COMPLETED');}
function testGmailBridge(){dispatchLinkedInVacancies([],false);console.log('GMAIL BRIDGE TEST PASSED');}
function installHourlyMonitor(){
 for(const t of ScriptApp.getProjectTriggers())if(t.getHandlerFunction()==='monitorLinkedIn')ScriptApp.deleteTrigger(t);
 ScriptApp.newTrigger('monitorLinkedIn').timeBased().everyHours(1).create();
 console.log('HOURLY MONITOR INSTALLED');
}
function testFixtures(){
 const card=(id,title,company,exp)=>'<li><a href="https://www.linkedin.com/jobs/view/'+id+'?trk=private">'+title+'</a><div>'+company+'</div><div>'+exp+'</div></li>';
 const check=(condition,label)=>{if(!condition)throw new Error('Fixture failed: '+label);};
 let r=parseAlert('<ul>'+card('123456','Junior Product Manager','Яндекс','Опыт от 2 лет')+card('123457','Product Analyst','Циан','Опыт от 3 лет')+'</ul>');
 check(r.records.length===1&&r.records[0].id==='123456'&&r.records[0].years===2,'isolated cards');
 check(parseAlert(card('123458','Product Manager','Авито','Москва')).records.length===0,'unknown experience');
 check(parseAlert(card('123459','Senior Product Manager','Авито','Опыт от 1 года')).records.length===0,'senior exclusion');
 check(parseAlert(card('123460','Product Manager','Other Employer','Опыт от 1 года')).records.length===0,'employer');
 check(parseAlert(card('123461','Product Manager','Авито','Опыт более 2 лет')).records.length===0,'strict threshold');
 check(parseAlert(card('123462','Product Manager','Авито','Опыт от 1 года')+card('123462','Product Manager','Авито','Опыт от 3 лет')).records.length===0,'contradiction');
 check(parseAlert(card('123463','Product Manager','Авито','Опыт от 6 месяцев')).records[0].years===0.5,'months');
 console.log('7 FIXTURES PASSED');
}
function verifyAndScan(){testFixtures();testLinkedInParser();console.log('CONNECTOR READY; hourly trigger uses monitorLinkedIn');}
if(typeof module!=='undefined'&&module.exports){module.exports={parseAlert,testFixtures};}
