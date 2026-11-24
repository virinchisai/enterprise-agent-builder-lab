"""Generate Swagger 2.0 connector with explicit tenant/scope/host configuration."""
import argparse,json,re
from pathlib import Path

def generate(host,tenant,scope):
    if not re.fullmatch(r'[a-zA-Z0-9.-]+',host) or host in ['localhost','127.0.0.1']: raise ValueError('Use reachable HTTPS DNS name')
    if not re.fullmatch(r'[0-9a-fA-F-]{36}',tenant): raise ValueError('Tenant GUID required')
    def op(id,summary,params,properties):
        return {'operationId':id,'summary':summary,'description':summary,'parameters':params,'responses':{'200':{'description':'Success','schema':{'type':'object','properties':properties}},'default':{'description':'Error','schema':{'type':'object','properties':{'detail':{'type':'string'}}}}}}
    s={'type':'string'}; path=lambda name:{'name':name,'in':'path','required':True,'type':'string'}
    return {'swagger':'2.0','info':{'title':'Enterprise Agent Builder','version':'2.0'},'host':host,'basePath':'/','schemes':['https'],'consumes':['application/json'],'produces':['application/json'],'securityDefinitions':{'entra':{'type':'oauth2','flow':'accessCode','authorizationUrl':f'https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize','tokenUrl':f'https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token','scopes':{scope:'Access tickets on behalf of the user'}}},'security':[{'entra':[scope]}], 'paths':{
        '/tickets':{'post':op('createTicket','Create a ticket after explicit user confirmation',[{'name':'Idempotency-Key','in':'header','required':True,'type':'string'},{'name':'body','in':'body','required':True,'schema':{'type':'object','required':['category','summary'],'properties':{'category':{'type':'string','enum':['vpn','hardware','access']},'summary':{'type':'string','minLength':5,'maxLength':500}}}}],{'ticket_id':s,'status':s,'approval_id':s,'replayed':{'type':'boolean'}})},
        '/tickets/{ticket_id}':{'get':op('getTicket','Get your own ticket status',[path('ticket_id')],{'id':s,'category':s,'summary':s,'status':s})},
        '/knowledge':{'get':op('searchKnowledge','Search synthetic IT policy',[{'name':'q','in':'query','required':True,'type':'string'}],{'status':s,'hits':{'type':'array','items':{'type':'object','properties':{'source':s,'section':{'type':'integer'},'text':s}}}})},
        '/approvals/{approval_id}':{'get':op('getApproval','Read approval status',[path('approval_id')],{'id':s,'status':s,'ticket':s})}
    }}
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--host',required=True);p.add_argument('--tenant',required=True);p.add_argument('--scope',required=True);p.add_argument('--output',required=True);a=p.parse_args();Path(a.output).write_text(json.dumps(generate(a.host,a.tenant,a.scope),indent=2)+'\n')
