import React,{act} from 'react';
import {createRoot} from 'react-dom/client';
import FormModal from './FormModal';
let host,root;const close=jest.fn();
beforeEach(()=>{global.IS_REACT_ACT_ENVIRONMENT=true;host=document.createElement('div');document.body.appendChild(host);root=createRoot(host)});
afterEach(async()=>{await act(async()=>root.unmount());host.remove();jest.clearAllMocks()});
test('modal formulaire : rôle, libellé champ et annulation Escape',async()=>{
 await act(async()=>root.render(<FormModal title="Créer un produit" onClose={close}><h3 className="modal-header">Créer un produit</h3><form><div className="form-group"><label className="form-label">Nom du produit</label><input type="text"/></div><button type="submit">Créer</button></form></FormModal>));
 const modal=host.querySelector('[role="dialog"]');
 expect(modal).toBeTruthy();expect(modal.getAttribute('aria-label')).toBe('Créer un produit');
 expect(host.querySelector('label').htmlFor).toBe(host.querySelector('input').id);
 await act(async()=>window.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape'})));
 expect(close).toHaveBeenCalledTimes(1);
});

test('ne perd pas silencieusement les saisies après clic sur fermer',async()=>{
 await act(async()=>root.render(<FormModal title="Modifier le produit" onClose={close}><form><div className="form-group"><label className="form-label">Nom</label><input type="text" defaultValue="A"/></div></form></FormModal>));
 const input=host.querySelector('input');
 await act(async()=>{const setter=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;setter.call(input,'AB');input.dispatchEvent(new Event('input',{bubbles:true}))});
 await act(async()=>host.querySelector('button[aria-label="Fermer le formulaire"]').click());
 expect(close).not.toHaveBeenCalled();
 expect(host.querySelector('[role="alert"]')?.textContent).toContain('ne sont pas enregistrées');
 await act(async()=>[...host.querySelectorAll('button')].find(b=>b.textContent==='Continuer la saisie').click());
 expect(close).not.toHaveBeenCalled();
 await act(async()=>host.querySelector('button[aria-label="Fermer le formulaire"]').click());
 await act(async()=>[...host.querySelectorAll('button')].find(b=>b.textContent==='Quitter sans enregistrer').click());
 expect(close).toHaveBeenCalledTimes(1);
});
