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
});
test('creating after cancelling an edit does not retain the old recipe identity',async()=>{
 await click('Production');await click('Productions');await click('Éditer');await click('Annuler');await click('Nouvelle Production');
 expect(host.querySelector('.modal-overlay h3').textContent).toContain('Ajouter une recette');
 expect(host.querySelector('.modal-overlay input').value).toBe('');
});
