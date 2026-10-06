import React from 'react';
import { number } from '../../utils/contracts';
import { recipeCapacity } from '../../utils/planning';

const money = n => number(n).toLocaleString('fr-FR',{style:'currency',currency:'EUR'});
export default function OperationalAnalytics({mode,products,stocks,recipes,analytics}) {
 const rows=recipes.map(r=>recipeCapacity(r,products,stocks));
 const inventory=stocks.reduce((sum,s)=>sum+number(s.quantite_actuelle)*number(products.find(p=>p.id===s.produit_id)?.prix_achat ?? products.find(p=>p.id===s.produit_id)?.reference_price),0);
 const title={couts:'Coûts matière',rentabilite:'Marge matière des ventes',previsionnel:'Capacité de production'}[mode];
 const sales=analytics.topProductions || [];
 return <section className="section-card"><h2>{title}</h2>
  <p>{mode==='previsionnel' ? 'Chaque recette est calculée séparément, selon son ingrédient limitant. Plusieurs recettes peuvent utiliser le même stock.' : 'Calculs selon les prix produit et les quantités des fiches recettes. Les charges de personnel, loyers et autres frais ne sont pas inclus.'}</p>
  {mode==='couts' && <div className="kpi-card"><span className="title">Valeur des stocks de produits</span><strong className="value">{money(inventory)}</strong></div>}
  {!(mode==='rentabilite' ? sales.length : rows.length) ? <p className="rt-empty">Aucune donnée disponible pour ce calcul.</p> : <div className="rt-table-scroll"><table className="rt-stock-table"><thead><tr><th>Production</th><th>{mode==='previsionnel'?'Portions possibles':'Coût matière / portion'}</th><th>{mode==='rentabilite'?'Marge matière estimée':'Prix de vente / portion'}</th><th>État des données</th></tr></thead><tbody>{(mode==='rentabilite' ? sales : rows).map((item,index)=>{
   const row=mode==='rentabilite' ? rows.find(r=>r.recipe.nom.toLocaleLowerCase('fr')===item.nom.toLocaleLowerCase('fr')) : item;
   const valid=row && !row.errors.length;
   return <tr key={row?.recipe.id || index}><td>{row?.recipe.nom || item.nom}</td><td>{valid ? mode==='previsionnel' ? row.portions : money(row.costPerPortion) : '—'}</td><td>{mode==='rentabilite' ? valid ? money(number(item.ventes)-row.costPerPortion*number(item.portions)) : '—' : money(row?.recipe.prix_vente)}</td><td>{valid?'Fiche complète':row?.errors.join(' · ') || 'Aucune fiche recette correspondante'}</td></tr>;
  })}</tbody></table></div>}
 </section>;
}
