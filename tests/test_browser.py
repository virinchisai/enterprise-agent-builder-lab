from fastapi.testclient import TestClient
from app import app
import pytest
@pytest.fixture
def client(monkeypatch,tmp_path):
    monkeypatch.setenv('AUTH_MODE','demo'); monkeypatch.setenv('LAB_DB',str(tmp_path/'lab.db')); monkeypatch.delenv('ENABLE_PROVIDER_CHAT',raising=False)
    return TestClient(app)
H={'Authorization':'Bearer demo-alice'}
def test_ui(client):
    r=client.get('/'); assert r.status_code==200 and 'IT support workspace' in r.text and 'frame-ancestors' in r.headers['content-security-policy']; assert client.get('/ui/app.js').status_code==200

def test_chat_local(client):
    r=client.post('/chat',headers=H,json={'question':'vpn'}); assert r.status_code==200 and r.json()['evidence']['hits']

def test_chat_auth(client): assert client.post('/chat',json={'question':'vpn'}).status_code==401

def test_chat_denied(client): assert client.post('/chat',headers=H,json={'question':'vpn','provider':'openai','allow_provider_egress':True}).status_code==403

def test_chat_no_consent(client,monkeypatch):
    monkeypatch.setenv('ENABLE_PROVIDER_CHAT','true'); assert client.post('/chat',headers=H,json={'question':'vpn','provider':'claude'}).status_code==403

def test_provider_mock(client,monkeypatch):
    import agent
    monkeypatch.setenv('ENABLE_PROVIDER_CHAT','true'); monkeypatch.setenv('OPENAI_API_KEY','mock'); monkeypatch.setenv('OPENAI_MODEL','mock')
    def fake(q,run,c,key,model):
        assert run('search_knowledge',{'q':'vpn'})['hits']; assert 'error' in run('get_ticket',{'ticket_id':'T-123'}); return 'Mock grounded answer'
    monkeypatch.setattr(agent,'openai_run',fake)
    assert client.post('/chat',headers=H,json={'question':'vpn','provider':'openai','allow_provider_egress':True}).json()['answer']=='Mock grounded answer'
