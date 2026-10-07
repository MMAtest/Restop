import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import axios from 'axios';
import App from './App';
import contracts from './test-fixtures/demo-contracts.json';

jest.mock('react-router-dom', () => ({useNavigate: () => jest.fn(), Link: ({children,to,...props}) => <a href={to} {...props}>{children}</a>}), {virtual:true});
jest.mock('axios', () => ({get:jest.fn(),post:jest.fn(),put:jest.fn(),delete:jest.fn(),defaults:{headers:{common:{}}}}));
jest.mock('./components/RoleBasedDashboard', () => () => null);
jest.mock('./pages/DataGridsPage', () => () => null);
jest.mock('react-chartjs-2', () => ({ Pie: () => null }));

let host, root, errors;
const click = async name => {
 const button = [...host.querySelectorAll('button')].find(b => b.textContent.trim() === name);
 expect(button).toBeTruthy();
 await act(async () => { button.click(); });
};
beforeEach(async () => {
 global.IS_REACT_ACT_ENVIRONMENT = true;
 window.scrollTo=jest.fn();
 localStorage.setItem('user_session', JSON.stringify({session_id:'test',user:{id:'demo-restop',role:'patron',full_name:'Démo'}}));
 axios.defaults = {headers:{common:{}}};
 axios.get.mockImplementation(async url => {
  const path = url.slice(url.indexOf('/api')+4).split('?')[0];
  return {data:path === '/auth/session' ? {valid:true,user:{id:'demo-restop',role:'patron',full_name:'Démo'}} : contracts[path] || []};
 });
 host=document.createElement('div');document.body.appendChild(host);errors=[];
 root=createRoot(host,{onUncaughtError:error=>errors.push(error)});
 await act(async()=>{root.render(<App />);});
});
afterEach(async()=>{await act(async()=>root.unmount());host.remove();jest.clearAllMocks();localStorage.clear();});
test('production category selector accepts the deployed list response',async()=>{
 await click('Production');await click('Productions');
 expect(errors).toEqual([]);expect(host.querySelector('#production').textContent).toContain('Entrecôte');
});
test('new product form opens even when the units endpoint has no data',async()=>{
 await click('Production');await click('Nouveau Produit');
 expect(errors).toEqual([]);expect(host.querySelector('select[name="unite"], #product-unit') || host.textContent.includes('Unité')).toBeTruthy();
});
test('nullable preparation fields do not break editing',async()=>{
 contracts['/preparations'][0].perte=null;
 await click('Production');await click('Préparations (3)');
 await click('✏️');expect(errors).toEqual([]);
 expect([...host.querySelectorAll('.modal-overlay option')].some(o=>o.textContent.includes('Sauce'))).toBe(true);
});
test('creating after cancelling an edit does not retain the old recipe identity',async()=>{
 await click('Production');await click('Productions');await click('Éditer');await click('Annuler');await click('Nouvelle Production');
 expect(host.querySelector('.modal-overlay h3').textContent).toContain('Ajouter une recette');
 expect(host.querySelector('.modal-overlay input').value).toBe('');
});
test('invoice correction opens the working validation dialog',async()=>{
 contracts['/ocr/documents']=[{id:'invoice',type_document:'facture_fournisseur',statut:'analyse',donnees_extraites:{fournisseur:'Test',date:'2026-10-07',total_ttc:10}}];
 axios.get.mockImplementation(async url => ({data:url.includes('/ocr/documents') ? contracts['/ocr/documents'] : url.includes('/auth/session') ? {valid:true,user:{id:'demo-restop',role:'patron',full_name:'Démo'}} : []}));
 await act(async()=>{root.unmount();});
 root=createRoot(host);await act(async()=>{root.render(<App/>);});
 await click('Stocks');await click('OCR');
 axios.post.mockResolvedValue({data:{supplier_name:'Test',invoice_date:'2026-10-07',invoice_number:'TEST-01',total_ttc:10,products:[]}});
 await click('Factures');
 await click('Vérifier les données de la facture');
 expect(host.textContent).toContain('Validation');
 expect(host.querySelector('[role=dialog], .modal-overlay')).toBeTruthy();
});
test('the supplier form accepts a midnight order cutoff',async()=>{
 await click('Production');await click('Fournisseurs');await click('Nouveau Fournisseur');await click('Configurer');
 const select=[...host.querySelectorAll('.modal-overlay select')].find(s=>[...s.options].some(o=>o.textContent==='00:00 (Matin)'));
 await act(async()=>{select.value='0';select.dispatchEvent(new Event('change',{bubbles:true}));});
 expect(select.value).toBe('0');
});
