import test from 'node:test';
import assert from 'node:assert/strict';
import {validateDraft,providerCapabilities} from '../einvoice-contract.mjs';
test('Restop e-invoice preflight is independent of paid APIs',()=>{
  const r=validateDraft({
    documentType:'invoice',number:'F-1',issueDate:'2026-10-19',currency:'EUR',
    seller:{name:'Fournisseur',siret:'12345678901234'},
    buyer:{name:'Restaurant',siret:'98765432109876'},
    lines:[{description:'Produit',quantity:3,unitPriceExclTax:'12.50',vatRate:5.5}]
  });
  assert.equal(r.ok,true);
  assert.deepEqual(r.preview.totals,{net:37.5,vat:2.06,gross:39.56});
  assert.equal(providerCapabilities().apiConnected,false);
  assert.equal(providerCapabilities().autoSendEnabled,false);
});
