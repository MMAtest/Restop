import React,{act} from 'react';
import {createRoot} from 'react-dom/client';
import axios from 'axios';
import TenantReceivingWizard,{toMilliunits,toCents} from './TenantReceivingWizard';
jest.mock('axios',()=>({get:jest.fn(),post:jest.fn(),defaults:{}}));
let root,host;
const order={id:'order-1',supplier_id:'supplier-1',status:'approved',estimated_total_cents:600,
 lines:[{product_id:'product-1',quantity_milliunits:3000,unit_price_cents:200,unit:'kg'}]};
const product={id:'product-1',name:'Tomates locales',unit:'kg'};
const change=(el,value)=>{const setter=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;setter.call(el,value);el.dispatchEvent(new Event('input',{bubbles:true}));};
const click=async(pattern)=>{
 const button=[...host.querySelectorAll('button')].find(b=>pattern.test(b.textContent));
 if(!button)throw Error('Button not found '+pattern);
 await act(async()=>button.click());return button;
};
beforeEach(()=>{global.IS_REACT_ACT_ENVIRONMENT=true;host=document.createElement('div');document.body.appendChild(host);root=createRoot(host);
 axios.get.mockReset();axios.post.mockReset();axios.get.mockImplementation(url=>Promise.resolve({data:url.includes('purchase-orders')?[order]:[product]}));
});
afterEach(async()=>{await act(async()=>root.unmount());host.remove();});

test('quantités et prix décimaux analysés sans arrondir',()=>{
 expect(toMilliunits('1,234')).toBe(1234);
 expect(toMilliunits('0.005')).toBe(5);
 expect(toMilliunits('1.1234')).toBeNull();
 expect(toMilliunits('-1')).toBeNull();
 expect(toCents('12,45')).toBe(1245);
 expect(toCents('12,457')).toBeNull();
 expect(toCents('abc')).toBeNull();
});

test('saisir, prévisualiser et confirmer sans appel anticipé de mise en stock',async()=>{
 const preview={issues:[],can_confirm:true,invoice_total_cents:600};
 axios.post.mockImplementation(url=>{
  if(url.endsWith('/receipts/preview'))return Promise.resolve({data:preview});
  if(url.endsWith('/receipts/confirm'))return Promise.resolve({data:{id:'receipt-1',order_status_after:'received',replayed:false}});
  throw Error('Unexpected endpoint '+url);
 });
 await act(async()=>root.render(<TenantReceivingWizard/>));
 await click(/Prête à recevoir/);
 expect(host.textContent).toContain('Tomates locales');
 const fields=[...host.querySelectorAll('.rt-receiving-fields input')];
 await act(async()=>{change(fields[0],'BL-ABC-001');change(fields[1],'FAC-ABC-001')});
 await click(/Vérifier les écarts/);
 expect(axios.post).toHaveBeenCalledTimes(1);
 expect(axios.post.mock.calls[0][0].endsWith('/receipts/preview')).toBe(true);
 expect(axios.post.mock.calls[0][1].invoice_source).toBe('human_verified');
 expect(host.textContent).toContain('6,00');
 await click(/Continuer vers validation/);
 expect(axios.post).toHaveBeenCalledTimes(1);
 expect(host.textContent).toContain('Dernière vérification');
 await click(/Oui, confirmer la réception et le stock/);
 expect(axios.post).toHaveBeenCalledTimes(2);
 expect(axios.post.mock.calls[1][0].endsWith('/receipts/confirm')).toBe(true);
 expect(host.textContent).toContain('Réception enregistrée');
});
