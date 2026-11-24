'use strict';
const el=id=>document.getElementById(id);
const value=id=>el(id).value.trim();
const key=()=>{el('idem').value=crypto.randomUUID()};
key();el('newkey').addEventListener('click',key);
async function call(path,method='GET',data,idem){
 const headers={Authorization:'Bearer '+value('token')};
 if(data!==undefined)headers['Content-Type']='application/json';
 if(idem)headers['Idempotency-Key']=idem;
 const r=await fetch(path,{method,headers,body:data===undefined?undefined:JSON.stringify(data),cache:'no-store',redirect:'error'});
 const result=await r.json();if(!r.ok)throw Error('HTTP '+r.status+': '+JSON.stringify(result));return result;
}
async function show(id,fn){const out=el(id);out.textContent='Working…';try{const result=await fn();out.textContent=JSON.stringify(result,null,2);return result}catch(e){out.textContent=String(e);}}
function submit(id,fn){el(id).addEventListener('submit',async e=>{e.preventDefault();const b=e.submitter;b.disabled=true;try{await fn()}finally{b.disabled=false}})}
submit('chat',()=>show('answer',()=>call('/chat','POST',{question:value('question'),provider:value('provider'),allow_provider_egress:el('consent').checked})));
submit('create',async()=>{const body={category:value('category'),summary:value('summary')};if(!confirm('Create synthetic '+body.category+' ticket: '+body.summary+'?'))return;const r=await show('ticketout',()=>call('/tickets','POST',body,value('idem')));if(r){el('ticket').value=r.ticket_id;if(r.approval_id)el('approval').value=r.approval_id;}});
submit('lookup',()=>show('ticketout',()=>call('/tickets/'+encodeURIComponent(value('ticket')))));
submit('review',()=>show('reviewout',()=>call('/approvals/'+encodeURIComponent(value('approval')))));
for(const decision of ['approve','reject'])el(decision).addEventListener('click',async()=>{const id=value('approval');if(!id||!confirm(decision+' '+id+'?'))return;await show('reviewout',()=>call('/approvals/'+encodeURIComponent(id)+'/decision','POST',{decision}));});
