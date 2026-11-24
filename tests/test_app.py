import pytest
from fastapi.testclient import TestClient
from app import app
@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setenv('LAB_DB',str(tmp_path/'test.db')); monkeypatch.setenv('AUTH_MODE','demo')
    return TestClient(app)
def headers(who='alice',key='request-001'): return {'Authorization':'Bearer demo-'+who,'Idempotency-Key':key}
def create(c,category='vpn',who='alice',key='request-001'): return c.post('/tickets',headers=headers(who,key),json={'category':category,'summary':'Test issue for support'})
def test_health(client): assert client.get('/health').status_code==200
def test_auth(client): assert client.get('/knowledge?q=vpn').status_code==401
def test_replay(client):
    a=create(client).json(); b=create(client).json(); assert a['ticket_id']==b['ticket_id'] and b['replayed']
def test_conflict(client):
    create(client); assert create(client,'hardware').status_code==409
def test_isolation(client):
    t=create(client).json()['ticket_id']; assert client.get('/tickets/'+t,headers=headers('bob')).status_code==404
def test_validation(client): assert create(client,'invalid').status_code==422
def test_extra(client): assert client.post('/tickets',headers=headers(),json={'category':'vpn','summary':'Test issue','owner':'bob'}).status_code==422
def test_approval(client):
    a=create(client,'access').json(); assert a['status']=='pending_approval'; url='/approvals/'+a['approval_id']+'/decision'
    assert client.post(url,headers=headers(),json={'decision':'approve'}).status_code==403
    assert client.post(url,headers=headers('reviewer'),json={'decision':'approve'}).status_code==200
    assert client.post(url,headers=headers('reviewer'),json={'decision':'approve'}).status_code==409
    assert client.get('/tickets/'+a['ticket_id'],headers=headers()).json()['status']=='open'
def test_reject(client):
    a=create(client,'access').json(); assert client.post('/approvals/'+a['approval_id']+'/decision',headers=headers('reviewer'),json={'decision':'reject'}).status_code==200
    assert client.get('/tickets/'+a['ticket_id'],headers=headers()).json()['status']=='rejected'
def test_approval_isolation(client):
    a=create(client,'access').json(); assert client.get('/approvals/'+a['approval_id'],headers=headers('bob')).status_code==404

def test_knowledge(client): assert client.get('/knowledge?q=vpn',headers=headers()).json()['hits']
def test_no_evidence(client): assert client.get('/knowledge?q=xyzzy',headers=headers()).json()['status']=='no_evidence'
def test_metrics(client): assert client.get('/metrics',headers=headers()).status_code==403
def test_entra_fails_closed(client,monkeypatch):
    monkeypatch.setenv('AUTH_MODE','entra'); monkeypatch.delenv('ENTRA_TENANT_ID',raising=False); assert client.get('/knowledge?q=vpn',headers=headers()).status_code==503
