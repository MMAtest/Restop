import React, {useMemo,useState} from 'react';
import {motion, AnimatePresence, useReducedMotion} from 'motion/react';
import {ArrowUpRight, CaretDown, Warning, CalendarX, TrendUp, Package, Receipt, ClockCounterClockwise, CheckCircle, Info} from '@phosphor-icons/react';
import {buildOperationalBrief} from '../../utils/operationalBrief.mjs';

const icons={dlc:CalendarX,stock:Package,price:TrendUp,invoice:Receipt,unused:ClockCounterClockwise};

export default function OperationalPriorities({alerts,documents,onAction,error}) {
  const [expanded,setExpanded]=useState(false);
  const reduced=useReducedMotion();
  const brief=useMemo(()=>buildOperationalBrief(alerts || {},documents),[alerts,documents]);
  const visible=expanded?brief.actions:brief.actions.slice(0,4);
  return <section className="rt-daily-brief" aria-labelledby="rt-priority-title">
    <header className="rt-daily-header">
      <div><span className="rt-panel-eyebrow">VOTRE RADAR</span><h2 id="rt-priority-title">À traiter aujourd’hui</h2><p>Des signaux concrets, pas des chiffres décoratifs.</p></div>
      <span className="rt-daily-tally" aria-label={`${brief.actions.length} actions suggérées`}>{brief.actions.length}<small>signal{brief.actions.length>1?'s':''}</small></span>
    </header>
    {error && <div role="status" className="rt-daily-warning"><Info size={17}/> Certaines analyses sont indisponibles. Les factures restent visibles.</div>}
    {alerts===null && !error && <div role="status" className="rt-daily-warning"><Info size={17}/> Alertes non chargées ; vérifiez les stocks et factures directement.</div>}
    {brief.actions.length===0 ? <div className="rt-daily-empty"><CheckCircle size={23}/><strong>Rien de prioritaire dans les données disponibles.</strong><p>Les alertes apparaîtront à mesure que vous enregistrerez vos lots et mouvements.</p></div> :
      <div className="rt-daily-feed"><AnimatePresence mode="popLayout" initial={false}>{visible.map((item,index)=>{
        const Icon=icons[item.kind]||Warning;
        return <motion.article layout key={item.id} className="rt-daily-item" initial={reduced?false:{opacity:0,y:8}} animate={{opacity:1,y:0}} exit={reduced?{}:{opacity:0,y:-5}} transition={{duration:0.24,delay:index*.02}}>
          <div className="rt-daily-line"><span className={`rt-daily-glyph rt-daily-glyph-${item.kind}`}><Icon size={20} weight="regular"/></span><span className="rt-daily-item-content"><span className="rt-daily-item-label">{item.priority<=2?'ATTENTION REQUISE':'À VÉRIFIER'}</span><strong>{item.title}</strong><small>{item.detail}</small><button type="button" onClick={()=>onAction(item.action)}>{item.label} <ArrowUpRight size={15}/></button></span></div>
        </motion.article>})}</AnimatePresence></div>}
    {brief.actions.length>4 && <button className="rt-daily-more" type="button" onClick={()=>setExpanded(!expanded)} aria-expanded={expanded}>{expanded?'Réduire la liste':`Afficher les ${brief.actions.length} signaux`} <CaretDown size={15} style={{transform:expanded?'rotate(180deg)':'none'}}/></button>}
    <footer className="rt-daily-footnote">À confirmer sur le terrain avant toute action. Aucun achat ou mouvement de stock automatique.</footer>
  </section>;
}
