import React,{useEffect,useRef,useState} from 'react';
import {X} from '@phosphor-icons/react';
import './dialog-system.css';

/** Progressive enhancement for the four legacy CRUD forms.
 * Scope labels, focus and scroll; keep their existing form submit handlers intact.
 */
export default function FormModal({title,onClose,children,wide=false,warnUnsavedOnClose=true}) {
 const panel=useRef(null),close=useRef(null);
 const onCloseRef=useRef(onClose);
 onCloseRef.current=onClose;
 const changed=useRef(false);
 const [discard,setDiscard]=useState(false);
 const discardRef=useRef(false);
 const requestClose=()=>{
  if(discardRef.current){setDiscard(false);discardRef.current=false;return;}
  if(warnUnsavedOnClose&&changed.current){setDiscard(true);discardRef.current=true;return;}
  onClose();
 };
 useEffect(()=>{
  const prior=document.body.style.overflow,previous=document.activeElement;
  document.body.style.overflow='hidden';
  // The legacy form used display-only labels. Associate each label to its nearby input.
  panel.current?.querySelectorAll('.form-group').forEach((group,i)=>{
   const label=group.querySelector('label.form-label'),control=group.querySelector('input,select,textarea');
   if(label&&control){if(!control.id)control.id=`rt-form-field-${i}`;label.htmlFor=control.id;}
  });
  (panel.current?.querySelector('input:not([type=hidden]),select,textarea')||close.current)?.focus();
  const keydown=event=>{
   if(event.key==='Escape'){event.preventDefault();if(discardRef.current){discardRef.current=false;setDiscard(false)}else if(warnUnsavedOnClose&&changed.current){discardRef.current=true;setDiscard(true)}else onCloseRef.current();}
   if(event.key==='Tab'){
    const enabled=[...panel.current.querySelectorAll('input:not(:disabled),select:not(:disabled),textarea:not(:disabled),button:not(:disabled)')].filter(e=>e.getClientRects().length||process.env.NODE_ENV==='test');
    if(!enabled.length)return;
    const first=enabled[0],last=enabled[enabled.length-1];
    if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}
    else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}
   }
  };
  window.addEventListener('keydown',keydown);
  return()=>{document.body.style.overflow=prior;window.removeEventListener('keydown',keydown);if(previous?.isConnected)previous.focus();};
 // onClose changes identity when parent rerenders; do not reset focus on every keystroke.
 },[]);
 return <div className="modal-overlay rt-form-dialog-overlay" onMouseDown={event=>{if(event.target===event.currentTarget)requestClose()}}>
  <section className={`modal-content rt-form-dialog-content ${wide?'is-wide':''}`} ref={panel} role="dialog" aria-modal="true" aria-label={title}>
   <button ref={close} type="button" className="rt-form-dialog-close" aria-label="Fermer le formulaire" onClick={requestClose}><X size={20}/></button>
   {discard&&<div className="rt-form-unsaved-warning" role="alert">
     <strong>Des modifications ne sont pas enregistrées.</strong>
     <p>Voulez-vous quitter le formulaire et perdre vos modifications ?</p>
     <div><button type="button" onClick={()=>{discardRef.current=false;setDiscard(false)}}>Continuer la saisie</button><button type="button" onClick={onClose}>Quitter sans enregistrer</button></div>
   </div>}
   <div onChangeCapture={()=>{changed.current=true}}>{children}</div>
  </section>
 </div>;
}
