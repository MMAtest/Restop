import React, { useState, useEffect } from 'react';
import axios from 'axios';

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
        <option value="">➕ Créer nouveau</option>
        {produitsList.map(p => (
          <option key={p.id} value={p.id}>{p.nom}</option>
        ))}
      </select>
    </div>

    {/* Ligne des 3 champs : Qté, Unité, Prix */}
    <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px', marginBottom: '10px'}}>
      <div>
        <label style={{display: 'block', fontSize: '11px', color: '#64748b', marginBottom: '4px'}}>Qté</label>
        <input 
          type="number" 
          step="0.1"
          style={{
            width: '100%',
            padding: '8px',
            textAlign: 'center',
            border: '1px solid #cbd5e1',
            borderRadius: '6px',
            fontSize: '14px'
          }}
          value={item.final_qty}
          onChange={(e) => handleItemChange(index, 'final_qty', parseFloat(e.target.value))}
        />
      </div>

      <div>
        <label style={{display: 'block', fontSize: '11px', color: '#64748b', marginBottom: '4px'}}>Unité</label>
        <select
          style={{
            width: '100%',
            padding: '8px',
            border: '1px solid #cbd5e1',
            borderRadius: '6px',
            fontSize: '14px'
          }}
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
      </div>

      <div>
        <label style={{display: 'block', fontSize: '11px', color: '#64748b', marginBottom: '4px'}}>Prix U. (€)</label>
        <input 
          type="number" 
          step="0.01"
          style={{
            width: '100%',
            padding: '8px',
            textAlign: 'right',
            border: '1px solid #cbd5e1',
            borderRadius: '6px',
            fontSize: '14px'
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

const InvoiceValidationModal = ({ documentId, onClose, onSuccess, onRefresh, produitsList, fournisseursList }) => {
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

  // Charger l'analyse au montage
  useEffect(() => {
    const fetchAnalysis = async () => {
      // Afficher la barre de progression immédiatement
      setShowProgressBar(true);

      try {
        const response = await axios.post(`${API}/ocr/analyze-facture/${documentId}`);
        const data = response.data;
        setAnalysis(data);
        
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
        const initializedItems = data.items.map(item => {
          const productName = item.status === 'matched' ? item.product_name : item.ocr_name;
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
            final_qty: item.ocr_qty || 1,
            final_unit: item.ocr_unit || 'pièce',
            final_price: item.ocr_price || 0,
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
          console.log(`⚠️ Taux de correspondance: ${(matchRate * 100).toFixed(0)}%. Nouveau fournisseur: ${isNewSupplier}. Joker IA suggéré.`);
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
  }, [documentId]);

  const handleReanalyzeWithAI = async () => {
    setLoading(true);
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
      const initializedItems = data.items.map(item => {
        const productName = item.status === 'matched' ? item.product_name : item.ocr_name;
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
          final_qty: item.ocr_qty || 1,
          final_unit: item.ocr_unit || 'pièce',
          final_price: item.ocr_price || 0,
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
      alert(`🤖 Analyse IA terminée !\n\n✅ ${matchedCount}/${initializedItems.length} produits automatiquement reconnus\n💰 Coût estimé : ~0.003€`);
      
    } catch (err) {
      console.error("Erreur Joker IA:", err);
      setShowProgressBar(false);
      setLoading(false);
      alert("Erreur lors de l'analyse IA : " + (err.response?.data?.detail || err.message));
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

  const handleValidate = async () => {
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
        items: items.map(item => ({
            ...item,
            ocr_price: item.final_price,
            dlc: item.dlc || null,
            batch_number: item.batch_number || null
        }))
      };
      
      const response = await axios.post(`${API}/ocr/confirm-import`, payload);
      alert(`✅ Import réussi !\n${response.data.stats.stock_entries} entrées de stock créées.`);
      onSuccess();
      onClose();
    } catch (err) {
      alert("Erreur: " + (err.response?.data?.detail || err.message));
      setLoading(false);
    }
  };

  if (loading) return (
    <div className="modal-overlay">
      <div className="modal-content" style={{padding: '40px', textAlign: 'center', maxWidth: '400px'}}>
        <div style={{fontSize: '40px', marginBottom: '20px'}}>🤖</div>
        <h3 style={{marginBottom: '15px'}}>Analyse en cours...</h3>
        <div style={{
          width: '100%',
          height: '8px',
          background: '#e0e0e0',
          borderRadius: '4px',
          overflow: 'hidden',
          marginBottom: '10px'
        }}>
          <div style={{
            width: '100%',
            height: '100%',
            background: 'linear-gradient(90deg, #10b981, #059669)',
            animation: 'progress 1.5s ease-in-out infinite'
          }}></div>
        </div>
        <p style={{fontSize: '14px', color: '#666'}}>
          Analyse intelligente des produits...
        </p>
        <style>{`
          @keyframes progress {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
          }
        `}</style>
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
    <div className="modal-overlay" style={{
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
        
        {/* HEADER FIXE */}
        <div style={{padding: isMobile ? '12px' : '20px', borderBottom: '1px solid #eee', background: '#fff'}}>
          <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px'}}>
            <h3 style={{margin: 0, fontSize: isMobile ? '16px' : '20px'}}>📝 Validation Facture</h3>
            <button onClick={onClose} style={{background: 'none', border: 'none', fontSize: '24px', cursor: 'pointer'}}>×</button>
          </div>
          
          <div style={{
            display: 'flex', 
            flexDirection: isMobile ? 'column' : 'row',
            gap: '10px', 
            background: '#f8f9fa', 
            padding: isMobile ? '10px' : '15px', 
            borderRadius: '8px'
          }}>
            <div style={{fontWeight: 'bold', fontSize: isMobile ? '13px' : '14px'}}>🏢 Fournisseur :</div>
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
                <option value="new">➕ Créer : {analysis.supplier_name}</option>
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
                    color: '#059669',
                    fontStyle: 'italic',
                    width: isMobile ? '100%' : 'auto'
                  }}>
                    💡 Nouveau fournisseur : Le système mémorisera vos corrections pour les prochaines factures
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
                📅 Date de la facture
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
                📋 Numéro de facture
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

        {/* SUGGESTION JOKER IA */}
        {showAiSuggestion && (
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
              <strong>🤖 Amélioration IA disponible</strong> • Beaucoup de produits non reconnus. L&apos;analyse IA peut améliorer la précision jusqu&apos;à 90%.
            </div>
            <button
              onClick={handleReanalyzeWithAI}
              style={{
                background: '#10b981',
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
              🚀 Améliorer avec IA (~0.003€)
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
            background: 'linear-gradient(135deg, #10b981, #059669)',
            color: 'white',
            textAlign: 'center',
            fontSize: isMobile ? '11px' : '13px',
            fontWeight: 'bold'
          }}>
            ✨ Analysé avec Gemini 2.0 Flash • Précision améliorée
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
                        <option value="">➕ Créer nouveau</option>
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
                  background: '#e0f2fe',
                  color: '#0284c7',
                  border: '1px dashed #0284c7',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontWeight: 'bold',
                  fontSize: isMobile ? '13px' : '14px'
              }}
            >
              ➕ Ajouter une ligne
            </button>
            
            {!aiPowered && (
              <button 
                onClick={handleReanalyzeWithAI}
                style={{
                    flex: 1,
                    padding: '10px 20px',
                    background: 'linear-gradient(135deg, #10b981, #059669)',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontWeight: 'bold',
                    fontSize: isMobile ? '13px' : '14px',
                    boxShadow: '0 2px 8px rgba(16, 185, 129, 0.3)'
                }}
              >
                🤖 Améliorer avec Gemini IA
              </button>
            )}
          </div>
        </div>

        {/* FOOTER FIXE */}
        <div style={{
          padding: isMobile ? '12px' : '20px',
          borderTop: '1px solid #eee',
          background: '#fff',
          display: 'flex',
          flexDirection: isMobile ? 'column' : 'row',
          justifyContent: 'space-between',
          alignItems: isMobile ? 'stretch' : 'center',
          gap: '10px'
        }}>
          <div style={{fontSize: isMobile ? '14px' : '16px', textAlign: isMobile ? 'center' : 'left'}}>
            <strong>Total Facture : </strong>
            <span style={{color: '#059669', fontSize: isMobile ? '16px' : '18px'}}>
                {items.reduce((acc, item) => acc + (item.final_qty * item.final_price), 0).toFixed(2)} €
            </span>
          </div>
          <div style={{display: 'flex', gap: '10px', flexDirection: isMobile ? 'column' : 'row'}}>
            <button className="button secondary" onClick={onClose} style={{padding: '12px 24px'}}>Annuler</button>
            <button className="button success" onClick={handleValidate} style={{padding: '12px 24px', fontSize: '16px'}}>
                ✅ Valider et Intégrer au Stock
            </button>
          </div>
        </div>

      </div>
    </div>
  );
};

export default InvoiceValidationModal;
