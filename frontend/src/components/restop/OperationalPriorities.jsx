import React, {useMemo, useState} from 'react';
import {ArrowRight, Warning, CalendarX, TrendUp, Package, Receipt, ClockCounterClockwise, CheckCircle, Info} from '@phosphor-icons/react';
import {buildOperationalBrief} from '../../utils/operationalBrief.mjs';

const icons = {dlc:CalendarX,stock:Package,price:TrendUp,invoice:Receipt,unused:ClockCounterClockwise};

export default function OperationalPriorities({alerts, documents, onAction, error}) {
  const [expanded,setExpanded] = useState(false);
  const brief = useMemo(() => buildOperationalBrief(alerts || {},documents),[alerts,documents]);
  const visible = expanded ? brief.actions : brief.actions.slice(0,4);
  return <section className="rt-priorities" aria-labelledby="rt-priority-title">
    <div className="rt-priorities-heading">
      <div>
        <p className="rt-eyebrow">LE BRIEF OPÉRATIONNEL</p>
        <h2 id="rt-priority-title">Ce qui mérite votre attention</h2>
        <p>Des recommandations calculées sur vos données enregistrées. Aucun achat ni mouvement de stock n’est effectué automatiquement.</p>
      </div>
      <span className="rt-priorities-count" aria-label={`${brief.actions.length} actions suggérées`}>
        <strong>{brief.actions.length}</strong><small>action{brief.actions.length === 1 ? '' : 's'}</small>
      </span>
    </div>
    {error && <div role="status" className="rt-priorities-warning"><Info size={18} /> Certaines alertes (DLC et prix fournisseurs) sont momentanément indisponibles. Affichage limité aux factures en attente.</div>}
    {alerts === null && !error && <div role="status" className="rt-priorities-warning"><Info size={18} /> Analyse des risques non chargée. Les factures restent visibles.</div>}
    {brief.actions.length === 0 ? (
      <div className="rt-priorities-empty"><CheckCircle size={23}/><div><strong>Aucune action détectée dans les données disponibles.</strong><p>Continuez à enregistrer les factures, mouvements et inventaires pour améliorer ce suivi.</p></div></div>
    ) : <>
      <div className="rt-priorities-list">
        {visible.map(item => {
          const Icon = icons[item.kind] || Warning;
          return <article key={item.id} className={`rt-priority-row rt-priority-${item.kind}`}>
            <span className="rt-priority-icon"><Icon size={21} weight="regular" /></span>
            <div className="rt-priority-details">
              <div className="rt-priority-title-line"><strong>{item.title}</strong>{item.priority <= 2 && <span className="rt-priority-flag">À traiter</span>}</div>
              <p>{item.detail}</p>
            </div>
            <button className="rt-priority-action" onClick={() => onAction(item.action)}>{item.label}<ArrowRight size={16}/></button>
          </article>;
        })}
      </div>
      {brief.actions.length > 4 && <button className="rt-priorities-more" onClick={() => setExpanded(value => !value)} aria-expanded={expanded}>{expanded ? 'Afficher moins' : `Voir les ${brief.actions.length} actions`}</button>}
    </>}
    <p className="rt-priorities-footnote">Le brief signale des anomalies potentielles : vérifiez les quantités, les dates, les prix et la qualité des données avant toute décision.</p>
  </section>;
}
