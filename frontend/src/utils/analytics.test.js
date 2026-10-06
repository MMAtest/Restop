import { aggregateReports } from './analytics';
const range = {startDate:new Date(2026,9,5,12),endDate:new Date(2026,9,5,12)};
test('filters actual dates and supports deployed name/qty/ca fields without invented amounts', () => {
  const r = aggregateReports([{date:'2026-10-05',ca_total:120,produits:[{name:'Burrata',qty:4,ca:60}]},{date:'2026-10-04',ca_total:900,produits:[]}],[],range);
  expect(r.caTotal).toBe(120); expect(r.caMidi).toBe(0); expect(r.caNonVentile).toBe(120);
  expect(r.topProductions[0]).toMatchObject({nom:'Burrata',ventes:60,portions:4});
  expect(r.couvertsTotal).toBe(0);
});
test('supports legacy fields and real service information', () => {
  const r=aggregateReports([{date:'2026-10-05',service:'soir',ca_total:'100',nb_couverts:5,produits:[{nom:'Soupe',quantite:5,prix_unitaire:20}]}],[{nom:'Soupe',categorie:'Entrée'}],range);
  expect(r.caSoir).toBe(100); expect(r.couvertsSoir).toBe(5);expect(r.ventesParCategorie.entrees).toBe(100);
});
test('empty period and malformed rows never display undefined or NaN', () => {
  expect(aggregateReports([{date:'2026-10-04',ca_total:50}],[],range).caTotal).toBe(0);
  const r=aggregateReports([{date:'2026-10-05',ca_total:'bad',produits:[{qty:2},{name:'Produit',qty:'bad'}]}],[],range);
  expect(r.caTotal).toBe(0);expect(r.topProductions).toHaveLength(1);expect(r.topProductions[0].ventes).toBe(0);
});
