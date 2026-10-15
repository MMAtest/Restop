import { API } from '../utils/api';
import React, {useCallback,useEffect,useMemo,useState} from 'react';
import axios from 'axios';
import {Receipt,ArrowsClockwise,DownloadSimple,ArrowUpRight,X,CalendarBlank,ChartBar,WarningCircle,CheckCircle} from '@phosphor-icons/react';
import {asList,number} from '../utils/contracts';
import {downloadCsv} from '../utils/export';


const formatMoney = value => Number(number(value,0)).toLocaleString('fr-FR',{style:'currency',currency:'EUR'});
const formatDate = value => {
  if(!value)return 'Date inconnue';
  const dt=new Date(value);
  return Number.isNaN(dt.getTime())?'Date inconnue':dt.toLocaleDateString('fr-FR',{day:'numeric',month:'short',year:'numeric'});
};
const dishesOf = report => Array.isArray(report.produits)?report.produits:[];

export default function HistoriqueZPage() {
  const [rapports,setRapports]=useState([]);
  const [loading,setLoading]=useState(true);
  const [error,setError]=useState('');
  const [selected,setSelected]=useState(null);
  const [updatedAt,setUpdatedAt]=useState(null);
  const fetchRapports=useCallback(async()=>{
    try{
      setLoading(true);
      const response=await axios.get(`${API}/rapports_z`);
      setRapports(asList(response.data));setError('');setUpdatedAt(new Date());
    }catch(_){setError('Impossible de charger les rapports Z. Vérifiez la connexion puis réessayez.');}
    finally{setLoading(false)}
  },[]);
  useEffect(()=>{
    fetchRapports();
    const timer=setInterval(()=>{if(!document.hidden)fetchRapports()},30000);
    const visibility=()=>{if(!document.hidden)fetchRapports()};
    document.addEventListener('visibilitychange',visibility);
    return()=>{clearInterval(timer);document.removeEventListener('visibilitychange',visibility)};
  },[fetchRapports]);
  const sorted=useMemo(()=>[...rapports].sort((a,b)=>new Date(b.date||0)-new Date(a.date||0)),[rapports]);
  const average=rapports.length?rapports.reduce((sum,item)=>sum+number(item.ca_total,0),0)/rapports.length:0;
  const chosen=selected ? rapports.find(item=>item.id===selected):null;
  return <section className="rt-module rt-z-history" aria-labelledby="rt-z-title">
    <header className="rt-module-heading"><div><p className="rt-module-kicker">CLÔTURE / CAISSE</p><h1 id="rt-z-title">Historique des rapports Z</h1><p>Consultez les clôtures, comparez les montants et exportez les données de caisse.</p></div>
      <div className="rt-module-actions"><button onClick={fetchRapports} disabled={loading} className="rt-control-secondary"><ArrowsClockwise size={17}/>{loading?'Chargement…':'Actualiser'}</button><button onClick={()=>downloadCsv('rapports-z.csv',['Date','CA total'],rapports.map(r=>[r.date,number(r.ca_total,0)]))} className="rt-control-primary" disabled={!rapports.length}><DownloadSimple size={17}/>Exporter CSV</button></div>
    </header>
    {error&&<div className="rt-inline-feedback is-error" role="alert"><WarningCircle size={19}/>{error}<button onClick={fetchRapports}>Réessayer</button></div>}
    <div className="rt-z-metrics"><div><span>Clôtures enregistrées</span><strong>{rapports.length}</strong><small>documents disponibles</small></div><div><span>CA moyen par clôture</span><strong>{rapports.length?formatMoney(average):'—'}</strong><small>sur les rapports chargés</small></div><div><span>Dernière clôture</span><strong className="rt-z-last-date">{sorted.length?formatDate(sorted[0].date):'—'}</strong><small>date du rapport Z</small></div></div>
    <div className="rt-data-surface"><header className="rt-data-surface-heading"><div><p className="rt-module-kicker">DOCUMENTS</p><h2>Clôtures disponibles</h2></div><span>{sorted.length} rapport{sorted.length>1?'s':''}</span></header>
      {loading&&!rapports.length ? <div className="rt-module-loading" role="status"><div className="rt-loading-bars"><i/><i/><i/></div>Chargement des rapports de caisse…</div> :
      sorted.length ? <div className="rt-z-list">{sorted.map((report,index)=><article className="rt-z-row" key={report.id||index}>
        <span className="rt-z-row-icon"><Receipt size={21}/></span><div className="rt-z-row-primary"><strong>Clôture du {formatDate(report.date)}</strong><small>{dishesOf(report).length} référence{dishesOf(report).length>1?'s':''} de plats · Rapport Z</small></div>
        <strong className="rt-z-row-money">{formatMoney(report.ca_total)}</strong>
        <button className="rt-z-details-button" onClick={()=>setSelected(report.id)} aria-label={`Consulter la clôture du ${formatDate(report.date)}`}>Consulter <ArrowUpRight size={17}/></button>
      </article>)}</div> : <div className="rt-module-empty"><CalendarBlank size={27}/><h3>Pas encore de rapport Z</h3><p>Les clôtures apparaîtront ici après l’import d’un rapport de caisse.</p></div>}
      <footer className="rt-data-surface-footer"><span><CheckCircle size={14}/> Données enregistrées</span><span>{updatedAt?`Actualisé à ${updatedAt.toLocaleTimeString('fr-FR',{hour:'2-digit',minute:'2-digit'})}`:'En attente de données'}</span></footer>
    </div>
    {chosen&&<div className="rt-detail-backdrop" onMouseDown={event=>{if(event.target===event.currentTarget)setSelected(null)}}><section className="rt-detail-panel" role="dialog" aria-modal="true" aria-labelledby="rt-z-details-title">
      <header><div><p className="rt-module-kicker">DÉTAIL DE CLÔTURE</p><h2 id="rt-z-details-title">Rapport Z du {formatDate(chosen.date)}</h2></div><button aria-label="Fermer les détails" onClick={()=>setSelected(null)}><X size={21}/></button></header>
      <div className="rt-detail-panel-content"><div className="rt-z-detail-total"><span>Chiffre d’affaires déclaré</span><strong>{formatMoney(chosen.ca_total)}</strong></div><h3>Produits enregistrés</h3>
        {dishesOf(chosen).length?<ul className="rt-z-dishes">{dishesOf(chosen).slice(0,50).map((item,index)=><li key={index}><span>{item.name||item.nom||'Plat sans nom'}</span><strong>{number(item.qty??item.quantite,1)} unité(s)</strong></li>)}</ul>:<p className="rt-detail-hint">Aucun détail de plat n’est associé à ce rapport.</p>}
        {dishesOf(chosen).length>50&&<p className="rt-detail-hint">Seuls les 50 premiers plats sont affichés dans cet aperçu.</p>}
      </div><footer><button className="rt-control-secondary" onClick={()=>setSelected(null)}>Fermer le détail</button></footer>
    </section></div>}
  </section>;
}
