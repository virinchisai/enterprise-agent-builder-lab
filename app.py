"""Enterprise agent lab: local synthetic mode or single-tenant Entra delegated access."""
import os, sqlite3, uuid, hashlib, json, time, hmac, re, logging
from pathlib import Path
from contextlib import contextmanager
from functools import lru_cache
from typing import Literal
import jwt
from fastapi import FastAPI, HTTPException, Depends, Header, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, ConfigDict

app=FastAPI(title='Enterprise Agent Builder Lab',version='2.0.0')
security=HTTPBearer(auto_error=False)
log=logging.getLogger('uvicorn.error')
class Principal(BaseModel):
    subject:str
    reviewer:bool=False

@lru_cache(maxsize=4)
def jwks(tenant):
    return jwt.PyJWKClient(f'https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys', timeout=5)

def identity(cred: HTTPAuthorizationCredentials|None=Depends(security)):
    if not cred: raise HTTPException(401,'Bearer token required')
    mode=os.getenv('AUTH_MODE','demo')
    if mode=='demo':
        users={'demo-alice':Principal(subject='alice'),'demo-bob':Principal(subject='bob'),'demo-reviewer':Principal(subject='reviewer',reviewer=True)}
        if cred.credentials not in users: raise HTTPException(401,'Invalid demo token')
        return users[cred.credentials]
    if mode!='entra': raise HTTPException(503,'Authentication mode misconfigured')
    tenant=os.getenv('ENTRA_TENANT_ID',''); audience=os.getenv('ENTRA_AUDIENCE','')
    if not re.fullmatch(r'[0-9a-fA-F-]{36}',tenant) or not audience: raise HTTPException(503,'Entra configuration missing')
    try:
        token=cred.credentials
        key=jwks(tenant).get_signing_key_from_jwt(token).key
        claims=jwt.decode(token,key,algorithms=['RS256'],audience=audience,issuer=f'https://login.microsoftonline.com/{tenant}/v2.0',options={'require':['exp','iat','iss','aud','tid','oid','scp']})
        if claims['tid'].lower()!=tenant.lower() or claims.get('ver')!='2.0' or not claims['oid']: raise ValueError('tenant or identity mismatch')
    except Exception: raise HTTPException(401,'Invalid access token')
    if 'Tickets.Access' not in claims['scp'].split(): raise HTTPException(403,'Required delegated scope missing')
    return Principal(subject=f"{tenant}:{claims['oid']}",reviewer='Ticket.Reviewer' in claims.get('roles',[]))

@contextmanager
def db():
    conn=sqlite3.connect(os.getenv('LAB_DB','lab.db'),timeout=5); conn.row_factory=sqlite3.Row
    try:
        conn.execute('PRAGMA journal_mode=WAL')
        conn.executescript('''CREATE TABLE IF NOT EXISTS tickets(id TEXT PRIMARY KEY, owner TEXT NOT NULL, idem TEXT NOT NULL, digest TEXT NOT NULL, category TEXT NOT NULL, summary TEXT NOT NULL, status TEXT NOT NULL, UNIQUE(owner,idem));
        CREATE TABLE IF NOT EXISTS approvals(id TEXT PRIMARY KEY, ticket TEXT NOT NULL UNIQUE, owner TEXT NOT NULL, digest TEXT NOT NULL, status TEXT NOT NULL, expires INTEGER NOT NULL, reviewer TEXT);
        CREATE TABLE IF NOT EXISTS audit(id TEXT PRIMARY KEY, actor TEXT NOT NULL, action TEXT NOT NULL, target TEXT NOT NULL, created INTEGER NOT NULL);''')
        yield conn; conn.commit()
    except Exception: conn.rollback(); raise
    finally: conn.close()

def audit(c,actor,action,target):
    c.execute('INSERT INTO audit VALUES(?,?,?,?,?)',(uuid.uuid4().hex,actor,action,target,int(time.time())))
    log.info('event=%s target=%s',action,target)

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def approval_digest(ticket,owner,body_digest):
    secret=os.getenv('APPROVAL_SIGNING_KEY','')
    if not secret:
        if os.getenv('AUTH_MODE','demo')!='demo': raise HTTPException(503,'Approval signing key missing')
        secret='synthetic-local-demo-only'
    return hmac.new(secret.encode(),f'{ticket}:{owner}:{body_digest}'.encode(),hashlib.sha256).hexdigest()

class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
class TicketInput(Strict):
    category:Literal['vpn','access','hardware']
    summary:str=Field(min_length=5,max_length=500)
class Decision(Strict):
    decision:Literal['approve','reject']

@app.get('/health',operation_id='health')
def health(): return {'status':'ok'}
@app.post('/tickets',operation_id='createTicket')
def create_ticket(body:TicketInput,p:Principal=Depends(identity),idempotency_key:str=Header(min_length=8,max_length=128)):
    d=digest(body.model_dump()); owner=p.subject
    with db() as c:
        c.execute('BEGIN IMMEDIATE')
        old=c.execute('SELECT * FROM tickets WHERE owner=? AND idem=?',(owner,idempotency_key)).fetchone()
        if old:
            if old['digest']!=d: raise HTTPException(409,'Idempotency key conflict')
            a=c.execute('SELECT id FROM approvals WHERE ticket=?',(old['id'],)).fetchone()
            return {'ticket_id':old['id'],'status':old['status'],'approval_id':a['id'] if a else None,'replayed':True}
        tid='T-'+uuid.uuid4().hex[:16]; status='pending_approval' if body.category=='access' else 'open'
        c.execute('INSERT INTO tickets VALUES(?,?,?,?,?,?,?)',(tid,owner,idempotency_key,d,body.category,body.summary,status))
        aid=None
        if status=='pending_approval':
            aid='A-'+uuid.uuid4().hex[:16]
            c.execute('INSERT INTO approvals VALUES(?,?,?,?,?,?,NULL)',(aid,tid,owner,approval_digest(tid,owner,d),'pending',int(time.time())+1800))
        audit(c,owner,'ticket_created',tid)
        return {'ticket_id':tid,'status':status,'approval_id':aid,'replayed':False}
@app.get('/tickets/{ticket_id}',operation_id='getTicket')
def get_ticket(ticket_id:str,p:Principal=Depends(identity)):
    with db() as c:
        row=c.execute('SELECT id,category,summary,status FROM tickets WHERE id=? AND owner=?',(ticket_id,p.subject)).fetchone()
        if not row: raise HTTPException(404,'Ticket not found')
        return dict(row)
@app.get('/approvals/{approval_id}',operation_id='getApproval')
def get_approval(approval_id:str,p:Principal=Depends(identity)):
    with db() as c:
        row=c.execute('SELECT a.id,a.owner,a.ticket,a.status,a.expires,t.category,t.summary FROM approvals a JOIN tickets t ON a.ticket=t.id WHERE a.id=?',(approval_id,)).fetchone()
        if not row or (row['owner']!=p.subject and not p.reviewer): raise HTTPException(404,'Approval not found')
        return dict(row)
@app.post('/approvals/{approval_id}/decision',operation_id='decideApproval')
def decide(approval_id:str,body:Decision,p:Principal=Depends(identity)):
    if not p.reviewer: raise HTTPException(403,'Reviewer role required')
    with db() as c:
        c.execute('BEGIN IMMEDIATE')
        a=c.execute('SELECT * FROM approvals WHERE id=?',(approval_id,)).fetchone()
        if not a: raise HTTPException(404,'Approval not found')
        if a['owner']==p.subject: raise HTTPException(403,'Self approval prohibited')
        if a['status']!='pending' or a['expires']<=time.time(): raise HTTPException(409,'Approval unavailable or expired')
        t=c.execute('SELECT * FROM tickets WHERE id=?',(a['ticket'],)).fetchone()
        actual=digest({'category':t['category'],'summary':t['summary']})
        if not hmac.compare_digest(a['digest'],approval_digest(t['id'],t['owner'],actual)): raise HTTPException(409,'Approved action changed')
        status='approved' if body.decision=='approve' else 'rejected'
        c.execute('UPDATE approvals SET status=?,reviewer=? WHERE id=?',(status,p.subject,approval_id))
        c.execute('UPDATE tickets SET status=? WHERE id=?',('open' if status=='approved' else 'rejected',t['id']))
        audit(c,p.subject,'approval_'+status,approval_id)
        return {'approval_id':approval_id,'status':status,'ticket_id':t['id']}
@app.get('/knowledge',operation_id='searchKnowledge')
def knowledge(q:str,p:Principal=Depends(identity)):
    if not 2<=len(q)<=300: raise HTTPException(422,'Query length must be 2–300')
    source=Path(__file__).parent/'knowledge'/'policy.md'
    chunks=source.read_text().split('\n\n'); terms=set(re.findall(r'\w+',q.lower()))
    scored=[(len(terms & set(re.findall(r'\w+',x.lower()))),i,x) for i,x in enumerate(chunks)]
    hits=[{'source':'policy.md','section':i+1,'text':x} for s,i,x in sorted(scored,reverse=True) if s>0][:3]
    return {'hits':hits,'status':'grounded' if hits else 'no_evidence'}
@app.get('/metrics',operation_id='metrics')
def metrics(p:Principal=Depends(identity)):
    if not p.reviewer: raise HTTPException(403,'Reviewer role required')
    with db() as c:
        return {'tickets':c.execute('SELECT COUNT(*) FROM tickets').fetchone()[0], 'audit_events':c.execute('SELECT COUNT(*) FROM audit').fetchone()[0]}
