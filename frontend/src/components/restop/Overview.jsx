import React, {useMemo, useState} from 'react';
import {motion, AnimatePresence, useReducedMotion} from 'motion/react';
import {
  ArrowUpRight, ArrowRight, Package, UploadSimple, Receipt, CheckCircle,
  Warning, MagnifyingGlass, TrendDown, Clock, CaretRight
} from '@phosphor-icons/react';
import OperationalPriorities from './OperationalPriorities';
import AnimatedNumber from './motion/AnimatedNumber';
import {pendingSupplierInvoices} from '../../utils/operationalBrief.mjs';
import './overview-premium.css';

export const previewStocks = [
  { image:'restop-tomatoes.webp', produit_id:'tomate', produit_nom:'Tomates fraîches', quantite_actuelle:8, quantite_min:20, unite:'kg' },
  { image:'restop-mozzarella.webp', produit_id:'mozza', produit_nom:'Mozzarella di bufala', quantite_actuelle:1.5, quantite_min:5, unite:'kg' },
  { image:'restop-basil.webp', produit_id:'basilic', produit_nom:'Basilic frais', quantite_actuelle:200, quantite_min:1000, unite:'g' },
];

const format = number => Number(number || 0).toLocaleString('fr-FR',{maximumFractionDigits:2});
const safe = value => Number.isFinite(Number(value)) ? Number(value) : 0;
const statusOf = item => {
  const quantity=safe(item.quantite_actuelle);
  const minimum=safe(item.quantite_min);
  return quantity <= 0 ? 'out' : minimum > 0 && quantity <= minimum ? 'low' : 'ok';
};
const stockStatusLabel = {out:'Rupture',low:'Sous seuil',ok:'Disponible'};

function StockIdentity({stock, preview}) {
  return <span className="rt-data-identity">
    <span className="rt-data-avatar">{preview && stock.image
      ? <img src={`/images/${stock.image}`} width="42" height="42" loading="lazy" alt="" />
      : <Package size={21} weight="light" />}</span>
    <span className="rt-data-name"><strong>{stock.produit_nom || stock.nom || 'Produit sans nom'}</strong>
      <small>{stock.unite ? `Unité · ${stock.unite}` : 'Suivi de stock'}</small></span>
  </span>;
}

function QuantityIndicator({stock}) {
  const quantity=safe(stock.quantite_actuelle);
  const minimum=safe(stock.quantite_min);
  const status=statusOf(stock);
  const percent=minimum>0 ? Math.max(0,Math.min(100,(quantity/minimum)*100)) : 100;
  return <div className="rt-data-quantity">
    <div className="rt-data-quantity-top"><strong>{format(quantity)} <span>{stock.unite||''}</span></strong><span>{minimum>0 ? `${Math.round(percent)} % du seuil`:'Aucun seuil'}</span></div>
    <div className="rt-data-bar" role="meter" aria-label={`Niveau de stock : ${format(quantity)} ${stock.unite||''}; seuil ${format(minimum)} ${stock.unite||''}`}
      aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(percent)}>
      <span className={`rt-data-bar-fill rt-data-bar-${status}`} style={{width:`${percent}%`}}/>
    </div>
  </div>;
}

function StockTable({stocks, preview, onStocks}) {
  const [filter,setFilter]=useState('watch');
  const reduceMotion=useReducedMotion();
  const filtered=useMemo(()=>stocks.filter(item=>filter==='all' ? true : filter==='out' ? statusOf(item)==='out' : statusOf(item)!=='ok')
    .sort((a,b)=>({out:0,low:1,ok:2}[statusOf(a)]-({out:0,low:1,ok:2}[statusOf(b)]))),[filter,stocks]);
  const stats={watch:stocks.filter(s=>statusOf(s)!=='ok').length,all:stocks.length,out:stocks.filter(s=>statusOf(s)==='out').length};
  const filters=[{id:'watch',label:'À surveiller'},{id:'all',label:'Tous les produits'},{id:'out',label:'Ruptures'}];
  return <section className="rt-data-panel" aria-labelledby="rt-data-panel-heading">
    <header className="rt-data-panel-heading">
      <div><span className="rt-panel-eyebrow">INVENTAIRE ACTIF</span><h2 id="rt-data-panel-heading">État des stocks</h2>
        <p>Les références qui méritent votre attention avant le prochain service.</p></div>
      <button className="rt-data-open" onClick={onStocks}>Ouvrir les stocks <ArrowUpRight size={16}/></button>
    </header>
    <div className="rt-data-filters" role="group" aria-label="Filtrer les produits par statut">
      {filters.map(option=><button key={option.id} className={filter===option.id?'is-active':''} aria-pressed={filter===option.id} onClick={()=>setFilter(option.id)}>
        {filter===option.id && <motion.span className="rt-data-filter-active" layoutId="rt-stock-filter" transition={{type:'spring',stiffness:380,damping:35}}/>}
        <span>{option.label}</span><small>{stats[option.id]}</small>
      </button>)}
    </div>
    {filtered.length>0 ? <>
      <div className="rt-data-table-wrap"><table className="rt-data-table">
        <thead><tr><th scope="col">Produit</th><th scope="col">Stock disponible</th><th scope="col">Seuil</th><th scope="col">État</th><th scope="col"><span className="rt-visually-hidden">Voir le produit</span></th></tr></thead>
        <tbody>{filtered.slice(0,8).map(item=><tr key={item.produit_id || item.id || item.produit_nom}>
          <td><StockIdentity stock={item} preview={preview}/></td>
          <td><QuantityIndicator stock={item}/></td>
          <td className="rt-data-threshold">{safe(item.quantite_min)>0 ? <><strong>{format(item.quantite_min)}</strong> <span>{item.unite||''}</span></> : <span>Non défini</span>}</td>
          <td><span className={`rt-data-status rt-data-status-${statusOf(item)}`}><i/>{stockStatusLabel[statusOf(item)]}</span></td>
          <td><button type="button" className="rt-data-row-link" onClick={onStocks} aria-label={`Voir ${item.produit_nom || item.nom || 'le produit'} dans les stocks`}><ArrowUpRight size={18}/></button></td>
        </tr>)}</tbody>
      </table></div>
      <div className="rt-data-mobile-list">
        <AnimatePresence mode="popLayout" initial={false}>{filtered.slice(0,8).map(item=><motion.article key={item.produit_id || item.id || item.produit_nom}
          layout initial={reduceMotion?false:{opacity:0,y:10}} animate={{opacity:1,y:0}} exit={reduceMotion?{}:{opacity:0,y:-6}} transition={{duration:0.22}} className="rt-data-mobile-item">
          <div className="rt-data-mobile-top"><StockIdentity stock={item} preview={preview}/><span className={`rt-data-status rt-data-status-${statusOf(item)}`}><i/>{stockStatusLabel[statusOf(item)]}</span></div>
          <QuantityIndicator stock={item}/>
          <button type="button" onClick={onStocks}>Consulter cette référence <CaretRight size={15}/></button>
        </motion.article>)}</AnimatePresence>
      </div>
    </> : <div className="rt-data-empty"><div className="rt-data-empty-icon"><CheckCircle size={24}/></div>
      <h3>{stocks.length===0 ? 'Votre suivi commence ici' : filter==='out' ? 'Aucune rupture enregistrée' : 'Tout est au-dessus des seuils'}</h3>
      <p>{stocks.length===0 ? 'Importez une première facture ou ajoutez vos produits pour visualiser vos niveaux de stock.' : 'Changez de filtre pour consulter le reste de votre inventaire.'}</p>
      {stocks.length===0 && <button onClick={onStocks}>Ouvrir les stocks <ArrowRight size={15}/></button>}
    </div>}
    <footer className="rt-data-panel-footer"><span><span className="rt-data-footer-dot"/> Informations issues des stocks enregistrés</span><span>{filtered.length>8?`8 sur ${filtered.length} produits`:`${filtered.length} produit${filtered.length>1?'s':''}`}</span></footer>
  </section>;
}

export default function Overview({stocks=[],documents=[],user,onStocks,onStockAlerts,onImport,onPurchases,loading=false,error='',onRetry,preview=false,alerts=null,alertsError='',onPriorityAction,showDemoBrief=false}) {
  const lowStocks=stocks.filter(s=>statusOf(s)!=='ok');
  const outStocks=stocks.filter(s=>statusOf(s)==='out');
  const pending=pendingSupplierInvoices(documents);
  const firstName=(user?.full_name || 'à vous').split(' ')[0];
  const Heading=preview?'h2':'h1';
  const showBrief=Boolean(onPriorityAction) && (!preview || showDemoBrief) && ['patron','super_admin','gerant'].includes(user?.role);
  const metrics=[
    {label:'Références suivies',value:stocks.length,helper:'dans votre inventaire',icon:Package,action:onStocks,kind:'catalog'},
    {label:'Produits à surveiller',value:lowStocks.length,helper:outStocks.length?`${outStocks.length} rupture${outStocks.length>1?'s':''} détectée${outStocks.length>1?'s':''}`:'sous le seuil défini',icon:Warning,action:onStockAlerts||onStocks,kind:'risk'},
    {label:'Documents à vérifier',value:preview?2:pending.length,helper:'avant entrée en stock',icon:Receipt,action:onPurchases,kind:'documents'},
  ];
  const reduced=useReducedMotion();
  return <section className={`rt-overview rt-overview-v2${preview?' rt-overview-preview':''}`} aria-labelledby={preview?'preview-title':'overview-title'}>
    <div className="rt-overview-intro">
      <div><div className="rt-overview-context"><span className="rt-overview-context-mark"/> COCKPIT RESTAURANT <span className="rt-context-divider"/> VISIBILITÉ DU JOUR</div>
        <Heading id={preview?'preview-title':'overview-title'}>Bonjour {firstName}<span className="rt-overview-heading-punct">.</span></Heading>
        <p>Les bonnes informations pour piloter votre prochain service.</p></div>
      <div className="rt-overview-actions">
        {onImport && <button className="rt-overview-primary" onClick={onImport}><UploadSimple size={18}/> Importer une facture <ArrowUpRight size={17}/></button>}
        {onStocks && <button className="rt-overview-secondary" onClick={onStocks}>Voir l’inventaire <ArrowRight size={17}/></button>}
      </div>
    </div>
    {error ? <div className="rt-overview-error" role="alert">{error} <button onClick={onRetry}>Réessayer</button></div> : loading ?
      <div role="status" className="rt-overview-loading"><span/><span/><span/> Chargement des indicateurs…</div> : <>
      <div className="rt-dashboard-metrics">{metrics.map((item,i)=>{
        const Icon=item.icon;
        return <motion.button key={item.kind} type="button" onClick={item.action} className={`rt-dashboard-metric rt-dashboard-metric-${item.kind}`}
          initial={reduced?false:{opacity:0,y:10}} animate={{opacity:1,y:0}} transition={{duration:0.32,delay:i*.045}}
          whileHover={reduced?undefined:{y:-2}} whileTap={reduced?undefined:{scale:.995}}>
          <span className="rt-metric-top"><span>{item.label}</span><Icon size={20} weight="light"/></span>
          <span className="rt-metric-value"><AnimatedNumber value={item.value}/><ArrowUpRight size={18} weight="regular"/></span>
          <span className="rt-metric-bottom">{item.helper}</span>
        </motion.button>})}</div>
      <div className={`rt-dashboard-body${showBrief?' has-brief':''}`}>
        <StockTable stocks={stocks} preview={preview} onStocks={onStocks}/>
        {showBrief && <aside className="rt-dashboard-brief" aria-label="Actions du jour"><OperationalPriorities alerts={alerts} documents={documents} error={alertsError} onAction={onPriorityAction}/></aside>}
      </div>
    </>}
  </section>;
}
