import React,{act} from 'react';
import {createRoot} from 'react-dom/client';
import axios from 'axios';
import HistoriqueZPage from './HistoriqueZPage';
jest.mock('axios',()=>({defaults:{headers:{common:{}}},get:jest.fn()}));
let host,root;
beforeEach(()=>{global.IS_REACT_ACT_ENVIRONMENT=true;host=document.createElement('div');document.body.appendChild(host);root=createRoot(host)});
afterEach(async()=>{await act(async()=>root.unmount());host.remove();jest.clearAllMocks()});

test('un rapport Z s’affiche et le détail est consultable sans alert navigateur',async()=>{
 axios.get.mockResolvedValue({data:[{id:'z1',date:'2026-10-14T13:00:00',ca_total:521.33,produits:[{name:'Salade',qty:4}]}]});
 await act(async()=>root.render(<HistoriqueZPage/>));
 expect(host.textContent).toContain('521,33');
 expect(host.textContent).toContain('Clôtures disponibles');
 await act(async()=>[...host.querySelectorAll('button')].find(b=>b.textContent.includes('Consulter')).click());
 const dialog=host.querySelector('[role=dialog]');
 expect(dialog?.textContent).toContain('Salade');
 expect(dialog?.textContent).toContain('4 unité(s)');
 await act(async()=>[...dialog.querySelectorAll('button')].find(b=>b.textContent.includes('Fermer le détail')).click());
 expect(host.querySelector('[role=dialog]')).toBeNull();
});

test('état vide et erreur avec possibilité de réessayer',async()=>{
 axios.get.mockResolvedValueOnce({data:[]}).mockRejectedValueOnce(new Error('network'));
 await act(async()=>root.render(<HistoriqueZPage/>));
 expect(host.textContent).toContain('Pas encore de rapport Z');
 await act(async()=>[...host.querySelectorAll('button')].find(b=>b.textContent.includes('Actualiser')).click());
 expect(host.querySelector('[role=alert]')?.textContent).toContain('Impossible de charger');
});
