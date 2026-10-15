import React,{useEffect,useId,useRef,useState} from 'react';
import {WarningCircle,X,Package,Trash} from '@phosphor-icons/react';
import './dialog-system.css';

/** A deliberate decision point for archive/restore/destructive operations.
 * The caller creates the action only after an explicit affirmative decision.
 */
export default function ActionDialog({request,onResolve}) {
 const id=useId(),initial=useRef(null),panel=useRef(null);
 const [reason,setReason]=useState('');
 const [typed,setTyped]=useState('');
 const options=request?.config;
 useEffect(()=>{setReason('');setTyped('')},[request]);
 useEffect(()=>{
  if(!request)return undefined;
  const previous=document.activeElement, prior=document.body.style.overflow;
  document.body.style.overflow='hidden';
  initial.current?.focus();
  const onKey=event=>{
   if(event.key==='Escape'){event.preventDefault();onResolve({confirmed:false});}
   if(event.key==='Tab'){
    const enabled=[...panel.current.querySelectorAll('button:not(:disabled),input:not(:disabled),textarea:not(:disabled)')];
    if(!enabled.length)return;
    const first=enabled[0],last=enabled[enabled.length-1];
    if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}
    else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}
   }
  };
  window.addEventListener('keydown',onKey);
  return()=>{window.removeEventListener('keydown',onKey);document.body.style.overflow=prior; if(previous?.isConnected)previous.focus()};
 },[request,onResolve]);
 if(!options)return null;
 const dangerous=options.dangerous===true;
 const allowed=!options.requireText || typed===options.requireText;
 return <div className="rt-decision-backdrop" onMouseDown={event=>{if(event.currentTarget===event.target)onResolve({confirmed:false})}}>
  <section ref={panel} className="rt-decision-card" role="dialog" aria-modal="true" aria-labelledby={`${id}-heading`} aria-describedby={`${id}-explanation`}>
   <div className="rt-decision-head"><span className={`rt-decision-glyph ${dangerous?'is-danger':''}`}>{dangerous?<Trash size={23}/>:<Package size={23}/>}</span>
    <button className="rt-decision-close" aria-label="Fermer la confirmation" onClick={()=>onResolve({confirmed:false})}><X size={21}/></button></div>
   <h2 id={`${id}-heading`}>{options.title}</h2><p id={`${id}-explanation`}>{options.description}</p>
   {dangerous&&<div className="rt-decision-warning" role="note"><WarningCircle size={18}/> Cette action ne peut pas être annulée depuis Restop. Vérifiez que la suppression est nécessaire.</div>}
   {options.askReason&&<label className="rt-decision-field">Motif de l’archivage (facultatif)<textarea value={reason} maxLength={500} rows={3} onChange={e=>setReason(e.target.value)} placeholder="Ex. : produit retiré de la carte"/></label>}
   {options.requireText&&<label className="rt-decision-field">Pour autoriser la suppression, saisissez <strong>{options.requireText}</strong><input type="text" value={typed} onChange={e=>setTyped(e.target.value)} autoComplete="off" spellCheck="false" aria-label={`Saisir ${options.requireText} pour confirmer`}/></label>}
   <footer><button ref={initial} type="button" className="rt-decision-cancel" onClick={()=>onResolve({confirmed:false})}>Annuler</button><button type="button" className={`rt-decision-confirm ${dangerous?'is-danger':''}`} disabled={!allowed} onClick={()=>onResolve({confirmed:true,reason:reason.trim()||null})}>{options.confirmLabel||(dangerous?'Supprimer définitivement':'Confirmer')}</button></footer>
  </section>
 </div>;
}
