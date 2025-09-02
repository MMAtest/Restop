import React, { useEffect, useState } from 'react';

const AdvancedStockPage = () => {
  const [activeTab, setActiveTab] = useState('adjustments');
  const [adjustmentHistory, setAdjustmentHistory] = useState([]);
  const [batchSummary, setBatchSummary] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showAdjustmentModal, setShowAdjustmentModal] = useState(false);
  const [adjustmentForm, setAdjustmentForm] = useState({
    adjustment_type: 'ingredient',
    target_id: '',
    quantity_adjusted: 0,
    adjustment_reason: '',
    user_name: 'Gérant'
  });
  const [availableTargets, setAvailableTargets] = useState([]);
  const [selectedBatch, setSelectedBatch] = useState(null);

  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  const fetchData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'adjustments') {
        const response = await fetch(`${backendUrl}/api/stock/adjustments-history`);
        const data = await response.json();
        setAdjustmentHistory(data);
      } else if (activeTab === 'batches') {
        const response = await fetch(`${backendUrl}/api/stock/batch-summary`);
        const data = await response.json();
        setBatchSummary(data);
      }
    } catch (error) {
      console.error('Erreur lors du chargement:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTargets = async (type) => {
    try {
      const endpoint = type === 'ingredient' ? '/api/produits' : '/api/recettes';
      const response = await fetch(`${backendUrl}${endpoint}`);
      const data = await response.json();
      setAvailableTargets(data);
    } catch (error) {
      console.error('Erreur lors du chargement des cibles:', error);
    }
  };

  const handleAdjustmentTypeChange = (type) => {
    setAdjustmentForm({ ...adjustmentForm, adjustment_type: type, target_id: '' });
    fetchTargets(type);
  };

  const handleSubmitAdjustment = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${backendUrl}/api/stock/advanced-adjustment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...adjustmentForm,
          quantity_adjusted: parseFloat(adjustmentForm.quantity_adjusted)
        })
      });

      if (response.ok) {
        setShowAdjustmentModal(false);
        setAdjustmentForm({
          adjustment_type: 'ingredient',
          target_id: '',
          quantity_adjusted: 0,
          adjustment_reason: '',
          user_name: 'Gérant'
        });
        fetchData();
        alert('Ajustement effectué avec succès!');
      } else {
        const error = await response.json();
        alert(`Erreur: ${error.detail}`);
      }
    } catch (error) {
      console.error('Erreur lors de l\'ajustement:', error);
      alert('Erreur lors de l\'ajustement');
    }
  };

  const formatDateTime = (dateStr) => {
    return new Date(dateStr).toLocaleString('fr-FR');
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR'
    }).format(amount);
  };

  const getBatchStatusColor = (status) => {
    switch (status) {
      case 'expired': return 'bg-red-100 text-red-800';
      case 'critical': return 'bg-orange-100 text-orange-800';
      default: return 'bg-green-100 text-green-800';
    }
  };

  const getBatchStatusText = (status) => {
    switch (status) {
      case 'expired': return 'Expiré';
      case 'critical': return 'Critique';
      default: return 'Bon';
    }
  };

  return (
    <div className="p-6 bg-gradient-to-br from-white to-gray-50 min-h-screen">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">
          🔧 Gestion Avancée des Stocks
        </h1>
        <p className="text-gray-600">Ajustements avancés et suivi des lots avec dates d'expiration</p>
      </div>

      {/* Tab Navigation */}
      <div className="mb-6">
        <div className="flex space-x-1 bg-white p-1 rounded-lg shadow-sm">
          <button
            onClick={() => setActiveTab('adjustments')}
            className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-all ${
              activeTab === 'adjustments'
                ? 'bg-primary-500 text-white shadow-sm'
                : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
            }`}
          >
            <span className="mr-2">⚙️</span>
            Ajustements
          </button>
          <button
            onClick={() => setActiveTab('batches')}
            className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-all ${
              activeTab === 'batches'
                ? 'bg-primary-500 text-white shadow-sm'
                : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
            }`}
          >
            <span className="mr-2">📦</span>
            Lots & Expiration
          </button>
        </div>
      </div>

      {/* Action Button */}
      <div className="mb-6">
        <button
          onClick={() => {
            setShowAdjustmentModal(true);
            fetchTargets(adjustmentForm.adjustment_type);
          }}
          className="bg-primary-500 hover:bg-primary-600 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center"
        >
          <span className="mr-2">➕</span>
          Nouvel Ajustement
        </button>
      </div>

      {/* Content */}
      {activeTab === 'adjustments' && (
        <div className="bg-white rounded-lg shadow-sm">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold flex items-center">
              <span className="mr-2">📊</span>
              Historique des Ajustements
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              Tous les ajustements de stock effectués avec traçabilité complète
            </p>
          </div>
          <div className="p-6">
            {loading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto"></div>
                <p className="mt-2 text-gray-600">Chargement...</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 px-4 font-semibold text-gray-700">Date/Heure</th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700">Type</th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700">Cible</th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700">Quantité</th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700">Raison</th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700">Utilisateur</th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700">Déductions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {adjustmentHistory.map((adjustment) => (
                      <tr key={adjustment.id} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-3 px-4 text-sm">{formatDateTime(adjustment.created_at)}</td>
                        <td className="py-3 px-4">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            adjustment.adjustment_type === 'ingredient' 
                              ? 'bg-blue-100 text-blue-800' 
                              : 'bg-green-100 text-green-800'
                          }`}>
                            {adjustment.adjustment_type === 'ingredient' ? '🥕 Ingrédient' : '🍽️ Plat Préparé'}
                          </span>
                        </td>
                        <td className="py-3 px-4 font-medium">{adjustment.target_name}</td>
                        <td className="py-3 px-4">
                          <span className={`font-semibold ${
                            adjustment.quantity_adjusted >= 0 ? 'text-green-600' : 'text-red-600'
                          }`}>
                            {adjustment.quantity_adjusted >= 0 ? '+' : ''}{adjustment.quantity_adjusted}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-sm">{adjustment.adjustment_reason}</td>
                        <td className="py-3 px-4 text-sm">{adjustment.user_name}</td>
                        <td className="py-3 px-4 text-sm">
                          {adjustment.ingredient_deductions.length > 0 ? (
                            <span className="text-blue-600">
                              {adjustment.ingredient_deductions.length} ingrédient(s)
                            </span>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                      </tr>
                    ))}
                    {adjustmentHistory.length === 0 && (
                      <tr>
                        <td colSpan="7" className="text-center py-8 text-gray-500">
                          Aucun ajustement enregistré
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'batches' && (
        <div className="space-y-6">
          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto"></div>
              <p className="mt-2 text-gray-600">Chargement...</p>
            </div>
          ) : (
            <>
              {batchSummary.map((product) => (
                <div key={product.product_id} className="bg-white rounded-lg shadow-sm">
                  <div className="p-6 border-b border-gray-200">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="text-lg font-semibold flex items-center">
                          <span className="mr-2">📦</span>
                          {product.product_name}
                        </h3>
                        <p className="text-sm text-gray-600 mt-1">
                          Stock total: {product.total_stock} • {product.batches.length} lot(s)
                        </p>
                      </div>
                      <div className="flex space-x-2">
                        {product.expired_batches > 0 && (
                          <span className="px-2 py-1 bg-red-100 text-red-800 rounded-full text-xs font-medium">
                            {product.expired_batches} expiré(s)
                          </span>
                        )}
                        {product.critical_batches > 0 && (
                          <span className="px-2 py-1 bg-orange-100 text-orange-800 rounded-full text-xs font-medium">
                            {product.critical_batches} critique(s)
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="p-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {product.batches.map((batch) => (
                        <div key={batch.id} className="border border-gray-200 rounded-lg p-4">
                          <div className="flex justify-between items-start mb-2">
                            <span className="font-medium text-sm">
                              Lot {batch.batch_number || batch.id.slice(0, 8)}
                            </span>
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getBatchStatusColor(batch.status)}`}>
                              {getBatchStatusText(batch.status)}
                            </span>
                          </div>
                          <div className="space-y-1 text-sm text-gray-600">
                            <div>Quantité: {batch.quantity}</div>
                            <div>Reçu: {formatDateTime(batch.received_date)}</div>
                            {batch.expiry_date && (
                              <div className={batch.status === 'expired' ? 'text-red-600 font-medium' : ''}>
                                Expire: {formatDateTime(batch.expiry_date)}
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
              {batchSummary.length === 0 && (
                <div className="bg-white rounded-lg shadow-sm p-8 text-center">
                  <div className="text-6xl mb-4">📦</div>
                  <h3 className="text-lg font-semibold text-gray-700 mb-2">Aucun lot enregistré</h3>
                  <p className="text-gray-500">Les lots apparaîtront ici une fois créés</p>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* Adjustment Modal */}
      {showAdjustmentModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-md w-full m-4">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold">Nouvel Ajustement de Stock</h3>
            </div>
            <form onSubmit={handleSubmitAdjustment} className="p-6">
              <div className="space-y-4">
                {/* Adjustment Type */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Type d'ajustement
                  </label>
                  <div className="flex space-x-4">
                    <label className="flex items-center">
                      <input
                        type="radio"
                        name="adjustment_type"
                        value="ingredient"
                        checked={adjustmentForm.adjustment_type === 'ingredient'}
                        onChange={(e) => handleAdjustmentTypeChange(e.target.value)}
                        className="mr-2"
                      />
                      🥕 Ajuster un Ingrédient
                    </label>
                    <label className="flex items-center">
                      <input
                        type="radio"
                        name="adjustment_type"
                        value="prepared_dish"
                        checked={adjustmentForm.adjustment_type === 'prepared_dish'}
                        onChange={(e) => handleAdjustmentTypeChange(e.target.value)}
                        className="mr-2"
                      />
                      🍽️ Ajuster un Plat Préparé
                    </label>
                  </div>
                </div>

                {/* Target Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {adjustmentForm.adjustment_type === 'ingredient' ? 'Ingrédient' : 'Recette'}
                  </label>
                  <select
                    value={adjustmentForm.target_id}
                    onChange={(e) => setAdjustmentForm({...adjustmentForm, target_id: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-md"
                    required
                  >
                    <option value="">Sélectionner...</option>
                    {availableTargets.map((target) => (
                      <option key={target.id} value={target.id}>
                        {target.nom}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Quantity */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Quantité {adjustmentForm.adjustment_type === 'prepared_dish' ? '(portions)' : ''}
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={adjustmentForm.quantity_adjusted}
                    onChange={(e) => setAdjustmentForm({...adjustmentForm, quantity_adjusted: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-md"
                    placeholder="Quantité (+ pour ajouter, - pour retirer)"
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    {adjustmentForm.adjustment_type === 'prepared_dish' 
                      ? 'Nombre négatif = plats préparés consommés (déduit automatiquement tous les ingrédients)'
                      : 'Nombre positif = ajout, nombre négatif = retrait'
                    }
                  </p>
                </div>

                {/* Reason */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Raison de l'ajustement
                  </label>
                  <textarea
                    value={adjustmentForm.adjustment_reason}
                    onChange={(e) => setAdjustmentForm({...adjustmentForm, adjustment_reason: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-md"
                    rows="3"
                    placeholder="Expliquez la raison de cet ajustement..."
                    required
                  />
                </div>

                {/* User Name */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Utilisateur
                  </label>
                  <input
                    type="text"
                    value={adjustmentForm.user_name}
                    onChange={(e) => setAdjustmentForm({...adjustmentForm, user_name: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-md"
                    required
                  />
                </div>
              </div>

              <div className="flex justify-end space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowAdjustmentModal(false)}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  className="bg-primary-500 hover:bg-primary-600 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                >
                  Effectuer l'Ajustement
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdvancedStockPage;