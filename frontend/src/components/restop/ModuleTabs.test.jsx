import React,{act} from 'react';
import {createRoot} from 'react-dom/client';
import ModuleTabs from './ModuleTabs';
let host,root;const cb=jest.fn();
beforeEach(()=>{global.IS_REACT_ACT_ENVIRONMENT=true;host=document.createElement('div');document.body.appendChild(host);root=createRoot(host)});
afterEach(async()=>{await act(async()=>root.unmount());host.remove();jest.clearAllMocks()});

test('rubriques accessibles, interdictions de rôles non rendues et état actif signalé',async()=>{
 await act(async()=>root.render(<ModuleTabs label="Gestion" value="stocks" onChange={cb} items={[{id:'stocks',label:'Stocks'},{id:'ocr',label:'OCR'},{id:'admin',label:'Admin',hidden:true}]}/>));
 expect(host.querySelector('[role=group]')?.getAttribute('aria-label')).toBe('Gestion');
 expect(host.textContent).not.toContain('Admin');
 expect(host.querySelector('button[aria-pressed=true]').textContent).toContain('Stocks');
 const ocr=[...host.querySelectorAll('button')].find(b=>b.textContent==='OCR');
 await act(async()=>ocr.click());
 expect(cb).toHaveBeenCalledWith('ocr');
});
