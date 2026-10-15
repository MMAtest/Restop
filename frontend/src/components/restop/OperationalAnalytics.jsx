import React,{useMemo,useState} from 'react';
import {MagnifyingGlass,Info,ChartLineUp,Coins,WarningCircle} from '@phosphor-icons/react';
import {number} from '../../utils/contracts';
import {recipeCapacity} from '../../utils/planning';
import './operational-analytics.css';

const money=n=>number(n).toLocaleString('fr-FR',{style:'currency',currency:'EUR'});
const titles={couts:'Coûts matière',rentabilite:'Marge matière des ventes',previsionnel:'Capacité de production'};
const messages={
  couts:'Calcul basé sur les prix et quantités des fiches recettes. Les charges fixes et le personnel ne sont pas inclus.',
  rentabilite:'Estimation de marge matière : chiffre d’affaires constaté moins coût des ingrédients. Les autres charges ne sont pas déduites.',
  previsionnel:'Capacité théorique par recette selon l’ingrédient limitant. Les capacités ne s’additionnent pas car plusieurs recettes partagent le stock.'
};

export default function OperationalAnalytics({mode,products=[],stocks=[],recipes=[],analytics={}}) {
 const [term,setTerm]=useState('');
 const rows=useMemo(()=>recipes.map(r=>recipeCapacity(r,products,stocks)),[recipes,products,stocks]);
 const sales=analytics?.topProductions||[];
 const source=mode==='rentabilite'?sales:rows;
 const incomplete=mode==='rentabilite'
  ? source.filter(item=>!rows.some(row=>row.recipe?.nom?.toLocaleLowerCase('fr')===item.nom?.toLocaleLowerCase('fr')&&!row.errors.length)).length
  : rows.filter(item=>item.errors?.length).length;
 const matching=source.filter(item=>(mode==='rentabilite'?item.nom:item.recipe?.nom||'').toLocaleLowerCase('fr').includes(term.trim().toLocaleLowerCase('fr')));
 const inventory=stocks.reduce((sum,s)=>{
  const product=products.find(p=>p.id===s.produit_id);
  const qty=Number(s.quantite_actuelle),price=Number(product?.prix_achat??product?.reference_price);
  return sum+(Number.isFinite(qty)&&Number.isFinite(price)&&qty>0&&price>=0?qty*price:0);
 },0);
 return <section className="rt-analytics-panel section-card" aria-label={titles[mode]||'Analyses opérationnelles'}>
  <header className="rt-analytics-heading"><div><p className="rt-module-kicker">DONNÉES MÉTIER</p><h2>{titles[mode]||'Analyses'}</h2><p>{messages[mode]}</p></div><span className="rt-analytics-heading-icon"><ChartLineUp size={24}/></span></header>
  {mode==='couts'&&<div className="rt-analytics-summary"><Coins size={23}/><span>Valeur indicative du stock renseigné</span><strong>{money(inventory)}</strong></div>}
  <div className="rt-analytics-tools"><div><strong>{source.length} référence{source.length>1?'s':''}</strong><small>Basé sur les données disponibles</small></div>
   <label className="rt-analytics-search"><MagnifyingGlass size={16}/><span className="rt-sr-only">Rechercher une production</span><input type="search" value={term} onChange={event=>setTerm(event.target.value)} placeholder="Rechercher une production…"/></label></div>
  {incomplete>0&&<div role="status" className="rt-analytics-data-notice"><WarningCircle size={18}/><span>{incomplete} référence{incomplete>1?'s':''} avec calcul indisponible : fiche produit manquante, donnée incomplète ou correspondance introuvable. Les valeurs concernées restent masquées.</span></div>}
  {source.length===0?<div className="rt-analytics-empty"><Info size={23}/><strong>Aucune donnée pour ce calcul</strong><p>Ajoutez des fiches recette ou importez vos ventes pour activer cette analyse.</p></div>:
   matching.length===0?<div className="rt-analytics-empty"><MagnifyingGlass size={23}/><strong>Aucune production correspondante</strong><p>Essayez un autre nom ou effacez la recherche.</p><button onClick={()=>setTerm('')}>Effacer la recherche</button></div>:
   <div className="rt-table-scroll"><table className="rt-stock-table rt-analytics-table"><thead><tr><th scope="col">Production</th><th scope="col">{mode==='previsionnel'?'Portions possibles':'Coût matière / portion'}</th><th scope="col">{mode==='rentabilite'?'Marge matière estimée':'Prix de vente / portion'}</th><th scope="col">Qualité des données</th></tr></thead><tbody>{matching.map((item,index)=>{
    const row=mode==='rentabilite'?rows.find(r=>r.recipe?.nom?.toLocaleLowerCase('fr')===item.nom?.toLocaleLowerCase('fr')):item;
    const valid=row&&!row.errors.length;
    return <tr key={row?.recipe?.id||item.id||index}><td><strong>{row?.recipe?.nom||item.nom}</strong></td>
     <td className="rt-analytics-number">{valid?(mode==='previsionnel'?row.portions:money(row.costPerPortion)):'—'}</td>
     <td className="rt-analytics-number">{mode==='rentabilite'?(valid?money(number(item.ventes)-row.costPerPortion*number(item.portions)):'—'):(row?.recipe?.prix_vente!=null?money(row.recipe.prix_vente):'—')}</td>
     <td>{valid?<span className="rt-analytics-status is-ok">Fiche complète</span>:<span className="rt-analytics-status is-missing">{row?.errors?.join(' · ')||'Fiche recette absente'}</span>}</td></tr>;
   })}</tbody></table></div>}
  <footer className="rt-analytics-footnote"><Info size={14}/> Les estimations dépendent des prix fournisseur, recettes et quantités enregistrés ; elles ne constituent pas une prévision comptable.</footer>
 </section>;
}
