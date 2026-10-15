import test from 'node:test';
import assert from 'node:assert/strict';
import {buildOperationalBrief, pendingSupplierInvoices} from './operationalBrief.mjs';

test('une facture OCR traitée mais non intégrée nécessite encore validation', () => {
  const docs = [
    { type_document:'facture_fournisseur', statut:'traite' },
    { type_document:'facture_fournisseur', statut:'integre' },
    { type_document:'z_report', statut:'traite' },
  ];
  assert.equal(pendingSupplierInvoices(docs).length, 1);
});

test('trie DLC expirée, rupture et hausse avant les informations non urgentes', () => {
  const result = buildOperationalBrief({
    expiring_products:[{product_name:'Lait',days_to_expiry:-1,quantity:2,batch_id:'l1'}],
    low_stock_items:[{product_name:'Œufs',current_quantity:0,minimum_quantity:10}],
    price_anomalies:[{product_name:'Farine',reference_price:3,actual_price:3.6,supplier_name:'A'}],
    unused_stock:[{product_name:'Thé',quantity:3,days_unused:40}],
  });
  assert.deepEqual(result.actions.map(a => a.kind), ['dlc','stock','price','unused']);
  assert.equal(result.urgentCount,3);
  assert.match(result.actions[2].detail,/20/);
});

test('ne promet pas de hausse lorsque le prix a baissé', () => {
  assert.equal(buildOperationalBrief({price_anomalies:[{reference_price:5,actual_price:4}]}).actions.length,0);
});

test('données manquantes et tableaux invalides n’inventent aucune alerte', () => {
  const r=buildOperationalBrief({low_stock_items:null,price_anomalies:{}},null);
  assert.deepEqual(r.actions,[]);
});
