import React, {act} from 'react';
import {createRoot} from 'react-dom/client';
import AppNavigation from './AppNavigation';

let root,host;const navigate=jest.fn(),suppliers=jest.fn();
async function render(user={role:'patron',full_name:'Camille'}){
 await act(async()=>root.render(<AppNavigation activeTab="overview" onNavigate={navigate} user={user} canOrders={true} onSuppliers={suppliers} onRefresh={()=>{}} onLogout={()=>{}}/>));
}
const click=async name=>{const btn=[...host.querySelectorAll('button')].find(b=>b.textContent.includes(name));expect(btn).toBeTruthy();await act(async()=>btn.click());};
beforeEach(()=>{global.IS_REACT_ACT_ENVIRONMENT=true;host=document.createElement('div');document.body.appendChild(host);root=createRoot(host);window.scrollTo=jest.fn()});
afterEach(async()=>{await act(async()=>root.unmount());host.remove();jest.clearAllMocks()});

test('recherche rapide, filtre et navigation par rôle',async()=>{
 await render();await click('Rechercher une page');
 const dialog=host.querySelector('[role=dialog]');expect(dialog).toBeTruthy();
 expect(dialog.getAttribute('aria-modal')).toBe('true');
 const input=dialog.querySelector('input');
 await act(async()=>{const setter=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;setter.call(input,'Achats');input.dispatchEvent(new Event('input',{bubbles:true}))});
 expect(host.textContent).toContain('Achats');
 await act(async()=>{input.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true}))});
 expect(navigate).toHaveBeenCalledWith('orders');
 expect(host.querySelector('[role=dialog]')).toBeNull();
});

test('aucun accès équipe proposé au gérant, Escape ferme la recherche',async()=>{
 await render({role:'gerant',full_name:'Alex'});
 expect(host.querySelector('nav[aria-label="Navigation principale"]').textContent).not.toContain('Équipe');
 await click('Rechercher une page');
 await act(async()=>window.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true})));
 expect(host.querySelector('[role=dialog]')).toBeNull();
});

test('raccourci clavier Ctrl K et fournisseurs',async()=>{
 await render();
 await act(async()=>window.dispatchEvent(new KeyboardEvent('keydown',{key:'k',ctrlKey:true,bubbles:true})));
 expect(host.querySelector('[role=dialog]')).toBeTruthy();
 await click('Fournisseurs');
 expect(suppliers).toHaveBeenCalledTimes(1);
});
