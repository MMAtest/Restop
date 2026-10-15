import React, {act} from 'react';
import {createRoot} from 'react-dom/client';
import axios from 'axios';
import InvoiceValidationModal from './InvoiceValidationModal';

jest.mock('axios', () => ({post:jest.fn()}));
const sample = {
  supplier_name: 'Primeur du Port', is_new_supplier:true,
  facture_date:'2026-10-15', numero_facture:'FAC-120',
  audit_warnings:[{code:'line_mismatch',message:'Écart de prix détecté pour une ligne.'}],
  items:[{ocr_name:'Tomates',ocr_qty:2,ocr_unit:'kg',ocr_price:4,ocr_total:8,
    final_qty:2,final_name:'Tomates',status:'new',confidence:0.3}]
};
let host, root, onSuccess, onClose;
const button = label => [...host.querySelectorAll('button')].find(b=>b.textContent.includes(label));
const click = async label => {
  const target=button(label);
  expect(target).toBeTruthy();
  await act(async()=>{target.click();});
};
beforeEach(async()=>{
  global.IS_REACT_ACT_ENVIRONMENT=true;
  window.innerWidth=1200;
  axios.post.mockImplementation(async url => url.includes('/confirm-import')
    ? {data:{stats:{stock_entries:1,batches_created:1}}}
    : {data:sample});
  onClose=jest.fn();onSuccess=jest.fn();
  host=document.createElement('div');document.body.appendChild(host);
  root=createRoot(host);
  await act(async()=>root.render(<InvoiceValidationModal
    documentId="doc1" onClose={onClose} onSuccess={onSuccess} produitsList={[]} fournisseursList={[]}/>));
});
afterEach(async()=>{
  await act(async()=>root.unmount());host.remove();jest.clearAllMocks();
});

test('guide en trois étapes avec messages et vérification humaine, puis succès visible',async()=>{
  expect(host.textContent).toContain('Étape 1/3');
  expect(host.textContent).toContain('Confirmez le fournisseur');
  expect(host.textContent).toContain('Analyse reçue');
  expect(host.textContent).not.toContain('Étape 3/3');
  await click('Continuer');
  expect(host.textContent).toContain('Étape 2/3');
  expect(host.textContent).toContain('Corrigez les quantités');
  expect(host.textContent).toContain('Tomates');
  await click('Continuer');
  expect(host.textContent).toContain('Étape 3/3');
  expect(host.textContent).toContain('Écart de prix détecté');
  await click('Confirmer l’entrée en stock');
  expect(host.querySelector('[role="alert"]').textContent).toContain('Cochez la confirmation');
  expect(axios.post).toHaveBeenCalledTimes(1);
  const checkbox=host.querySelector('input[type=checkbox]');
  await act(async()=>{checkbox.click();});
  await click('Confirmer l’entrée en stock');
  expect(axios.post).toHaveBeenCalledTimes(2);
  expect(axios.post.mock.calls[1][1]).toEqual(expect.objectContaining({
    invoice_number:'FAC-120',acknowledge_audit_warnings:true
  }));
  expect(host.textContent).toContain('Facture intégrée au stock');
  expect(onSuccess).toHaveBeenCalledTimes(1);
  expect(onClose).not.toHaveBeenCalled();
  await click('Fermer et voir les stocks');
  expect(onClose).toHaveBeenCalledTimes(1);
});

test('erreurs de saisie expliquées dans le guide sans navigateur alert',async()=>{
  await click('Continuer');
  const qty=[...host.querySelectorAll('input[type=number]')].find(i=>i.value==='2');
  expect(qty).toBeTruthy();
  await act(async()=>{
    const setter=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
    setter.call(qty,'0');qty.dispatchEvent(new Event('input',{bubbles:true}));
  });
  await click('Continuer');
  expect(host.querySelector('[role="alert"]').textContent).toContain('Ligne 1');
  expect(host.textContent).toContain('Étape 2/3');
});

test('message serveur d’échec reste visible dans la fenêtre',async()=>{
  axios.post.mockImplementation(async url=>url.includes('/confirm-import')
    ? Promise.reject({response:{data:{detail:'MongoDB replica set requis'}}})
    : {data:{...sample,audit_warnings:[],items:[{...sample.items[0],status:'matched',product_id:'p1'}]}});
  // Mount instance that uses latest mock (initial mount already happened)
  await act(async()=>root.unmount());
  root=createRoot(host);
  await act(async()=>root.render(<InvoiceValidationModal documentId="doc2" onClose={onClose} onSuccess={onSuccess} produitsList={[]} fournisseursList={[]}/>));
  await click('Continuer');await click('Continuer');
  await click('Confirmer l’entrée en stock');
  expect(host.querySelector('[role="alert"]').textContent).toContain('Cochez la confirmation');
  await act(async()=>host.querySelector('input[type=checkbox]').click());
  await click('Confirmer l’entrée en stock');
  expect(host.querySelector('[role="alert"]').textContent).toContain('MongoDB replica set requis');
  expect(onSuccess).not.toHaveBeenCalled();
});

test('affiche des instructions et les contrôles du wizard sur mobile',async()=>{
  await act(async()=>{window.innerWidth=390;window.dispatchEvent(new Event('resize'));});
  expect(host.querySelector('[role="dialog"]')).toBeTruthy();
  expect(host.querySelector('.rt-wizard-steps [aria-current="step"]').textContent).toContain('Fournisseur');
  await click('Continuer');
  expect(host.textContent).toContain('Une ligne incorrecte peut fausser le stock');
  expect(host.querySelectorAll('input').length).toBeGreaterThan(0);
});
