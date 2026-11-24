import json,httpx
from agent import invoke,openai_run,claude_run
from scripts.connector import generate

def test_invalid_tool():
    with httpx.Client(transport=httpx.MockTransport(lambda r: (_ for _ in ()).throw(AssertionError('unexpected request')))) as c:
        assert 'error' in invoke('create_ticket',{},'http://localhost','token',c)
def test_openai_tool_roundtrip():
    calls=[]
    def handler(r):
        body=json.loads(r.content);calls.append(body)
        if len(calls)==1: return httpx.Response(200,json={'choices':[{'message':{'role':'assistant','content':None,'tool_calls':[{'id':'x','type':'function','function':{'name':'search_knowledge','arguments':'{"q":"vpn"}'}}]}}]})
        assert body['messages'][-1]['role']=='tool';return httpx.Response(200,json={'choices':[{'message':{'content':'Use policy.'}}]})
    with httpx.Client(transport=httpx.MockTransport(handler)) as c: assert openai_run('vpn',lambda n,a:{'hits':['policy']},c,'fake','fake')=='Use policy.'
def test_claude_tool_roundtrip():
    calls=[]
    def handler(r):
        body=json.loads(r.content);calls.append(body)
        if len(calls)==1: return httpx.Response(200,json={'content':[{'type':'tool_use','id':'x','name':'search_knowledge','input':{'q':'vpn'}}]})
        assert body['messages'][-1]['content'][0]['tool_use_id']=='x';return httpx.Response(200,json={'content':[{'type':'text','text':'Use policy.'}]})
    with httpx.Client(transport=httpx.MockTransport(handler)) as c: assert claude_run('vpn',lambda n,a:{'hits':['policy']},c,'fake','fake')=='Use policy.'
def test_connector():
    d=generate('example.invalid','00000000-0000-0000-0000-000000000000','api://example/Tickets.Access');assert d['swagger']=='2.0' and '/tickets' in d['paths'] and not any('/decision' in p for p in d['paths'])
