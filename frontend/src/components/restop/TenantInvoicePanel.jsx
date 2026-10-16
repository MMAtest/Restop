import React,{useState} from 'react';
import axios from 'axios';
import {FilePdf,UploadSimple,CheckCircle,DownloadSimple,WarningCircle} from '@phosphor-icons/react';
import {API} from '../../utils/api';

const toMilliunits = value => {
  const m=String(value).trim().match(/^(\d{1,9})(?:[,.](\d{1,3}))?$/);
  return m?Number(m[1])*1000+Number((m[2]||'').padEnd(3,'0')):null;
};
const toCents = value => {
  const m=String(value).trim().match(/^(\d{1,8})(?:[,.](\d{1,2}))?$/);
  return m?Number(m[1])*100+Number((m[2]||'').padEnd(2,'0')):null;
};
const errorText=e=>typeof e.response?.data?.detail==='string'?e.response.data.detail:e.message||'Erreur de document';

export default function TenantInvoicePanel({orderId,lines,invoice,onInvoiceChange,onReviewed}){
  const [file,setFile]=useState(null),[invoiceDoc,setInvoiceDoc]=useState(null),[text,setText]=useState('');
  const [suggestions,setSuggestions]=useState({});
  const [note,setNote]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState('');
  const upload=async()=>{
    if(!file)return;
    if(file.size<1||file.size>8*1024*1024){setError('Le document doit peser entre 1 octet et 8 Mio.');return}
    setBusy(true);setError('');
    try{
      const payload=new FormData();payload.append('file',file);
      const response=await axios.post(`${API}/tenant/invoices/upload?order_id=${encodeURIComponent(orderId)}`,payload);
      setInvoiceDoc(response.data);onReviewed('pending');
      const info=await axios.get(`${API}/tenant/invoices/${response.data.id}`);
      setText(info.data.extracted_text||'');setSuggestions(info.data.suggestions||{});
      if(info.data.suggestions?.invoice_reference&&!invoice)onInvoiceChange(info.data.suggestions.invoice_reference);
    }catch(e){setError(errorText(e))}
    finally{setBusy(false)}
  };
  const review=async()=>{
    if(!invoiceDoc||invoiceDoc.status!=='needs_review')return;
    if(note.trim().length<8){setError('Expliquez le contrôle humain effectué (8 caractères minimum).');return}
    if(!invoice.trim()){setError('Référence facture requise pour vérifier le document.');return}
    const selected=lines.filter(x=>x.included);
    const checked=selected.map(x=>({product_id:x.product_id,invoiced_milliunits:toMilliunits(x.invoiced),invoiced_unit_price_cents:toCents(x.price)}));
    if(!checked.length||checked.some(x=>!x.invoiced_milliunits||x.invoiced_unit_price_cents===null)){
      setError('Vérifiez les quantités facturées et prix de chaque ligne avant validation.');return;
    }
    setBusy(true);setError('');
    try{
      const response=await axios.post(`${API}/tenant/invoices/${invoiceDoc.id}/review`,{
        invoice_reference:invoice,lines:checked,review_note:note.trim()});
      setInvoiceDoc(response.data);onReviewed(response.data.id);
    }catch(e){setError(errorText(e))}
    finally{setBusy(false)}
  };
  const download=async()=>{
    if(!invoiceDoc)return;
    setBusy(true);setError('');
    try{
      const response=await axios.get(`${API}/tenant/invoices/${invoiceDoc.id}/file`,{responseType:'blob'});
      const blob=new Blob([response.data],{type:'application/octet-stream'});
      const objectUrl=window.URL.createObjectURL(blob);
      const anchor=document.createElement('a');anchor.href=objectUrl;
      anchor.download=`facture-originale-${invoiceDoc.id}.${invoiceDoc.extension||'pdf'}`;
      document.body.appendChild(anchor);anchor.click();anchor.remove();
      window.setTimeout(()=>window.URL.revokeObjectURL(objectUrl),1000);
    }catch(e){setError(errorText(e))}
    finally{setBusy(false)}
  };
  return <section className="rt-invoice-panel" aria-label="Document facture isolé">
    <div className="rt-invoice-panel-title"><FilePdf size={20}/><div><h3>Pièce facture originale</h3><p>Le document est conservé dans l’espace du restaurant. L’extraction est une suggestion à vérifier.</p></div></div>
    {!invoiceDoc?<div className="rt-invoice-upload"><label>Déposer un PDF ou une image (8 Mio maximum)
      <input aria-label="Document de facture" type="file" accept=".pdf,.png,.jpg,.jpeg,.webp,application/pdf,image/png,image/jpeg,image/webp" onChange={e=>setFile(e.target.files?.[0]||null)}/></label>
      <button onClick={upload} disabled={!file||busy}><UploadSimple size={17}/>{busy?'Lecture…':'Importer et analyser'}</button></div>:<>
      <div className="rt-invoice-file"><span><CheckCircle size={18}/>{invoiceDoc.extension?.toUpperCase()} · SHA-256 {invoiceDoc.sha256?.slice(0,14)}… · {Math.ceil(invoiceDoc.size_bytes/1024)} Kio</span>
      <button onClick={download} disabled={busy}><DownloadSimple size={16}/> Original</button></div>
      <div className="rt-invoice-extraction"><span>Extraction : {invoiceDoc.extraction_engine==='pdf_embedded_text'?'texte du PDF':invoiceDoc.extraction_engine==='tesseract_image'?'OCR Tesseract':"texte indisponible — saisie manuelle"}</span>
        {text?<pre>{text.slice(0,3200)}</pre>:<p>Aucun texte fiable extrait. Contrôlez l’original et remplissez les lignes manuellement.</p>}
        {suggestions.potential_product_matches?.length>0&&<p className="rt-invoice-suggestions">Indices OCR non vérifiés : {suggestions.potential_product_matches.map(p=>p.name).join(' · ')}</p>}
      </div>
      {invoiceDoc.status==='reviewed'?<p className="rt-invoice-verified"><CheckCircle size={17}/> Document vérifié. La réception utilisera exactement les montants et quantités approuvés.</p>:
      invoiceDoc.status==='needs_review'?<div className="rt-invoice-verify"><label>Compte rendu du contrôle humain<textarea rows="2" value={note} onChange={e=>setNote(e.target.value)} placeholder="J’ai comparé le PDF, le bon de livraison et les lignes saisies…"/></label>
      <button onClick={review} disabled={busy}>{busy?'Vérification…':'Valider les données lues sur la facture'}</button></div>:<p className="rt-invoice-verified">Document déjà lié à une réception</p>}
    </>}
    {error&&<p className="rt-invoice-error" role="alert"><WarningCircle size={16}/>{error}</p>}
  </section>;
}
