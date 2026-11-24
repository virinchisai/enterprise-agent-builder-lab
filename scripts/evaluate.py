"""Synthetic HTTP acceptance checks. Run against a disposable loopback demo instance."""
import os,uuid,json,httpx
from urllib.parse import urlsplit
base=os.getenv('LAB_API','http://127.0.0.1:8000').rstrip('/')
if urlsplit(base).hostname not in ('127.0.0.1','localhost'): raise SystemExit('Evaluation requires loopback synthetic demo')
results=[]
with httpx.Client(base_url=base,timeout=10,follow_redirects=False) as c:
 def check(name,condition):
    results.append({'case':name,'passed':bool(condition)}); assert condition,name
 def h(user='alice',key=None): return {'Authorization':'Bearer demo-'+user,**({'Idempotency-Key':key} if key else {})}
 check('UI serves',c.get('/').status_code==200)
 check('health',c.get('/health').status_code==200)
 check('unauthenticated blocked',c.get('/knowledge?q=vpn').status_code==401)
 check('local grounded chat',bool(c.post('/chat',headers=h(),json={'question':'vpn'}).json()['evidence']['hits']))
 check('no evidence',c.get('/knowledge?q=xyzzy',headers=h()).json()['status']=='no_evidence')
 key=uuid.uuid4().hex; data={'category':'access','summary':'Synthetic evaluation access request'}
 a=c.post('/tickets',headers=h(key=key),json=data).json(); check('approval pending',a['status']=='pending_approval')
 b=c.post('/tickets',headers=h(key=key),json=data).json(); check('idempotent replay',b['replayed'] and b['ticket_id']==a['ticket_id'])
 t='/tickets/'+a['ticket_id']; p='/approvals/'+a['approval_id']+'/decision'
 check('cross-user isolation',c.get(t,headers=h('bob')).status_code==404)
 check('ordinary user cannot approve',c.post(p,headers=h(),json={'decision':'approve'}).status_code==403)
 check('reviewer decision',c.post(p,headers=h('reviewer'),json={'decision':'approve'}).status_code==200)
 check('approval replay denied',c.post(p,headers=h('reviewer'),json={'decision':'approve'}).status_code==409)
 check('ticket now open',c.get(t,headers=h()).json()['status']=='open')
print(json.dumps({'passed':sum(x['passed'] for x in results),'total':len(results),'cases':results},indent=2))
