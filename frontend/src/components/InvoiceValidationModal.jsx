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
        
        // Logique Fournisseur
        if (data.supplier_id) {
            setSelectedSupplierId(data.supplier_id);
            setNewSupplierName(data.supplier_name);
        } else {
            setSelectedSupplierId('new');
            setNewSupplierName(data.supplier_name || 'Nouveau Fournisseur');
        }

        // Logique Produits
        const initializedItems = data.items.map(item => ({
          ...item,
          selected_product_id: item.status === 'matched' ? item.product_id : '', 
          final_name: item.status === 'matched' ? item.product_name : item.ocr_name,
          final_qty: item.ocr_qty || 1,
          final_unit: item.ocr_unit || 'pièce',
          final_price: item.ocr_price || 0, // Prix unitaire
          batch_number: '',
          dlc: ''
        }));
        setItems(initializedItems);
        setLoading(false);
      } catch (err) {
        console.error("Erreur analyse:", err);
        setError("Impossible d'analyser la facture.");
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
    
    // Auto-remplissage si on sélectionne un produit existant
    if (field === 'selected_product_id') {
        const prod = produitsList.find(p => p.id === value);
        if (prod) {
            newItems[index].final_name = prod.nom;
            newItems[index].final_unit = prod.unite;
        } else if (value === "") {
            newItems[index].final_name = newItems[index].ocr_name;
        }
    }
    
    setItems(newItems);
  };

  // Fonction de suppression de ligne
  const handleDeleteItem = (index) => {
    const newItems = items.filter((_, i) => i !== index);
    setItems(newItems);
  };

  // Fonction d'ajout de ligne manuelle
  const handleAddItem = () => {
    setItems([...items, {
        ocr_name: "Nouvel article",
        selected_product_id: "",
        final_name: "",
        final_qty: 1,
        final_unit: "kg",
        final_price: 0,
        batch_number: "",
        dlc: ""
    }]);
  };

  const handleValidate = async () => {
    if (!window.confirm("Confirmez-vous l'import de ces produits en stock ?")) return;
    
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
            ocr_price: item.final_price, // On envoie le prix corrigé
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
      <div className="modal-content" style={{padding: '40px', textAlign: 'center'}}>
        <div style={{fontSize: '40px', marginBottom: '20px'}}>🤖</div>
        <h3>Traitement en cours...</h3>
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
    <div className="modal-overlay">
      <div className="modal-content large" style={{maxWidth: '98%', width: '1400px', height: '95vh', display: 'flex', flexDirection: 'column', padding: '0'}}>
        
        {/* HEADER FIXE */}
        <div style={{padding: '20px', borderBottom: '1px solid #eee', background: '#fff'}}>
          <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px'}}>
            <h3 style={{margin: 0}}>📝 Validation Facture</h3>
            <button onClick={onClose} style={{background: 'none', border: 'none', fontSize: '24px', cursor: 'pointer'}}>×</button>
          </div>
          
          <div style={{display: 'flex', gap: '15px', alignItems: 'center', background: '#f8f9fa', padding: '15px', borderRadius: '8px'}}>
            <div style={{fontWeight: 'bold'}}>🏢 Fournisseur :</div>
            <select 
                value={selectedSupplierId} 
                onChange={(e) => setSelectedSupplierId(e.target.value)}
                style={{padding: '8px', borderRadius: '4px', border: '1px solid #ccc', minWidth: '200px'}}
            >
                <option value="new">➕ Créer : {analysis.supplier_name}</option>
                {fournisseursList.map(f => <option key={f.id} value={f.id}>{f.nom}</option>)}
            </select>
            
            {selectedSupplierId === 'new' && (
                <input 
                    type="text" 
                    value={newSupplierName}
                    onChange={(e) => setNewSupplierName(e.target.value)}
                    placeholder="Nom du fournisseur"
                    style={{padding: '8px', border: '1px solid #f59e0b', borderRadius: '4px'}}
                />
            )}
            
            <div style={{marginLeft: 'auto', color: '#666'}}>
                Date: <strong>{analysis.facture_date}</strong> • N°: <strong>{analysis.numero_facture}</strong>
            </div>
          </div>
        </div>

        {/* TABLEAU SCROLLABLE */}
        <div style={{flex: 1, overflowY: 'auto', padding: '20px', overflowX: 'auto'}}>
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
                  
                  {/* COL 1 : NOM */}
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

                  {/* COL 2 : CORRESPONDANCE */}
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

                  {/* COL 3 : QTÉ */}
                  <td style={{padding: '10px'}}>
                    <input 
                      type="number" 
                      step="0.1"
                      style={{width: '100%', padding: '6px', textAlign: 'center', border: '1px solid #cbd5e1', borderRadius: '4px'}}
                      value={item.final_qty}
                      onChange={(e) => handleItemChange(index, 'final_qty', parseFloat(e.target.value))}
                    />
                  </td>

                  {/* COL 4 : UNITÉ */}
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

                  {/* COL 5 : PRIX UNITAIRE */}
                  <td style={{padding: '10px'}}>
                    <input 
                      type="number" 
                      step="0.01"
                      style={{width: '100%', padding: '6px', textAlign: 'right', border: '1px solid #cbd5e1', borderRadius: '4px'}}
                      value={item.final_price}
                      onChange={(e) => handleItemChange(index, 'final_price', parseFloat(e.target.value))}
                    />
                  </td>

                  {/* COL 6 : TOTAL (Calculé) */}
                  <td style={{padding: '10px', textAlign: 'right', fontWeight: 'bold', color: '#64748b'}}>
                    {(item.final_qty * item.final_price).toFixed(2)} €
                  </td>

                  {/* COL 7 : DLC & LOT */}
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

                  {/* COL 8 : SUPPRESSION */}
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
          
          <button 
            onClick={handleAddItem}
            style={{
                marginTop: '15px',
                padding: '10px 20px',
                background: '#e0f2fe',
                color: '#0284c7',
                border: '1px dashed #0284c7',
                borderRadius: '6px',
                cursor: 'pointer',
                width: '100%',
                fontWeight: 'bold'
            }}
          >
            ➕ Ajouter une ligne manuellement
          </button>
        </div>

        {/* FOOTER FIXE */}
        <div style={{padding: '20px', borderTop: '1px solid #eee', background: '#fff', display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <div style={{fontSize: '16px'}}>
            <strong>Total Facture : </strong>
            <span style={{color: '#059669', fontSize: '18px'}}>
                {items.reduce((acc, item) => acc + (item.final_qty * item.final_price), 0).toFixed(2)} €
            </span>
          </div>
          <div style={{display: 'flex', gap: '10px'}}>
            <button className="button secondary" onClick={onClose}>Annuler</button>
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
