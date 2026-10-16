import React, {useCallback, useEffect, useState} from 'react';
import axios from 'axios';
import TenantInvoicePanel from './TenantInvoicePanel';
import {API} from '../../utils/api';
import {ArrowLeft, ArrowRight, CheckCircle, WarningCircle, Truck, FileText, ShieldCheck} from '@phosphor-icons/react';
import './tenant-receiving.css';

// Exact decimal input conversion: no floating point stock or currency math.
export const toMilliunits = value => {
  const match=String(value).trim().match(/^(\d{1,9})(?:[.,](\d{1,3}))?$/);
  if(!match)return null;
  return Number(match[1])*1000+Number((match[2]||'').padEnd(3,'0'));
};
export const toCents = value => {
  const match=String(value).trim().match(/^(\d{1,8})(?:[.,](\d{1,2}))?$/);
  if(!match)return null;
  return Number(match[1])*100+Number((match[2]||'').padEnd(2,'0'));
};
const fromMilliunits=v=>(v/1000).toFixed(3);
const fromCents=v=>(v/100).toFixed(2);
const euros=v=>(v/100).toLocaleString('fr-FR',{style:'currency',currency:'EUR'});
const apiError=err=>typeof err?.response?.data?.detail==='string'?err.response.data.detail:err?.message||'Erreur de communication avec le serveur';
const makeKey=()=>`restop-receipt-${typeof crypto!=='undefined'&&crypto.randomUUID?crypto.randomUUID():`${Date.now()}-${Math.random().toString(36).slice(2)}`}`;

export default function TenantReceivingWizard(){
  const [orders,setOrders]=useState([]),[products,setProducts]=useState([]),[loading,setLoading]=useState(true),[busy,setBusy]=useState(false);
  const [selected,setSelected]=useState(null),[lines,setLines]=useState([]);
  const [invoice,setInvoice]=useState(''),[delivery,setDelivery]=useState(''),[key,setKey]=useState(makeKey);
  const [preview,setPreview]=useState(null),[result,setResult]=useState(null);
  const [accept,setAccept]=useState(false),[reason,setReason]=useState(''),[error,setError]=useState('');
  const [confirmReady,setConfirmReady]=useState(false);
  const [invoiceDocumentId,setInvoiceDocumentId]=useState(null);
  const load=useCallback(async()=>{
    setLoading(true);setError('');
    try{const [response,catalog]=await Promise.all([
      axios.get(`${API}/tenant/purchase-orders`),axios.get(`${API}/tenant/products`)]);
      setOrders(response.data||[]);setProducts(catalog.data||[])}
    catch(err){setError(`Module de réception indisponible : ${apiError(err)}.`)}
    finally{setLoading(false)}
  },[]);
  useEffect(()=>{load()},[load]);

  const choose=order=>{
    setSelected(order);setPreview(null);setResult(null);setError('');setInvoice('');setDelivery('');
    setKey(makeKey());setAccept(false);setReason('');setConfirmReady(false);setInvoiceDocumentId(null);
    setLines((order.lines||[]).filter(line=>line.quantity_milliunits>((order.received_milliunits_by_product||{})[line.product_id]||0))
      .map(line=>{
        const previously=(order.received_milliunits_by_product||{})[line.product_id]||0;
        const available=Math.max(0,line.quantity_milliunits-previously);
        return {product_id:line.product_id,name:products.find(p=>p.id===line.product_id)?.name||line.product_id.slice(0,8),unit:line.unit,
          ordered:available,received:fromMilliunits(available),invoiced:fromMilliunits(available),
          price:fromCents(line.unit_price_cents),included:true};
      }));
  };
  const editLine=(id,field,value)=>{setLines(old=>old.map(line=>line.product_id===id?{...line,[field]:value}:line));setPreview(null);setConfirmReady(false)};
  const buildPayload=()=>{
    if(invoiceDocumentId==='pending')throw Error('Vérifiez les informations de la facture importée avant de poursuivre.');
    const included=lines.filter(x=>x.included);
    if(!invoice.trim()||!delivery.trim())throw Error('Renseignez la référence du bon de livraison et celle de la facture vérifiée.');
    if(!included.length)throw Error('Sélectionnez au moins un produit livré.');
    const items=included.map(x=>{
      const delivered=toMilliunits(x.received),billed=toMilliunits(x.invoiced),price=toCents(x.price);
      if(!delivered||!billed||price===null)throw Error('Vérifiez les quantités et les prix : 3 décimales maximum pour les quantités, 2 pour les prix.');
      return {product_id:x.product_id,received_milliunits:delivered,invoiced_milliunits:billed,invoiced_unit_price_cents:price};
    });
    return {delivery_note_reference:delivery,invoice_reference:invoice,
      ...(invoiceDocumentId?{invoice_document_id:invoiceDocumentId}:{}),
      invoice_source:'human_verified',idempotency_key:key,lines:items,
      acknowledge_variances:accept,variance_reason:accept?reason.trim():null};
  };
  const previewReceipt=async()=>{
    setBusy(true);setError('');setConfirmReady(false);
    try{const payload=buildPayload();const response=await axios.post(`${API}/tenant/purchase-orders/${selected.id}/receipts/preview`,payload);setPreview(response.data)}
    catch(err){setError(apiError(err))}
    finally{setBusy(false)}
  };
  const confirmReceipt=async()=>{
    setBusy(true);setError('');
    try{
      const payload=buildPayload();
      const response=await axios.post(`${API}/tenant/purchase-orders/${selected.id}/receipts/confirm`,payload);
      setResult(response.data);setPreview(null);
    }catch(err){setError(`${apiError(err)} Si la connexion a été interrompue, ne changez pas la clé de réception avant vérification.`)}
    finally{setBusy(false)}
  };
  const approve=async()=>{
    setBusy(true);setError('');
    try{const response=await axios.post(`${API}/tenant/purchase-orders/${selected.id}/approve`);setSelected(response.data);await load()}
    catch(err){setError(apiError(err))}
    finally{setBusy(false)}
  };
  const back=()=>{setSelected(null);setPreview(null);setResult(null);load()};

  return <section className="rt-receiving" aria-label="Réception intelligente pilote">
    <header className="rt-receiving-hero"><div><span className="rt-receiving-eyebrow">MODULE PILOTE · MULTI-ÉTABLISSEMENTS</span>
      <h2>Réception fournisseur</h2><p>Commande interne, bon de livraison et facture : chaque écart est vérifié avant la mise en stock.</p>
      </div><Truck size={33} weight="light"/></header>
    <div className="rt-receiving-info"><ShieldCheck size={18}/><span>La facture est saisie après vérification humaine. L’extraction OCR automatique n’est pas encore raccordée à cette version isolée.</span></div>
    {error&&<p role="alert" className="rt-receiving-error"><WarningCircle size={17}/>{error}</p>}
    {loading?<p role="status" className="rt-receiving-empty">Chargement des commandes sécurisées…</p>:
    !selected?<>
      <div className="rt-receiving-sectionhead"><h3>Choisir une commande</h3><button onClick={load} disabled={busy}>Actualiser</button></div>
      {orders.filter(order=>['draft','approved','receiving'].includes(order.status)).length===0?
      <div className="rt-receiving-empty">Aucune commande interne en attente. Créez d’abord un brouillon dans le module Achats du pilote.</div>:
      <div className="rt-receiving-orders">{orders.filter(order=>['draft','approved','receiving'].includes(order.status)).map(order=>
       <button key={order.id} className="rt-receiving-order" onClick={()=>choose(order)}>
        <span><strong>{order.supplier_id.slice(0,8)} · {order.lines.length} référence(s)</strong><small>{order.id.slice(0,13)} · {euros(order.estimated_total_cents)}</small></span>
        <em>{order.status==='draft'?'À approuver':order.status==='receiving'?'Réception partielle':'Prête à recevoir'}</em><ArrowRight size={19}/>
       </button>)}</div>}
    </>:
    result?<div className="rt-receiving-success" role="status"><CheckCircle size={39}/><h3>Réception enregistrée</h3><p>Stock et mouvements confirmés par le serveur. {result.replayed?'Cette réception existait déjà : aucun stock ajouté une seconde fois.':'Le journal d’audit est disponible dans la liste des réceptions.'}</p>
      <strong>{result.order_status_after==='received'?'Commande entièrement reçue':'Commande encore partiellement reçue'}</strong><small>Identifiant de réception : {result.id}</small><button onClick={back}>Retour aux commandes</button></div>:
    <div className="rt-receiving-body">
      <button className="rt-receiving-back" onClick={back}><ArrowLeft size={17}/> Changer de commande</button>
      <div className="rt-receiving-sectionhead"><h3>Commande {selected.id.slice(0,12)}</h3><span>{selected.status==='draft'?'Approbation requise':selected.status==='receiving'?'Livraison partielle':'En attente de livraison'}</span></div>
      {selected.status==='draft'?<div className="rt-receiving-approval"><h4>Approbation interne nécessaire</h4><p>Cette étape ne transmet aucun message au fournisseur et n’ajoute rien en stock. Seule la direction peut approuver.</p><button onClick={approve} disabled={busy}>Approuver la commande</button></div>:
      <>
        <div className="rt-receiving-steps"><span>01 · Documents vérifiés</span><span>02 · Écarts</span><span>03 · Validation</span></div>
        <TenantInvoicePanel key={selected.id} orderId={selected.id} invoice={invoice} lines={lines} onInvoiceChange={value=>{setInvoice(value);setPreview(null)}} onReviewed={id=>{setInvoiceDocumentId(id);setPreview(null)}}/>
        <div className="rt-receiving-fields"><label>Référence bon de livraison<input value={delivery} onChange={e=>{setDelivery(e.target.value);setPreview(null)}} placeholder="BL-2026-…"/></label>
          <label>Référence facture vérifiée<input value={invoice} disabled={Boolean(invoiceDocumentId&&invoiceDocumentId!=='pending')} onChange={e=>{setInvoice(e.target.value);setPreview(null)}} placeholder="FAC-2026-…"/></label></div>
        <div className="rt-receiving-sectionhead"><h3>Produits et quantités</h3><small>Quantités dans l’unité fournisseur, prix en €</small></div>
        <div className="rt-receiving-lines">{lines.map(item=><div key={item.product_id} className="rt-receiving-line">
          <label className="rt-receiving-included"><input type="checkbox" checked={item.included} onChange={e=>editLine(item.product_id,'included',e.target.checked)}/><strong>{item.name}</strong><small>Reste à recevoir : {fromMilliunits(item.ordered)} {item.unit}</small></label>
          <div className="rt-receiving-linefields"><label>Livré ({item.unit})<input type="text" inputMode="decimal" value={item.received} disabled={!item.included} onChange={e=>editLine(item.product_id,'received',e.target.value)}/></label>
            <label>Facturé ({item.unit})<input type="text" inputMode="decimal" value={item.invoiced} disabled={!item.included||Boolean(invoiceDocumentId&&invoiceDocumentId!=='pending')} onChange={e=>editLine(item.product_id,'invoiced',e.target.value)}/></label>
            <label>PU facture (€)<input type="text" inputMode="decimal" value={item.price} disabled={!item.included||Boolean(invoiceDocumentId&&invoiceDocumentId!=='pending')} onChange={e=>editLine(item.product_id,'price',e.target.value)}/></label></div></div>)}</div>
        {preview&&<div className="rt-receiving-review" role="status"><h3><FileText size={19}/> Résultat du rapprochement</h3>
          <strong>Montant facturé sur les lignes reçues : {euros(preview.invoice_total_cents)}</strong>
          {preview.issues.length?<><p>{preview.issues.length} écart(s) à examiner :</p><ul>{preview.issues.map((issue,index)=><li key={`${issue.product_id}-${index}`}>{issue.product_id.slice(0,8)} — {issue.code.replaceAll('_',' ')}</li>)}</ul>
          <label className="rt-receiving-accept"><input type="checkbox" checked={accept} onChange={e=>setAccept(e.target.checked)}/> J’ai contrôlé et accepte les écarts signalés</label>
          {accept&&<label className="rt-receiving-reason">Motif obligatoire<textarea value={reason} onChange={e=>setReason(e.target.value)} rows={3} placeholder="Préciser le contrôle effectué et l’écart accepté"/></label>}</>:<p>Aucun écart détecté sur les lignes fournies. Vérifiez les pièces avant validation.</p>}
        </div>}
        <footer className="rt-receiving-actions"><button className="rt-receiving-secondary" onClick={previewReceipt} disabled={busy}>{busy?'Traitement…':'Vérifier les écarts'}</button>
          <button className="rt-receiving-primary" onClick={()=>setConfirmReady(true)} disabled={busy||!preview||(preview.issues.length>0&&(!accept||reason.trim().length<8))}>Continuer vers validation <ArrowRight size={16}/></button>
        </footer>
        {confirmReady&&<div className="rt-receiving-final" role="alert"><strong>Dernière vérification avant écriture en stock</strong>
          <p>Cette opération enregistrera définitivement une réception et augmentera les quantités selon les produits sélectionnés. Elle ne peut être annulée depuis ce module.</p>
          <div><button className="rt-receiving-secondary" onClick={()=>setConfirmReady(false)}>Revoir les documents</button>
          <button className="rt-receiving-primary" onClick={confirmReceipt} disabled={busy}>{busy?'Confirmation…':'Oui, confirmer la réception et le stock'}</button></div>
        </div>}
        <small className="rt-receiving-disclaimer">Aucun mouvement de stock n’est exécuté lors de la prévisualisation. La validation enregistre les mouvements et la réception dans une transaction MongoDB.</small>
      </>}
    </div>}
  </section>;
}
