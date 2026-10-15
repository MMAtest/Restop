import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ProgressBar from './ProgressBar';
import { asList, number } from '../utils/contracts';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Hook pour détecter la taille d'écran
const useIsMobile = () => {
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);
  
  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth <= 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  
  return isMobile;
};

// VERSION MOBILE - ITEM EN CARTE (déplacé en dehors pour éviter les re-rendus)
const MobileItemCard = ({ item, index, handleItemChange, handleDeleteItem, produitsList }) => (
  <div style={{
    background: item.selected_product_id ? '#fff' : '#fff7ed',
    border: '1px solid #e2e8f0',
    borderRadius: '8px',
    padding: '12px',
    position: 'relative'
  }}>
    {/* Bouton supprimer en haut à droite */}
    <button 
      onClick={() => handleDeleteItem(index)}
      style={{
        position: 'absolute',
        top: '8px',
        right: '8px',
        background: '#fee2e2',
        color: '#dc2626',
        border: 'none',
        borderRadius: '4px',
        width: '28px',
        height: '28px',
        cursor: 'pointer',
        fontSize: '16px'
      }}
    >
      🗑️
    </button>

    {/* Nom du produit */}
    <div style={{marginBottom: '10px'}}>
      <label style={{display: 'block', fontSize: '11px', color: '#64748b', marginBottom: '4px'}}>Nom du produit</label>
      <input 
        type="text" 
        value={item.final_name}
        onChange={(e) => handleItemChange(index, 'final_name', e.target.value)}
        style={{
          width: '100%',
          padding: '8px',
          border: '1px solid #cbd5e1',
          borderRadius: '6px',
          fontSize: '14px',
          fontWeight: 'bold'
        }}
        placeholder="Nom du produit"
      />
      <div style={{fontSize: '10px', color: '#94a3b8', marginTop: '2px'}}>
        Lu par OCR: {item.ocr_name}
      </div>
    </div>

    {/* Correspondance stock */}
    <div style={{marginBottom: '10px'}}>
      <label style={{display: 'block', fontSize: '11px', color: '#64748b', marginBottom: '4px'}}>Correspondance Stock</label>
      <select 
        style={{
          width: '100%',
          padding: '8px',
          borderRadius: '6px',
          border: '1px solid #cbd5e1',
          fontSize: '14px'
        }}
        value={item.selected_product_id}
        onChange={(e) => handleItemChange(index, 'selected_product_id', e.target.value)}
      >
        <option value="">Créer nouveau</option>
        {produitsList.map(p => (
          <option key={p.id} value={p.id}>{p.nom}</option>
        ))}
      </select>
    </div>

    {/* Ligne des 3 champs : Qté, Unité, Prix - Largeurs optimisées */}
    <div style={{display: 'grid', gridTemplateColumns: '70px 90px 1fr', gap: '6px', marginBottom: '10px'}}>
      <div>
        <label style={{display: 'block', fontSize: '10px', color: '#64748b', marginBottom: '2px', fontWeight: '600'}}>Qté</label>
        <input 
          type="number" 
          step="0.1"
          style={{
            width: '100%',
            padding: '6px 2px',
            textAlign: 'center',
            border: '1px solid #cbd5e1',
            borderRadius: '4px',
            fontSize: '13px'
          }}
          value={item.final_qty}
          onChange={(e) => handleItemChange(index, 'final_qty', parseFloat(e.target.value))}
        />
      </div>

      <div>
        <label style={{display: 'block', fontSize: '10px', color: '#64748b', marginBottom: '2px', fontWeight: '600'}}>Unité</label>
        <select
          style={{
            width: '100%',
            padding: '6px 2px',
            border: '1px solid #cbd5e1',
            borderRadius: '4px',
            fontSize: '11px'
          }}
          value={item.final_unit}
          onChange={(e) => handleItemChange(index, 'final_unit', e.target.value)}
        >
          <option value="pièce">Pce</option>
          <option value="kg">Kg</option>
          <option value="g">g</option>
          <option value="L">L</option>
          <option value="colis">Colis</option>
          <option value="botte">Botte</option>
        </select>
      </div>

      <div>
        <label style={{display: 'block', fontSize: '10px', color: '#64748b', marginBottom: '2px', fontWeight: '600'}}>Prix €</label>
        <input 
          type="number" 
          step="0.01"
          style={{
            width: '100%',
            padding: '6px 4px',
            textAlign: 'right',
            border: '1px solid #cbd5e1',
            borderRadius: '4px',
            fontSize: '13px'
          }}
          value={item.final_price}
          onChange={(e) => handleItemChange(index, 'final_price', parseFloat(e.target.value))}
        />
      </div>
    </div>

    {/* Total */}
    <div style={{marginBottom: '10px', textAlign: 'right', fontSize: '16px', fontWeight: 'bold', color: '#059669'}}>
      Total: {(item.final_qty * item.final_price).toFixed(2)} €
    </div>

    {/* DLC & Lot */}
    <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px'}}>
      <div>
        <label style={{display: 'block', fontSize: '11px', color: '#64748b', marginBottom: '4px'}}>DLC</label>
        <input 
          type="date" 
          style={{
            width: '100%',
            padding: '6px',
            border: '1px solid #cbd5e1',
            borderRadius: '6px',
            fontSize: '13px'
          }}
          value={item.dlc}
          onChange={(e) => handleItemChange(index, 'dlc', e.target.value)}
        />
      </div>
      <div>
        <label style={{display: 'block', fontSize: '11px', color: '#64748b', marginBottom: '4px'}}>N° Lot</label>
        <input 
          type="text" 
          placeholder="N° Lot"
          style={{
            width: '100%',
            padding: '6px',
            border: '1px solid #cbd5e1',
            borderRadius: '6px',
            fontSize: '13px'
          }}
          value={item.batch_number}
          onChange={(e) => handleItemChange(index, 'batch_number', e.target.value)}
        />
      </div>
    </div>
  </div>
);

const InvoiceValidationModal = ({ documentId, onClose, onSuccess, onRefresh, produitsList = [], fournisseursList = [], previewData = null }) => {
  const [loading, setLoading] = useState(true);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState(null);
  const [items, setItems] = useState([]);
  const isMobile = useIsMobile();
  const [showProgressBar, setShowProgressBar] = useState(false);
  const [aiPowered, setAiPowered] = useState(false);
  const [showAiSuggestion, setShowAiSuggestion] = useState(false);
  
  // Gestion du fournisseur
  const [selectedSupplierId, setSelectedSupplierId] = useState('');
  const [newSupplierName, setNewSupplierName] = useState('');
  const [newSupplierCategory, setNewSupplierCategory] = useState('frais');
  const [editableDate, setEditableDate] = useState('');
  const [editableNumero, setEditableNumero] = useState('');
  const [wizardStep, setWizardStep] = useState(0);
  const [wizardError, setWizardError] = useState('');
  const [wizardNotice, setWizardNotice] = useState('');
  const [acknowledged, setAcknowledged] = useState(false);
  const [successStats, setSuccessStats] = useState(null);


  // Charger l'analyse au montage
  useEffect(() => {
    const fetchAnalysis = async () => {
      // Afficher la barre de progression immédiatement
      setShowProgressBar(true);

      try {
        const response = previewData ? { data: previewData } : await axios.post(`${API}/ocr/analyze-facture/${documentId}`);
        const data = response.data;
        setAnalysis(data);
        setWizardNotice('Analyse reçue : commencez par vérifier le fournisseur et la référence de facture.');

        
        // Logique Fournisseur
        if (data.supplier_id) {
            setSelectedSupplierId(data.supplier_id);
            setNewSupplierName(data.supplier_name);
        } else {
            setSelectedSupplierId('new');
            setNewSupplierName(data.supplier_name || 'Nouveau Fournisseur');
        }
        
        // Initialiser date et numéro éditables
        setEditableDate(data.facture_date || '');
        setEditableNumero(data.numero_facture || '');

        // Logique Produits
        const initializedItems = asList(data.items).map(item => {
          const productName = String((item.status === 'matched' ? item.product_name : item.ocr_name) || item.ocr_name || 'Produit');
          const dlc = item.dlc || '';
          
          // Générer automatiquement un numéro de lot si une DLC est détectée
          let batchNumber = item.batch_number || '';
          if (dlc && !batchNumber) {
            const dlcDate = dlc.replace(/-/g, '');
            const productCode = productName.substring(0, 3).toUpperCase().replace(/[^A-Z0-9]/g, 'X');
            const randomSuffix = Math.floor(Math.random() * 100).toString().padStart(2, '0');
            batchNumber = `LOT-${dlcDate}-${productCode}${randomSuffix}`;
          }
          
          return {
            ...item,
            selected_product_id: item.status === 'matched' ? item.product_id : '', 
            final_name: productName,
            final_qty: number(item.ocr_qty, 1),
            final_unit: item.ocr_unit || 'pièce',
            final_price: number(item.ocr_price),
            batch_number: batchNumber,
            dlc: dlc
          };
        });
        setItems(initializedItems);
        
        // Calculer le score de qualité et proposer Joker IA si nécessaire
        const totalItems = initializedItems.length;
        const matchedItems = initializedItems.filter(item => item.status === 'matched').length;
        const matchRate = totalItems > 0 ? matchedItems / totalItems : 0;
        
        // Proposer Joker IA si moins de 80% de correspondances OU nouveau fournisseur
        const isNewSupplier = data.is_new_supplier;
        if ((matchRate < 0.8 || isNewSupplier) && totalItems > 0 && !data.ai_powered) {
          setShowAiSuggestion(true);
          console.log(`Taux de correspondance: ${(matchRate * 100).toFixed(0)}%. Nouveau fournisseur: ${isNewSupplier}. Joker IA suggéré.`);
        }
        
        setShowProgressBar(false);
        setLoading(false);
      } catch (err) {
        console.error("Erreur analyse:", err);
        setShowProgressBar(false);
        setError("Impossible d'analyser la facture.");
        setLoading(false);
      }
    };
    fetchAnalysis();
  }, [documentId, previewData]);

  const handleReanalyzeWithAI = async () => {
    if (previewData) {
      setWizardNotice('La relecture IA est désactivée dans la démonstration. Aucun document n’est envoyé à un service externe.');
      return;
    }
    setLoading(true);
    setWizardError('');
    setWizardNotice('Nouvelle lecture OCR en cours. Vérifiez les résultats avant de poursuivre.');
    setShowProgressBar(true);
    setShowAiSuggestion(false);
    
    try {
      const response = await axios.post(`${API}/ocr/analyze-facture-ai/${documentId}`);
      const data = response.data;
      
      setAnalysis(data);
      setAiPowered(true);
      
      // Logique Fournisseur
      if (data.supplier_id) {
          setSelectedSupplierId(data.supplier_id);
          setNewSupplierName(data.supplier_name);
      } else {
          setSelectedSupplierId('new');
          setNewSupplierName(data.supplier_name || 'Nouveau Fournisseur');
      }
      
      // Initialiser date et numéro éditables
      setEditableDate(data.facture_date || '');
      setEditableNumero(data.numero_facture || '');

      // Logique Produits avec DLC auto-générée par Gemini
      const initializedItems = asList(data.items).map(item => {
        const productName = String((item.status === 'matched' ? item.product_name : item.ocr_name) || item.ocr_name || 'Produit');
        const dlc = item.dlc || '';
        
        // Générer lot si DLC présente
        let batchNumber = item.batch_number || '';
        if (dlc && !batchNumber) {
          const dlcDate = dlc.replace(/-/g, '');
          const productCode = productName.substring(0, 3).toUpperCase().replace(/[^A-Z0-9]/g, 'X');
          const randomSuffix = Math.floor(Math.random() * 100).toString().padStart(2, '0');
          batchNumber = `LOT-${dlcDate}-${productCode}${randomSuffix}`;
        }
        
        return {
          ...item,
          selected_product_id: item.status === 'matched' ? item.product_id : '', 
          final_name: productName,
          final_qty: number(item.ocr_qty, 1),
          final_unit: item.ocr_unit || 'pièce',
          final_price: number(item.ocr_price),
          batch_number: batchNumber,
          dlc: dlc
        };
      });
      
      setItems(initializedItems);
      setShowProgressBar(false);
      setLoading(false);
      
      // Rafraîchir la liste des documents pour afficher le montant mis à jour
      if (onRefresh) {
        onRefresh();
      }
      
      // Afficher un message de succès
      const matchedCount = initializedItems.filter(i => i.status === 'matched').length;
      setWizardNotice(`Nouvelle lecture terminée : ${matchedCount} produit(s) rapproché(s) sur ${initializedItems.length}. Vérifiez chaque donnée avant import.`);
      
    } catch (err) {
      console.error("Erreur Joker IA:", err);
      setShowProgressBar(false);
      setLoading(false);
      setWizardError("Nouvelle lecture impossible : " + (err.response?.data?.detail || err.message));
    }
  };

  const handleItemChange = (index, field, value) => {
    const updatedItems = [...items];
    updatedItems[index][field] = value;
    
    // Si on change la DLC, générer automatiquement un numéro de lot
    if (field === 'dlc' && value) {
      // Format du lot : LOT-YYYYMMDD-XXX (XXX = 3 premiers caractères du nom du produit)
      const dlcDate = value.replace(/-/g, ''); // Format YYYYMMDD
      const productName = updatedItems[index].final_name || 'PRD';
      const productCode = productName.substring(0, 3).toUpperCase().replace(/[^A-Z0-9]/g, 'X');
      const randomSuffix = Math.floor(Math.random() * 100).toString().padStart(2, '0');
      
      updatedItems[index].batch_number = `LOT-${dlcDate}-${productCode}${randomSuffix}`;
    }
    
    if (field === 'selected_product_id' && value) {
        const product = produitsList.find(p => p.id === value);
        if (product) {
            updatedItems[index].final_name = product.nom;
            updatedItems[index].final_unit = product.unite || 'pièce';
        }
    }
    setItems(updatedItems);
    setAcknowledged(false);
    setWizardError('');
  };

  const handleDeleteItem = (index) => {
    setItems(items.filter((_, i) => i !== index));
  };

  const handleAddItem = () => {
    setItems([...items, {
        ocr_name: 'Nouveau produit',
        selected_product_id: '',
        final_name: '',
        final_qty: 1,
        final_unit: 'pièce',
        final_price: 0,
        batch_number: '',
        dlc: '',
        status: 'manual'
    }]);
  };

  const lineWarnings = (currentItems = items) => currentItems.filter(item =>
    Number(item.ocr_total) > 0 && Number(item.ocr_qty) > 0 &&
    Math.abs(Number(item.ocr_total) - Number(item.ocr_qty) * Number(item.final_price)) > 0.05
  );
  const uncertainItems = items.filter(item => !item.selected_product_id || (item.confidence > 0 && item.confidence < 0.8));
  const auditWarnings = Array.isArray(analysis?.audit_warnings) ? analysis.audit_warnings : [];
  const hasWarnings = Boolean(uncertainItems.length || lineWarnings().length || auditWarnings.length);
  const invoiceTotal = items.reduce((sum, item) => sum + Number(item.final_qty || 0) * Number(item.final_price || 0), 0);

  const nextStep = () => {
    setWizardError('');
    if (wizardStep === 0) {
      if (!selectedSupplierId || (selectedSupplierId === 'new' && !newSupplierName.trim())) {
        setWizardError('Choisissez un fournisseur ou indiquez son nom pour continuer.');
        return;
      }
      setWizardStep(1);
      setWizardNotice('Vérifiez les produits : quantité, unité, prix, rapprochement et DLC. Rien n’est encore ajouté au stock.');
      return;
    }
    if (wizardStep === 1) {
      if (!items.length) {
        setWizardError('Ajoutez au moins un produit à la facture pour continuer.');
        return;
      }
      const invalidIndex = items.findIndex(item =>
        !Number.isFinite(Number(item.final_qty)) || Number(item.final_qty) <= 0 ||
        !Number.isFinite(Number(item.final_price)) || Number(item.final_price) < 0 ||
        (!item.selected_product_id && !String(item.final_name || '').trim())
      );
      if (invalidIndex !== -1) {
        setWizardError(`Ligne ${invalidIndex + 1} : renseignez un produit, une quantité positive et un prix valide.`);
        return;
      }
      setAcknowledged(false);
      setWizardStep(2);
      setWizardNotice('Dernière vérification : contrôlez le récapitulatif puis confirmez l’import. Aucun stock n’a encore changé.');
    }
  };

  const handleValidate = async () => {
    setWizardError('');
    if (wizardStep !== 2) return;
    if (hasWarnings && !acknowledged) {
      setWizardError('Cochez la confirmation des points à contrôler avant d’intégrer la facture.');
      return;
    }
    setWizardNotice('Import en cours : création des lots et mouvements de stock. Ne fermez pas cette fenêtre.');
    setLoading(true);
    try {
      let finalSupplierId = selectedSupplierId;
      let finalSupplierName = newSupplierName;
      let createSupplier = false;

      if (selectedSupplierId === 'new') {
          createSupplier = true;
          finalSupplierId = null;
      } else {
          const supplier = fournisseursList.find(s => s.id === selectedSupplierId);
          if (supplier) finalSupplierName = supplier.nom;
      }

      const payload = {
        document_id: documentId,
        supplier_id: finalSupplierId,
        supplier_name: finalSupplierName,
        create_supplier: createSupplier,
        supplier_category: newSupplierCategory,
        invoice_number: editableNumero.trim(),
        invoice_date: editableDate,
        acknowledge_audit_warnings: auditWarnings.length > 0 && acknowledged,
        items: items.map(item => ({
            ...item,
            ocr_price: item.final_price,
            dlc: item.dlc || null,
            batch_number: item.batch_number || null
        }))
      };
      
      const response = previewData
        ? {data: {stats: {stock_entries:items.length,batches_created:items.length}}}
        : await axios.post(`${API}/ocr/confirm-import`, payload);
      setSuccessStats(response.data.stats || {stock_entries: items.length});
      setWizardStep(3);
      setWizardNotice(previewData ? 'Simulation réussie. Aucun stock ni document réel n’a été modifié.' : 'Import terminé : la facture a été intégrée au stock.');
      setLoading(false);
      if (onSuccess) onSuccess();
    } catch (err) {
      setWizardError("Import non confirmé : " + (err.response?.data?.detail || err.message) + ". Vérifiez l’état du document avant toute nouvelle tentative.");
      setWizardNotice('L’import ne peut pas être considéré comme réussi.');
      setLoading(false);
    }
  };

  if (loading && !analysis) return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-label="Analyse de la facture en cours" style={{zIndex: 99999}}>
      <div className="modal-content rt-wizard-loading" role="status">
        <div className="rt-wizard-spinner" aria-hidden="true" />
        <strong>Lecture de la facture en cours</strong>
        <p>Restop identifie les fournisseurs et les lignes. Vous pourrez tout vérifier avant l’entrée en stock.</p>
      </div>
    </div>
  );

  if (error) return (
    <div className="modal-overlay">
      <div className="modal-content" style={{padding: '20px', textAlign: 'center'}}>
        <h3 style={{color: 'red'}}>Erreur</h3>
        <p>{error}</p>
        <button className="button secondary" onClick={onClose}>Fermer</button>
      </div>
    </div>
  );

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="rt-wizard-title" style={{
      padding: isMobile ? '0' : '20px'
    }}>
      <div className="modal-content large" style={{
        maxWidth: isMobile ? '100%' : '1400px',
        width: '100%',
        height: isMobile ? '100vh' : '95vh',
        display: 'flex',
        flexDirection: 'column',
        padding: '0',
        margin: '0',
        borderRadius: isMobile ? '0' : '12px',
        maxHeight: isMobile ? '100vh' : '95vh'
      }}>
        
        {previewData && <div className="rt-wizard-demo-banner" role="status">Mode démonstration · Données fictives · Aucune écriture ni coût IA</div>}
        <header className="rt-wizard-header">
          <div className="rt-wizard-title"><div><p className="rt-wizard-eyebrow">Restop · Assistant de facture</p><h2 id="rt-wizard-title">Valider une facture fournisseur</h2></div>
            <button type="button" aria-label="Fermer le guide de validation" onClick={onClose} disabled={loading}>×</button></div>
          <ol className="rt-wizard-steps" aria-label="Étapes de validation">
            {['Fournisseur', 'Produits', 'Récapitulatif'].map((label, index) =>
              <li key={label} aria-current={wizardStep === index ? 'step' : undefined} className={wizardStep === index ? 'is-current' : wizardStep > index ? 'is-complete' : ''}>
                <span>{wizardStep > index ? '✓' : index + 1}</span>{label}
              </li>)}
          </ol>
          <p className="rt-wizard-explanation">{[
            'Étape 1/3 — Confirmez le fournisseur, la date et le numéro de facture. Cela aide à repérer les doublons.',
            'Étape 2/3 — Corrigez les quantités, prix, unités et correspondances produits. Une ligne incorrecte peut fausser le stock.',
            'Étape 3/3 — Vérifiez les écarts et le résumé avant toute écriture. Vous gardez la décision finale.',
            'Terminé — La facture a été enregistrée. Consultez le détail du stock pour vérifier les entrées.'
          ][wizardStep]}</p>
        </header>
        {wizardNotice && <div className="rt-wizard-notice" role="status">{wizardNotice}</div>}
        {wizardError && <div className="rt-wizard-error" role="alert">{wizardError}</div>}

        {wizardStep === 0 && <div className="rt-wizard-step-panel">
        {/* Identification et références du document */}
        <div className="rt-wizard-supplier-fields" style={{padding: isMobile ? '12px' : '20px', borderBottom: '1px solid #eee', background: '#fff'}}>
          
          <div style={{
            display: 'flex', 
            flexDirection: isMobile ? 'column' : 'row',
            gap: '10px', 
            background: '#f8f9fa', 
            padding: isMobile ? '10px' : '15px', 
            borderRadius: '8px'
          }}>
            <div style={{fontWeight: 'bold', fontSize: isMobile ? '13px' : '14px'}}>Fournisseur :</div>
            <select 
                value={selectedSupplierId} 
                onChange={(e) => setSelectedSupplierId(e.target.value)}
                style={{
                  padding: '8px', 
                  borderRadius: '4px', 
                  border: '1px solid #ccc', 
                  width: isMobile ? '100%' : '200px',
                  fontSize: isMobile ? '13px' : '14px'
                }}
            >
                <option value="new">Créer : {analysis.supplier_name}</option>
                {fournisseursList.map(f => <option key={f.id} value={f.id}>{f.nom}</option>)}
            </select>
            
            {selectedSupplierId === 'new' && (
                <>
                  <input 
                      type="text" 
                      value={newSupplierName}
                      onChange={(e) => setNewSupplierName(e.target.value)}
                      placeholder="Nom du fournisseur"
                      style={{
                        padding: '8px', 
                        border: '1px solid #f59e0b', 
                        borderRadius: '4px',
                        width: isMobile ? '100%' : 'auto',
                        fontSize: isMobile ? '13px' : '14px'
                      }}
                  />
                  <div style={{
                    fontSize: '11px',
                    color: '#681b32',
                    fontStyle: 'normal',
                    width: isMobile ? '100%' : 'auto'
                  }}>
                    Nouveau fournisseur : Le système mémorisera vos corrections pour les prochaines factures
                  </div>
                </>
            )}
          </div>
          
          {/* Ligne séparée pour Date et Numéro (éditables) */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: isMobile ? '1fr 1fr' : '200px 200px',
            gap: '10px',
            marginTop: '10px'
          }}>
            <div>
              <label style={{display: 'block', fontSize: '11px', color: '#64748b', marginBottom: '4px'}}>
                Date de la facture
              </label>
              <input 
                type="date"
                value={editableDate}
                onChange={(e) => setEditableDate(e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #cbd5e1',
                  borderRadius: '4px',
                  fontSize: isMobile ? '13px' : '14px'
                }}
              />
            </div>
            
            <div>
              <label style={{display: 'block', fontSize: '11px', color: '#64748b', marginBottom: '4px'}}>
                Numéro de facture
              </label>
              <input 
                type="text"
                value={editableNumero}
                onChange={(e) => setEditableNumero(e.target.value)}
                placeholder="Numéro facture"
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #cbd5e1',
                  borderRadius: '4px',
                  fontSize: isMobile ? '13px' : '14px'
                }}
              />
            </div>
          </div>
        </div>

        </div>}

        {wizardStep === 1 && <div className="rt-wizard-step-panel rt-wizard-products">
        {Array.isArray(analysis?.audit_warnings) && analysis.audit_warnings.length > 0 && (
          <div className="rt-invoice-audit" role="alert">
            <strong>Montants à contrôler avant import · {analysis.audit_warnings.length} anomalie(s)</strong>
            <ul>{analysis.audit_warnings.slice(0, 6).map((warning, idx) =>
              <li key={`${warning.code}-${idx}`}>{warning.message}</li>
            )}</ul>
            {analysis.audit_warnings.length > 6 && <p>Et {analysis.audit_warnings.length - 6} autre(s) point(s) à vérifier.</p>}
            <small>Ces contrôles sont indicatifs : les remises, consignes et poids variables peuvent expliquer des écarts. Votre confirmation reste obligatoire.</small>
          </div>
        )}

        {/* SUGGESTION JOKER IA */}
        {showAiSuggestion && !previewData && (
          <div style={{
            padding: isMobile ? '10px' : '15px',
            background: 'linear-gradient(135deg, #fef3c7, #fde68a)',
            borderBottom: '1px solid #fbbf24',
            display: 'flex',
            flexDirection: isMobile ? 'column' : 'row',
            alignItems: 'center',
            gap: '10px'
          }}>
            <div style={{flex: 1, fontSize: isMobile ? '12px' : '14px'}}>
              <strong>Amélioration IA disponible</strong> • Beaucoup de produits non reconnus. Une seconde lecture IA peut aider sur les factures complexes, sans garantie de précision.
            </div>
            <button
              onClick={handleReanalyzeWithAI}
              style={{
                background: '#681b32',
                color: 'white',
                border: 'none',
                padding: isMobile ? '8px 16px' : '10px 20px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontWeight: 'bold',
                fontSize: isMobile ? '12px' : '14px',
                whiteSpace: 'nowrap'
              }}
            >
              Relire avec l’IA (coût variable)
            </button>
            <button
              onClick={() => setShowAiSuggestion(false)}
              style={{
                background: 'transparent',
                border: 'none',
                fontSize: '20px',
                cursor: 'pointer',
                padding: '5px'
              }}
            >
              ✕
            </button>
          </div>
        )}

        {/* BADGE IA POWERED */}
        {aiPowered && (
          <div style={{
            padding: '8px',
            background: 'linear-gradient(135deg, #681b32, #92263d)',
            color: 'white',
            textAlign: 'center',
            fontSize: isMobile ? '11px' : '13px',
            fontWeight: 'bold'
          }}>
            Nouvelle lecture IA effectuée · Contrôlez les valeurs proposées
          </div>
        )}

        {/* CONTENU SCROLLABLE */}
        <div style={{flex: 1, overflowY: 'auto', padding: isMobile ? '10px' : '20px', overflowX: isMobile ? 'visible' : 'auto'}}>
          {isMobile ? (
            // VERSION MOBILE : CARTES
            <div style={{display: 'flex', flexDirection: 'column', gap: '12px'}}>
              {items.map((item, index) => (
                <MobileItemCard 
                  key={index} 
                  item={item} 
                  index={index}
                  handleItemChange={handleItemChange}
                  handleDeleteItem={handleDeleteItem}
                  produitsList={produitsList}
                />
              ))}
            </div>
          ) : (
            // VERSION DESKTOP : TABLEAU
            <table style={{width: '100%', minWidth: '800px', borderCollapse: 'collapse', fontSize: '13px'}}>
              <thead style={{background: '#f1f5f9', position: 'sticky', top: 0, zIndex: 10}}>
                <tr>
                  <th style={{padding: '12px', textAlign: 'left', borderBottom: '2px solid #cbd5e1', width: '20%'}}>Produit (OCR) / Nom Final</th>
                  <th style={{padding: '12px', textAlign: 'left', borderBottom: '2px solid #cbd5e1', width: '20%'}}>Correspondance Stock</th>
                  <th style={{padding: '12px', textAlign: 'center', borderBottom: '2px solid #cbd5e1', width: '80px'}}>Qté</th>
                  <th style={{padding: '12px', textAlign: 'center', borderBottom: '2px solid #cbd5e1', width: '100px'}}>Unité</th>
                  <th style={{padding: '12px', textAlign: 'center', borderBottom: '2px solid #cbd5e1', width: '100px'}}>Prix U. (€)</th>
                  <th style={{padding: '12px', textAlign: 'center', borderBottom: '2px solid #cbd5e1', width: '100px'}}>Total (€)</th>
                  <th style={{padding: '12px', textAlign: 'left', borderBottom: '2px solid #cbd5e1'}}>DLC & Lot</th>
                  <th style={{padding: '12px', textAlign: 'center', borderBottom: '2px solid #cbd5e1', width: '50px'}}>Action</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item, index) => (
                  <tr key={index} style={{borderBottom: '1px solid #e2e8f0', background: item.selected_product_id ? '#fff' : '#fff7ed'}}>
                    <td style={{padding: '10px'}}>
                      <input 
                          type="text" 
                          value={item.final_name}
                          onChange={(e) => handleItemChange(index, 'final_name', e.target.value)}
                          style={{width: '100%', padding: '6px', border: '1px solid #cbd5e1', borderRadius: '4px', fontWeight: 'bold'}}
                          placeholder="Nom du produit"
                      />
                      <div style={{fontSize: '11px', color: '#94a3b8', marginTop: '4px'}}>
                          Lu: {item.ocr_name}
                      </div>
                    </td>
                    <td style={{padding: '10px'}}>
                      <select 
                        style={{width: '100%', padding: '6px', borderRadius: '4px', border: '1px solid #cbd5e1'}}
                        value={item.selected_product_id}
                        onChange={(e) => handleItemChange(index, 'selected_product_id', e.target.value)}
                      >
                        <option value="">Créer nouveau</option>
                        {produitsList.map(p => (
                          <option key={p.id} value={p.id}>{p.nom}</option>
                        ))}
                      </select>
                    </td>
                    <td style={{padding: '10px'}}>
                      <input 
                        type="number" 
                        step="0.1"
                        style={{width: '100%', padding: '6px', textAlign: 'center', border: '1px solid #cbd5e1', borderRadius: '4px'}}
                        value={item.final_qty}
                        onChange={(e) => handleItemChange(index, 'final_qty', parseFloat(e.target.value))}
                      />
                    </td>
                    <td style={{padding: '10px'}}>
                      <select
                          style={{width: '100%', padding: '6px', border: '1px solid #cbd5e1', borderRadius: '4px'}}
                          value={item.final_unit}
                          onChange={(e) => handleItemChange(index, 'final_unit', e.target.value)}
                      >
                          <option value="pièce">Pièce</option>
                          <option value="kg">Kg</option>
                          <option value="g">Gramme</option>
                          <option value="L">Litre</option>
                          <option value="colis">Colis</option>
                          <option value="botte">Botte</option>
                      </select>
                    </td>
                    <td style={{padding: '10px'}}>
                      <input 
                        type="number" 
                        step="0.01"
                        style={{width: '100%', padding: '6px', textAlign: 'right', border: '1px solid #cbd5e1', borderRadius: '4px'}}
                        value={item.final_price}
                        onChange={(e) => handleItemChange(index, 'final_price', parseFloat(e.target.value))}
                      />
                    </td>
                    <td style={{padding: '10px', textAlign: 'right', fontWeight: 'bold', color: '#64748b'}}>
                      {(item.final_qty * item.final_price).toFixed(2)} €
                    </td>
                    <td style={{padding: '10px'}}>
                      <div style={{display: 'flex', gap: '5px', marginBottom: '5px'}}>
                          <span style={{fontSize: '12px', width: '30px'}}>DLC:</span>
                          <input 
                              type="date" 
                              style={{flex: 1, padding: '4px', border: '1px solid #cbd5e1', borderRadius: '4px'}}
                              value={item.dlc}
                              onChange={(e) => handleItemChange(index, 'dlc', e.target.value)}
                          />
                      </div>
                      <div style={{display: 'flex', gap: '5px'}}>
                          <span style={{fontSize: '12px', width: '30px'}}>Lot:</span>
                          <input 
                              type="text" 
                              placeholder="N° Lot"
                              style={{flex: 1, padding: '4px', border: '1px solid #cbd5e1', borderRadius: '4px'}}
                              value={item.batch_number}
                              onChange={(e) => handleItemChange(index, 'batch_number', e.target.value)}
                          />
                      </div>
                    </td>
                    <td style={{padding: '10px', textAlign: 'center'}}>
                      <button 
                          onClick={() => handleDeleteItem(index)}
                          style={{
                              background: '#fee2e2', 
                              color: '#dc2626', 
                              border: 'none', 
                              borderRadius: '4px', 
                              width: '32px', 
                              height: '32px', 
                              cursor: 'pointer',
                              display: 'flex', 
                              alignItems: 'center', 
                              justifyContent: 'center'
                          }}
                          title="Supprimer cette ligne"
                      >
                          🗑️
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          
          {/* Boutons d'action */}
          <div style={{display: 'flex', gap: '10px', marginTop: '15px', flexDirection: isMobile ? 'column' : 'row'}}>
            <button 
              onClick={handleAddItem}
              style={{
                  flex: 1,
                  padding: '10px 20px',
                  background: '#fff5f7',
                  color: '#681b32',
                  border: '1px dashed #92263d',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontWeight: 'bold',
                  fontSize: isMobile ? '13px' : '14px'
              }}
            >
              Ajouter une ligne
            </button>
            
            {!aiPowered && !previewData && (
              <button 
                onClick={handleReanalyzeWithAI}
                style={{
                    flex: 1,
                    padding: '10px 20px',
                    background: 'linear-gradient(135deg, #681b32, #92263d)',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontWeight: 'bold',
                    fontSize: isMobile ? '13px' : '14px',
                    boxShadow: '0 2px 8px rgba(104, 27, 50, 0.15)'
                }}
              >
                Améliorer avec Gemini IA
              </button>
            )}
          </div>
        </div>

        </div>}

        {wizardStep === 2 && <section className="rt-wizard-review" aria-labelledby="rt-review-title">
          <h3 id="rt-review-title">Tout est prêt pour la dernière vérification</h3>
          <p>{previewData ? 'Simulation : vous pouvez terminer le parcours sans créer aucun mouvement réel.' : 'Les données ci-dessous correspondent à vos corrections. Aucune modification du stock n’est réalisée avant validation.'}</p>
          <dl className="rt-wizard-review-facts">
            <div><dt>Fournisseur</dt><dd>{selectedSupplierId === 'new' ? newSupplierName : (fournisseursList.find(s => s.id === selectedSupplierId)?.nom || newSupplierName)}</dd></div>
            <div><dt>Facture n°</dt><dd>{editableNumero || 'Non renseigné'}</dd></div>
            <div><dt>Date</dt><dd>{editableDate || 'Non renseignée'}</dd></div>
            <div><dt>Produits</dt><dd>{items.length} ligne(s)</dd></div>
          </dl>
          <div className="rt-wizard-review-scroll"><table><thead><tr><th>Produit</th><th>Quantité</th><th>Prix unitaire</th><th>Montant indicatif</th></tr></thead><tbody>
            {items.map((item, index) => <tr key={index}><td>{item.final_name || item.ocr_name}</td><td>{item.final_qty} {item.final_unit || ''}</td><td>{Number(item.final_price).toFixed(2)} €</td><td>{(Number(item.final_qty) * Number(item.final_price)).toFixed(2)} €</td></tr>)}
          </tbody></table></div>
          <p className="rt-wizard-total">Sous-total indicatif des lignes : <strong>{invoiceTotal.toFixed(2)} €</strong></p>
          <small>Le sous-total des lignes n’est pas forcément le TTC : TVA, remises, transport et consignes peuvent s’ajouter.</small>
          {hasWarnings ? <div className="rt-wizard-review-warning">
            <strong>Points à contrôler avant validation</strong>
            <p>{uncertainItems.length} produit(s) sans correspondance certaine, {lineWarnings().length} écart(s) de ligne, {auditWarnings.length} anomalie(s) OCR.</p>
            <ul>{auditWarnings.map((warning, idx) => <li key={`${warning.code}-${idx}`}>{warning.message}</li>)}</ul>
            <label><input type="checkbox" checked={acknowledged} onChange={event => setAcknowledged(event.target.checked)} /> J’ai vérifié les anomalies et je confirme les quantités, les prix et les unités corrigés.</label>
          </div> : <div className="rt-wizard-review-ok">Aucune anomalie automatique détectée. Vérifiez malgré tout les données avant import.</div>}
        </section>}

        {wizardStep === 3 && <section className="rt-wizard-success" role="status">
          <div aria-hidden="true" className="rt-wizard-success-icon">✓</div>
          <h3>{previewData ? 'Simulation terminée' : 'Facture intégrée au stock'}</h3>
          <p>{previewData ? 'Parcours de démonstration terminé : aucune donnée n’a été enregistrée ni transmise.' : 'L’import est terminé. Les quantités et mouvements associés ont été enregistrés.'}</p>
          <strong>{successStats?.stock_entries ?? 0} entrée(s) de stock · {successStats?.batches_created ?? 0} lot(s)</strong>
          <p>Vous pouvez fermer cette fenêtre et consulter les mouvements dans l’onglet Stocks.</p>
        </section>}

        <footer className="rt-wizard-footer">
          <p>{wizardStep === 3 ? 'Import finalisé' : `Étape ${wizardStep + 1} sur 3`} · {wizardStep === 0 ? 'Identification' : wizardStep === 1 ? `${items.length} produit(s) à contrôler` : wizardStep === 2 ? `${invoiceTotal.toFixed(2)} € de lignes (hors ajustements)` : 'Terminé'}</p>
          <div className="rt-wizard-footer-buttons">
            {wizardStep === 3 ? <button type="button" className="rt-wizard-primary" onClick={onClose}>Fermer et voir les stocks</button> : <>
              <button type="button" className="rt-wizard-secondary" disabled={loading} onClick={wizardStep === 0 ? onClose : () => {setWizardError('');setWizardStep(step => step - 1);}}>{wizardStep === 0 ? 'Annuler' : 'Retour'}</button>
              {wizardStep < 2 ? <button type="button" className="rt-wizard-primary" disabled={loading} onClick={nextStep}>Continuer →</button>
                : <button type="button" className="rt-wizard-primary" onClick={handleValidate} disabled={loading}>
                    {loading ? 'Intégration en cours…' : previewData ? 'Terminer la simulation' : 'Confirmer l’entrée en stock'}
                  </button>}
            </>}
          </div>
        </footer>
      </div>
    </div>
  );
};

export default InvoiceValidationModal;
