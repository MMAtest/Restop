import React, {useState} from 'react';
import {Link} from 'react-router-dom';
import {ArrowLeft, ArrowRight, Receipt, ShieldCheck, Sparkle, Package} from '@phosphor-icons/react';
import Brand from '../components/restop/Brand';
import Overview, {previewStocks} from '../components/restop/Overview';
import InvoiceValidationModal from '../components/InvoiceValidationModal';
import '../styles/workspace.css';
import '../styles/demo.css';

// All data on this page is static and fictitious; it has no back-end access.
export const DEMO_INVOICE = {
  supplier_name:'Primeur du Port (exemple)', is_new_supplier:false,
  supplier_id:'s-demo', facture_date:'2026-10-15', numero_facture:'SIM-2026-1042',
  total_ht:52.80,total_ttc:58.08,
  audit_warnings:[{code:'line_mismatch',message:'Une ligne nécessite une vérification des unités et du conditionnement.'}],
  items:[
    {ocr_name:'Tomates fraîches colis',ocr_qty:2,ocr_unit:'colis',ocr_price:12.50,ocr_total:25.00,
     product_id:'tomate',product_name:'Tomates fraîches',status:'matched',confidence:0.98,final_qty:2,final_unit:'colis'},
    {ocr_name:'Basilic frais',ocr_qty:10,ocr_unit:'botte',ocr_price:1.80,ocr_total:18.00,
     status:'ambiguous',confidence:0.58,final_qty:10,final_unit:'botte'},
    {ocr_name:'Mozzarella di bufala',ocr_qty:2,ocr_unit:'kg',ocr_price:4.90,ocr_total:9.80,
     product_id:'mozza',product_name:'Mozzarella di bufala',status:'matched',confidence:0.95,final_qty:2,final_unit:'kg'}
  ]
};

const DEMO_ALERTS = {
  expiring_products:[{product_name:'Mozzarella di bufala',days_to_expiry:1,quantity:1.5,batch_id:'lot-001'}],
  low_stock_items:[{product_name:'Tomates fraîches',current_quantity:8,minimum_quantity:20}],
  price_anomalies:[{product_name:'Basilic frais',reference_price:1.50,actual_price:1.80,supplier_name:'Primeur du Port'}]
};
const DEMO_DOCS = [{id:'demo-ocr-invoice',type_document:'facture_fournisseur',statut:'traite'}];

export default function DemoPage() {
  const [showWizard,setShowWizard] = useState(false);
  const [completed,setCompleted] = useState(false);
  const [stockNotice,setStockNotice] = useState(false);
  const openWizard = () => {setCompleted(false);setShowWizard(true)};
  const openStocks = () => {setStockNotice(true);document.getElementById('demo-stocks')?.scrollIntoView({behavior:'smooth',block:'start'});};
  const onPriorityAction = action => action === 'stocks' ? openStocks() : openWizard();
  return <div className="rt-demo-page">
    <header className="rt-demo-topbar">
      <Link to="/" className="rt-demo-home"><Brand/><span><ArrowLeft size={16}/> Retour au site</span></Link>
      <div className="rt-demo-indicator"><ShieldCheck size={17}/> Démonstration isolée · Données fictives</div>
      <Link to="/connexion" className="rt-demo-signin">Connexion <ArrowRight size={16}/></Link>
    </header>
    <main className="rt-demo-main">
      <div className="rt-demo-intro">
        <p className="rt-eyebrow">RESTOP 2026 · DÉMONSTRATION INTERACTIVE</p>
        <h1>La gestion commence par<br/><span>les bonnes décisions.</span></h1>
        <p>Explorez un tableau de bord réaliste et testez les trois étapes de validation OCR. Aucun compte, aucun document réel et aucun appel à un service IA.</p>
        <button className="rt-button rt-peach" onClick={openWizard}><Receipt size={20}/> Tester le wizard OCR <ArrowRight size={18}/></button>
      </div>
      {completed && <div className="rt-demo-completed" role="status"><Sparkle size={21}/> Parcours terminé. En mode démonstration, aucune écriture en base n’a été effectuée. <button onClick={openWizard}>Rejouer le scénario</button></div>}
      <div className="rt-demo-grid">
        <div className="rt-demo-panel" id="demo-stocks">
          <div className="rt-demo-section-head"><span><Package size={20}/> Vue d'ensemble</span><small>Simulation d'un établissement indépendant</small></div>
          {stockNotice && <div className="rt-demo-stock-notice" role="status">Stocks fictifs : ce tableau montre des seuils d’alerte et des quantités de démonstration, sans modification possible.</div>}
          <Overview stocks={previewStocks} documents={DEMO_DOCS} user={{role:'patron',full_name:'Camille'}} onStocks={openStocks} onStockAlerts={openStocks} onImport={openWizard} onPurchases={openWizard} alerts={DEMO_ALERTS} onPriorityAction={onPriorityAction}/>
        </div>
      </div>
      <section className="rt-demo-explain" aria-label="Comment tester le wizard">
        <h2>Le scénario à essayer</h2>
        <div className="rt-demo-explain-steps">
          <div><strong>01</strong><h3>Confirmer le fournisseur</h3><p>La référence sert à éviter les doublons de facture.</p></div>
          <div><strong>02</strong><h3>Corriger les lignes</h3><p>Modifiez prix et quantités, et vérifiez les correspondances avec le stock.</p></div>
          <div><strong>03</strong><h3>Valider en connaissance de cause</h3><p>Contrôlez les anomalies et terminez la simulation sans risque.</p></div>
        </div>
      </section>
    </main>
    {showWizard && <InvoiceValidationModal documentId="demo-ocr-invoice" previewData={DEMO_INVOICE}
      produitsList={[
        {id:'tomate',nom:'Tomates fraîches',unite:'kg'},
        {id:'mozza',nom:'Mozzarella di bufala',unite:'kg'},
        {id:'basilic',nom:'Basilic frais',unite:'botte'}
      ]}
      fournisseursList={[{id:'s-demo',nom:'Primeur du Port (exemple)'}]}
      onSuccess={() => setCompleted(true)} onClose={() => setShowWizard(false)}/>}
  </div>;
}
