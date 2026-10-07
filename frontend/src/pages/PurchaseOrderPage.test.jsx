import React,{act} from 'react';
import {createRoot} from 'react-dom/client';
import PurchaseOrderPage from './PurchaseOrderPage';
import {apiFetch} from '../utils/api';
jest.mock('../utils/api',()=>({apiFetch:jest.fn(),responseJson:async r=>r.json()}));
test('order history resolves the supplier name when the order response omits it',async()=>{
 global.IS_REACT_ACT_ENVIRONMENT=true;const host=document.createElement('div');document.body.appendChild(host);const root=createRoot(host);
 apiFetch.mockImplementation(async url=>({ok:true,json:async()=>url.endsWith('/fournisseurs')?[{id:'supplier',nom:'Maison du Frais'}]:url.endsWith('/orders')?[{id:'order',supplier_id:'supplier',order_number:'CMD-1',total_amount:10,status:'pending',items:[]}]:[]}));
 await act(async()=>root.render(<PurchaseOrderPage currentUser={{role:'patron'}}/>));
 await act(async()=>[...host.querySelectorAll('button')].find(b=>b.textContent.includes('Historique')).click());
 expect(host.querySelector('h4').textContent).toBe('Maison du Frais');
 await act(async()=>root.unmount());host.remove();jest.resetAllMocks();
});
