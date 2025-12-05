import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const InvoiceValidationModal = ({ documentId, onClose, onSuccess, produitsList, fournisseursList }) => {
  const [loading, setLoading] = useState(true);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState(null);
  const [items, setItems] = useState([]);
  
  // Gestion du fournisseur
  const [selectedSupplierId, setSelectedSupplierId] = useState('');
  const [newSupplierName, setNewSupplierName] = useState('');
  const [newSupplierCategory, setNewSupplierCategory] = useState('frais');

  // Charger l'analyse au montage
  useEffect(() => {
    const fetchAnalysis = async () => {
      try {
        const response = await axios.post(`${API}/ocr/analyze-facture/${documentId}`);
        const data = response.data;
        setAnalysis(data);
        
        // Logique Fournisseur Intelligent
        if (data.supplier_id) {
            // Fournisseur reconnu
            setSelectedSupplierId(data.supplier_id);
            setNewSupplierName(data.supplier_name);
        } else {
            // Nouveau fournisseur
            setSelectedSupplierId('new'); // Mode création par défaut
            setNewSupplierName(data.supplier_name || 'Nouveau Fournisseur');
        }

        // Logique Produits Intelligente
        const initializedItems = data.items.map(item => ({
          ...item,
          // Si matché -> ID, Sinon -> Vide (Mode Création)
          selected_product_id: item.status === 'matched' ? item.product_id : '', 
          // Si Création -> Nom OCR par défaut, sinon Nom Base
          final_name: item.status === 'matched' ? item.product_name : item.ocr_name,
          final_qty: item.ocr_qty,
          final_unit: item.ocr_unit,
          batch_number: '',
          dlc: ''
        }));
        setItems(initializedItems);
        setLoading(false);
      } catch (err) {
        console.error("Erreur analyse:", err);
        setError("Impossible d'analyser la facture. Vérifiez que c'est bien une facture fournisseur.");
        setLoading(false);
      }
    };
    
    if (documentId) {
      fetchAnalysis();
    }
  }, [documentId]);

  const handleItemChange = (index, field, value) => {
    const newItems = [...items];
    newItems[index] = { ...newItems[index], [field]: value };
    
    // Si on sélectionne un produit existant, on met à jour son nom final
    if (field === 'selected_product_id') {
        const prod = produitsList.find(p => p.id === value);
        if (prod) {
            newItems[index].final_name = prod.nom;
            newItems[index].final_unit = prod.unite;
        } else if (value === "") {
            // Retour au mode création : on remet le nom OCR original
            newItems[index].final_name = newItems[index].ocr_name;
        }
    }
    
    setItems(newItems);
  };

  const handleValidate = async () => {
    if (!window.confirm("Confirmez-vous l'import de ces produits en stock ?")) return;
    
    setLoading(true);
    try {
      // Préparer le fournisseur
      let finalSupplierId = selectedSupplierId;
      let finalSupplierName = newSupplierName;
      let createSupplier = false;

      if (selectedSupplierId === 'new') {
          createSupplier = true;
          finalSupplierId = null; // Sera créé par le backend
      } else {
          // Récupérer le vrai nom si existant
          const supplier = fournisseursList.find(s => s.id === selectedSupplierId);
          if (supplier) finalSupplierName = supplier.nom;
      }

      const payload = {
        document_id: documentId,
        supplier_id: finalSupplierId,
        supplier_name: finalSupplierName,
        create_supplier: createSupplier,
        supplier_category: newSupplierCategory, // Nouveau champ à gérer côté backend si besoin
        items: items.map(item => ({
            ...item,
            dlc: item.dlc || null,
            batch_number: item.batch_number || null
        }))
      };
      
      const response = await axios.post(`${API}/ocr/confirm-import`, payload);
      alert(`✅ Import réussi !\n${response.data.stats.stock_entries} entrées de stock créées.\n${response.data.stats.batches_created} lots créés.`);
      onSuccess();
      onClose();
    } catch (err) {
      console.error("Erreur validation:", err);
      alert("Erreur lors de la validation: " + (err.response?.data?.detail || err.message));
      setLoading(false);
    }
  };

  if (loading) return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div style={{textAlign: 'center', padding: '40px'}}>
          <div style={{fontSize: '40px', marginBottom: '20px'}}>🤖</div>
          <h3>Lecture intelligente en cours...</h3>
          <p>Détection des produits et fournisseurs...</p>
        </div>
      </div>
    </div>
  );

  if (error) return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div style={{textAlign: 'center', padding: '20px'}}>
          <div style={{color: 'red', fontSize: '40px', marginBottom: '10px'}}>⚠️</div>
          <h3>Erreur</h3>
          <p>{error}</p>
          <button className="button secondary" onClick={onClose} style={{marginTop: '20px'}}>Fermer</button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="modal-overlay">
      <div className="modal-content large" style={{maxWidth: '950px', width: '95%', maxHeight: '90vh', display: 'flex', flexDirection: 'column'}}>
        
        {/* HEADER : GESTION DU FOURNISSEUR */}
        <div className="modal-header" style={{borderBottom: '1px solid #eee', paddingBottom: '15px', marginBottom: '15px', flexShrink: 0}}>
          <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start'}}>
            <div style={{flex: 1}}>
                <h3 style={{marginBottom: '10px'}}>📝 Validation Facture</h3>
                
                {/* Zone Fournisseur Intelligente */}
                <div style={{background: '#f0f9ff', padding: '12px', borderRadius: '8px', border: '1px solid #bae6fd'}}>
                    <div style={{display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap'}}>
                        <div style={{fontWeight: 'bold', minWidth: '100px'}}>🏢 Fournisseur :</div>
                        
                        {/* Sélecteur de Fournisseur */}
                        <select 
                            value={selectedSupplierId} 
                            onChange={(e) => setSelectedSupplierId(e.target.value)}
                            style={{padding: '8px', borderRadius: '4px', border: '1px solid #ccc', minWidth: '200px', fontWeight: '500'}}
                        >
                            <option value="new">➕ Créer nouveau : {analysis.supplier_name}</option>
                            <optgroup label="Fournisseurs existants">
                                {fournisseursList.map(f => (
                                    <option key={f.id} value={f.id}>{f.nom}</option>
                                ))}
                            </optgroup>
                        </select>

                        {/* Si Nouveau : Champs d'édition */}
                        {selectedSupplierId === 'new' && (
                            <>
                                <input 
                                    type="text" 
                                    value={newSupplierName}
                                    onChange={(e) => setNewSupplierName(e.target.value)}
                                    placeholder="Nom du fournisseur"
                                    style={{padding: '8px', borderRadius: '4px', border: '1px solid #f59e0b', flex: 1}}
                                />
                                <select
                                    value={newSupplierCategory}
                                    onChange={(e) => setNewSupplierCategory(e.target.value)}
                                    style={{padding: '8px', borderRadius: '4px', border: '1px solid #ddd'}}
                                >
                                    <option value="frais">Frais</option>
                                    <option value="surgelés">Surgelés</option>
                                    <option value="épicerie">Épicerie</option>
                                    <option value="boissons">Boissons</option>
                                    <option value="autre">Autres</option>
                                </select>
                            </>
                        )}
                    </div>
                    <div style={{fontSize: '13px', color: '#64748b', marginTop: '8px', marginLeft: '110px'}}>
                        Date: {analysis.facture_date} • N°: {analysis.numero_facture}
                    </div>
                </div>
            </div>
            <button className="modal-close" onClick={onClose} style={{background: 'none', border: 'none', fontSize: '28px', cursor: 'pointer', marginLeft: '15px'}}>×</button>
          </div>
        </div>

        {/* BODY : LISTE DES PRODUITS */}
        <div className="modal-body" style={{overflowY: 'auto', flex: 1}}>
          <table style={{width: '100%', borderCollapse: 'collapse', fontSize: '13px'}}>
            <thead style={{background: '#f8f9fa', position: 'sticky', top: 0, zIndex: 10}}>
              <tr>
                <th style={{padding: '12px', textAlign: 'left', borderBottom: '2px solid #e2e8f0'}}>Produit Lu (OCR)</th>
                <th style={{padding: '12px', textAlign: 'left', borderBottom: '2px solid #e2e8f0', width: '30%'}}>Correspondance Stock</th>
                <th style={{padding: '12px', textAlign: 'center', width: '70px', borderBottom: '2px solid #e2e8f0'}}>Qté</th>
                <th style={{padding: '12px', textAlign: 'left', width: '130px', borderBottom: '2px solid #e2e8f0'}}>DLC 📅</th>
                <th style={{padding: '12px', textAlign: 'left', width: '110px', borderBottom: '2px solid #e2e8f0'}}>Lot 📦</th>
                <th style={{padding: '12px', textAlign: 'right', borderBottom: '2px solid #e2e8f0'}}>Prix</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item, index) => (
                <tr key={index} style={{borderBottom: '1px solid #f1f5f9', background: item.selected_product_id ? 'white' : '#fffbeb'}}>
                  <td style={{padding: '12px'}}>
                    <div style={{fontWeight: 'bold', color: '#1e293b'}}>{item.ocr_name}</div>
                    <div style={{fontSize: '11px', color: '#64748b'}}>{item.ocr_unit}</div>
                  </td>
                  <td style={{padding: '12px'}}>
                    <select 
                      style={{
                        width: '100%', 
                        padding: '8px', 
                        borderRadius: '6px',
                        border: item.selected_product_id ? '1px solid #cbd5e1' : '2px solid #f59e0b',
                        backgroundColor: item.selected_product_id ? 'white' : '#fffbeb',
                        fontWeight: item.selected_product_id ? 'normal' : 'bold',
                        color: item.selected_product_id ? 'black' : '#d97706'
                      }}
                      value={item.selected_product_id}
                      onChange={(e) => handleItemChange(index, 'selected_product_id', e.target.value)}
                    >
                      <option value="">➕ Créer : {item.ocr_name}</option>
                      <optgroup label="Produits existants">
                        {produitsList.map(p => (
                            <option key={p.id} value={p.id}>
                            {p.nom} ({p.unite})
                            </option>
                        ))}
                      </optgroup>
                    </select>
                    
                    {/* Champ d'édition du nom si création */}
                    {!item.selected_product_id && (
                        <div style={{marginTop: '6px', display: 'flex', alignItems: 'center'}}>
                            <span style={{marginRight: '5px'}}>✏️</span>
                            <input 
                                type="text"
                                value={item.final_name}
                                onChange={(e) => handleItemChange(index, 'final_name', e.target.value)}
                                placeholder="Nom du produit final"
                                style={{width: '100%', padding: '6px', fontSize: '12px', border: '1px solid #f59e0b', borderRadius: '4px'}}
                            />
                        </div>
                    )}
                  </td>
                  <td style={{padding: '12px'}}>
                    <input 
                      type="number" 
                      style={{width: '60px', padding: '6px', textAlign: 'center', borderRadius: '4px', border: '1px solid #cbd5e1'}}
                      value={item.final_qty}
                      onChange={(e) => handleItemChange(index, 'final_qty', parseFloat(e.target.value))}
                    />
                  </td>
                  <td style={{padding: '12px'}}>
                    <input 
                      type="date" 
                      style={{width: '100%', padding: '6px', border: item.dlc ? '1px solid #10b981' : '1px solid #cbd5e1', borderRadius: '4px'}}
                      value={item.dlc}
                      onChange={(e) => handleItemChange(index, 'dlc', e.target.value)}
                    />
                  </td>
                  <td style={{padding: '12px'}}>
                    <input 
                      type="text" 
                      placeholder="Auto"
                      style={{width: '100%', padding: '6px', borderRadius: '4px', border: '1px solid #cbd5e1'}}
                      value={item.batch_number}
                      onChange={(e) => handleItemChange(index, 'batch_number', e.target.value)}
                    />
                  </td>
                  <td style={{padding: '12px', textAlign: 'right', fontWeight: '500'}}>
                    {item.ocr_price}€
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="modal-footer" style={{borderTop: '1px solid #eee', paddingTop: '15px', marginTop: '15px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0}}>
          <div style={{fontSize: '13px', color: '#64748b'}}>
            {items.length} produits à importer
          </div>
          <div style={{display: 'flex', gap: '10px'}}>
            <button className="button secondary" onClick={onClose}>Annuler</button>
            <button className="button success" onClick={handleValidate} style={{padding: '10px 20px', fontSize: '15px'}}>
                ✅ Valider et Intégrer au Stock
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InvoiceValidationModal;
