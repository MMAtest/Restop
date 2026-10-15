import React from 'react';
import {Package,Warning,ClockCountdown,Coins,ArrowUpRight} from '@phosphor-icons/react';
import './stock-kpi-bar.css';

export const expiringWithin = (entries=[],days=3,now=new Date())=>entries.filter(p=>{
  if(!p.dlc)return false;
  const date=new Date(p.dlc);
  return !Number.isNaN(date.getTime())&&date.getTime() < now.getTime()+days*86400000;
});

export default function StockKpiBar({stocks=[],products=[],preparations=[],activeFilter='all',onAll,onCritical,onDlc}) {
 const low=stocks.filter(s=>Number(s.quantite_actuelle)<=Number(s.quantite_min)&&Number.isFinite(Number(s.quantite_min)));
 const expiring=expiringWithin(preparations);
 const total=stocks.reduce((sum,stock)=>{
  const product=products.find(p=>p.id===stock.produit_id);
  const qty=Number(stock.quantite_actuelle),price=Number(product?.prix_achat??product?.reference_price);
  return sum+(Number.isFinite(qty)&&Number.isFinite(price)&&qty>0&&price>=0?qty*price:0);
 },0);
 const values=[
  {id:'all',title:'Références en stock',amount:stocks.length,helper:'Voir l’inventaire',icon:Package,action:onAll},
  {id:'critical',title:'Stocks à surveiller',amount:low.length,helper:'Voir les seuils dépassés',icon:Warning,action:onCritical},
  {id:'valuation',title:'Valorisation indicative',amount:total.toLocaleString('fr-FR',{style:'currency',currency:'EUR',maximumFractionDigits:0}),helper:'Sur la base des prix renseignés',icon:Coins},
  {id:'dlc',title:'DLC proches ou dépassées',amount:expiring.length,helper:'Lots à contrôler sous 3 jours',icon:ClockCountdown,action:onDlc}
 ];
 return <section aria-label="Indicateurs de stock" className="rt-stock-kpi-grid">
  {values.map(({id,title,amount,helper,icon:Icon,action})=>{
   const inner=<><span className="rt-stock-kpi-title">{title}<Icon size={19} weight="light"/></span>
    <strong className="rt-stock-kpi-value">{amount}</strong><span className="rt-stock-kpi-foot">{helper}{action&&<ArrowUpRight size={14}/>}</span></>;
   return action?<button key={id} type="button" className={`rt-stock-kpi rt-stock-kpi-${id} ${activeFilter===id?'is-active':''}`}
     aria-pressed={activeFilter===id} onClick={action}>{inner}</button>:
     <div key={id} className="rt-stock-kpi rt-stock-kpi-readonly" aria-label={`${title} : ${amount}. ${helper}`}>{inner}</div>;
  })}
 </section>;
}
