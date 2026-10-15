import React,{act} from 'react';
import {createRoot} from 'react-dom/client';
import StockKpiBar,{expiringWithin} from './StockKpiBar';
let host,root;
const onAll=jest.fn(),onCritical=jest.fn(),onDlc=jest.fn();
beforeEach(()=>{global.IS_REACT_ACT_ENVIRONMENT=true;host=document.createElement('div');document.body.appendChild(host);root=createRoot(host)});
afterEach(async()=>{await act(async()=>root.unmount());host.remove();jest.clearAllMocks()});

test('stock KPI : vrais boutons, chiffres calculés, pas de carte valeur trompeuse cliquable',async()=>{
 await act(async()=>root.render(<StockKpiBar stocks={[{produit_id:'a',quantite_actuelle:2,quantite_min:4},{produit_id:'b',quantite_actuelle:6,quantite_min:2}]} products={[{id:'a',prix_achat:2.5},{id:'b',prix_achat:4}]} onAll={onAll} onCritical={onCritical} onDlc={onDlc} activeFilter="critical"/>));
 expect(host.textContent).toContain('29');
 expect(host.querySelectorAll('button.rt-stock-kpi').length).toBe(3);
 expect(host.querySelector('.rt-stock-kpi-readonly')).toBeTruthy();
 const critical=host.querySelector('button.rt-stock-kpi-critical');
 expect(critical.getAttribute('aria-pressed')).toBe('true');
 await act(async()=>critical.click());
 expect(onCritical).toHaveBeenCalledTimes(1);
});

test('DLC invalides ignorées, DLC dépassées signalées, dates frontières',()=>{
 const now=new Date('2026-10-15T12:00:00Z');
 const rows=[{dlc:'not-a-date'},{dlc:'2026-10-10'},{dlc:'2026-10-20'},{dlc:'2026-10-17'},{dlc:null}];
 expect(expiringWithin(rows,3,now)).toHaveLength(2);
});
