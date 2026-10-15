import React,{act} from 'react';
import {createRoot} from 'react-dom/client';
import OperationalAnalytics from './OperationalAnalytics';
let host,root;
beforeEach(()=>{global.IS_REACT_ACT_ENVIRONMENT=true;host=document.createElement('div');document.body.appendChild(host);root=createRoot(host)});
afterEach(async()=>{await act(async()=>root.unmount());host.remove()});

test('no recipe: clear empty state with explanation rather than fake estimate',async()=>{
 await act(async()=>root.render(<OperationalAnalytics mode="previsionnel" products={[]} stocks={[]} recipes={[]} analytics={{}}/>));
 expect(host.textContent).toContain('Aucune donnée pour ce calcul');
 expect(host.textContent).toContain('Capacité théorique');
 expect(host.querySelector('table')).toBeNull();
});

test('sales without matching recipe: disclose missing calculation, never invent margin',async()=>{
 await act(async()=>root.render(<OperationalAnalytics mode="rentabilite" recipes={[]} products={[]} stocks={[]} analytics={{topProductions:[{nom:'Plat inconnu',ventes:300,portions:6}]}}/>));
 expect(host.querySelector('[role=status]')?.textContent).toContain('1 référence');
 expect(host.textContent).toContain('Fiche recette absente');
 expect(host.querySelectorAll('tbody tr').length).toBe(1);
});
