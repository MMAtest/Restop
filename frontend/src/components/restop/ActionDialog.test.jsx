import React,{act} from 'react';
import {createRoot} from 'react-dom/client';
import ActionDialog from './ActionDialog';
let host,root;const onResolve=jest.fn();
const danger={config:{title:'Supprimer le produit ?',description:'Effacement définitif',dangerous:true,requireText:'SUPPRIMER',confirmLabel:'Supprimer définitivement'}};
const archive={config:{title:'Archiver Tomates ?',description:'Déplacement vers les archives',askReason:true,confirmLabel:'Archiver'}};
const change=(el,value)=>{const set=Object.getOwnPropertyDescriptor(el.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype,'value').set;set.call(el,value);el.dispatchEvent(new Event('input',{bubbles:true}))};
beforeEach(()=>{global.IS_REACT_ACT_ENVIRONMENT=true;host=document.createElement('div');document.body.appendChild(host);root=createRoot(host)});
afterEach(async()=>{await act(async()=>root.unmount());host.remove();jest.clearAllMocks()});

test('une suppression est bloquée tant que SUPPRIMER n’a pas été saisi',async()=>{
 await act(async()=>root.render(<ActionDialog request={danger} onResolve={onResolve}/>));
 const dialog=host.querySelector('[role="dialog"]');
 expect(dialog?.getAttribute('aria-modal')).toBe('true');
 const confirm=[...host.querySelectorAll('button')].find(b=>b.textContent==='Supprimer définitivement');
 expect(confirm.disabled).toBe(true);
 await act(async()=>change(host.querySelector('input'),'SUPPRIMER'));
 expect(confirm.disabled).toBe(false);
 await act(async()=>confirm.click());
 expect(onResolve).toHaveBeenCalledWith({confirmed:true,reason:null});
});

test('archiver propose un motif facultatif et renvoie son texte',async()=>{
 await act(async()=>root.render(<ActionDialog request={archive} onResolve={onResolve}/>));
 const textarea=host.querySelector('textarea');
 await act(async()=>change(textarea,'  Retiré du menu  '));
 await act(async()=>[...host.querySelectorAll('button')].find(b=>b.textContent==='Archiver').click());
 expect(onResolve).toHaveBeenCalledWith({confirmed:true,reason:'Retiré du menu'});
});

test('Escape annule sans effectuer de suppression',async()=>{
 await act(async()=>root.render(<ActionDialog request={danger} onResolve={onResolve}/>));
 await act(async()=>window.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true})));
 expect(onResolve).toHaveBeenCalledWith({confirmed:false});
});
