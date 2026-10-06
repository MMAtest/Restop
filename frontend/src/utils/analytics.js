const numeric = value => Number.isFinite(Number(value)) ? Number(value) : 0;
const categoryKey = value => {
  const text = (value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  if (text.includes('entree')) return 'entrees';
  if (text.includes('plat')) return 'plats';
  if (text.includes('dessert')) return 'desserts';
  if (/bar|boisson|vin/.test(text)) return 'boissons';
  return 'autres';
};
const dayKey = value => {
  // Date-only reports are restaurant calendar days, not UTC instants.
  if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value)) return value;
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleDateString('sv-SE', { timeZone: 'Europe/Paris' });
};
export function aggregateReports(reports = [], recipes = [], range) {
  const data = {caTotal:0,caMidi:0,caSoir:0,caNonVentile:0,couvertsMidi:0,couvertsSoir:0,couvertsTotal:0,topProductions:[],flopProductions:[],ventesParCategorie:{entrees:0,plats:0,desserts:0,boissons:0,autres:0}};
  const start = range ? dayKey(range.startDate) : '';
  const end = range ? dayKey(range.endDate) : '';
  const rows = (Array.isArray(reports) ? reports : []).filter(r => { const d=dayKey(r.date || r.date_rapport); return d && (!range || (d >= start && d <= end)); });
  const grouped = new Map();
  rows.forEach(r => {
    data.caTotal += numeric(r.ca_total);
    const covers = numeric(r.nb_couverts ?? r.couverts);
    data.couvertsTotal += covers;
    const service = String(r.service || '').toLowerCase();
    if (service === 'midi') { data.caMidi += numeric(r.ca_total); data.couvertsMidi += covers; }
    else if (service === 'soir') { data.caSoir += numeric(r.ca_total); data.couvertsSoir += covers; }
    else data.caNonVentile += numeric(r.ca_total);
    (Array.isArray(r.produits) ? r.produits : []).forEach(p => {
      const name = p.nom || p.name || p.produit_nom;
      if (!name || name === 'undefined') return;
      const quantity = numeric(p.quantite ?? p.qty);
      const revenue = numeric(p.ca ?? p.ventes ?? p.montant ?? quantity * numeric(p.prix_unitaire));
      const recipe = (Array.isArray(recipes) ? recipes : []).find(x => (x.nom || '').toLocaleLowerCase('fr') === name.toLocaleLowerCase('fr'));
      const row = grouped.get(name) || {nom:name,ventes:0,portions:0,categorie:p.categorie || recipe?.categorie || 'Autres',coefficientPrevu:numeric(recipe?.coefficient_prevu),coefficientReel:numeric(recipe?.coefficient_reel),coutMatiere:0,prixVente:numeric(recipe?.prix_vente)};
      row.ventes += revenue; row.portions += quantity; row.coutMatiere += numeric(recipe?.cout_matiere) * quantity;
      grouped.set(name,row);
      data.ventesParCategorie[categoryKey(row.categorie)] += revenue;
    });
  });
  const sorted = [...grouped.values()].sort((a,b) => b.ventes-a.ventes);
  data.topProductions = sorted.slice(0,7);
  data.flopProductions = sorted.length > 1 ? [...sorted].reverse().slice(0,7) : [];
  return data;
}
