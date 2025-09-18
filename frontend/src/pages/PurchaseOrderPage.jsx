import React, { useState, useEffect } from 'react';

const PurchaseOrderPage = () => {
  const [suppliers, setSuppliers] = useState([]);
  const [selectedSupplier, setSelectedSupplier] = useState(null);
  const [supplierProducts, setSupplierProducts] = useState([]);
  const [orderItems, setOrderItems] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // États pour le module de commande automatique
  const [activeOrderTab, setActiveOrderTab] = useState('manual'); // 'manual' ou 'auto'
  const [recipes, setRecipes] = useState([]);
  const [selectedRecipes, setSelectedRecipes] = useState([]);
  const [autoOrderResults, setAutoOrderResults] = useState([]);

  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    fetchSuppliers();
    fetchRecipes();
  }, []);

  const fetchRecipes = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/recettes`);
      if (response.ok) {
        const data = await response.json();
        setRecipes(data);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des recettes:', error);
    }
  };

  const fetchSuppliers = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/fournisseurs`);
      if (response.ok) {
        const data = await response.json();
        setSuppliers(data);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des fournisseurs:', error);
    }
  };

  const handleSupplierSelect = async (supplier) => {
    setSelectedSupplier(supplier);
    setLoading(true);
    try {
      // Get products from this supplier
      const response = await fetch(`${backendUrl}/api/supplier-product-info/${supplier.id}`);
      if (response.ok) {
        const data = await response.json();
        
        // Get product details for each relation
        const productsWithDetails = await Promise.all(
          data.map(async (relation) => {
            const productResponse = await fetch(`${backendUrl}/api/produits/${relation.product_id}`);
            if (productResponse.ok) {
              const product = await productResponse.json();
              return {
                ...relation,
                product_name: product.nom,
                product_unit: product.unite,
                product_category: product.categorie
              };
            }
            return relation;
          })
        );
        
        setSupplierProducts(productsWithDetails);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des produits:', error);
    } finally {
      setLoading(false);
    }
  };

  const addToOrder = (productRelation) => {
    const existingItem = orderItems.find(item => item.product_id === productRelation.product_id);
    
    if (existingItem) {
      setOrderItems(orderItems.map(item => 
        item.product_id === productRelation.product_id 
          ? { ...item, quantity: item.quantity + 1 }
          : item
      ));
    } else {
      setOrderItems([...orderItems, {
        product_id: productRelation.product_id,
        product_name: productRelation.product_name,
        unit_price: productRelation.price,
        quantity: 1,
        unit: productRelation.product_unit
      }]);
    }
  };

  const updateQuantity = (productId, newQuantity) => {
    if (newQuantity <= 0) {
      setOrderItems(orderItems.filter(item => item.product_id !== productId));
    } else {
      setOrderItems(orderItems.map(item => 
        item.product_id === productId 
          ? { ...item, quantity: newQuantity }
          : item
      ));
    }
  };

  const getTotalOrder = () => {
    return orderItems.reduce((total, item) => total + (item.unit_price * item.quantity), 0);
  };

  const handleCreateOrder = () => {
    if (orderItems.length === 0) {
      alert('Veuillez ajouter des produits à la commande');
      return;
    }
    
    const orderData = {
      supplier: selectedSupplier,
      items: orderItems,
      total: getTotalOrder(),
      date: new Date().toISOString()
    };
    
    console.log('Commande créée:', orderData);
    alert(`Commande créée pour ${selectedSupplier.nom} - Total: ${getTotalOrder().toFixed(2)}€`);
    
    // Reset order
    setOrderItems([]);
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR'
    }).format(amount);
  };

  return (
    <div className="p-6 bg-gradient-to-br from-gray-100 to-gray-200 min-h-screen">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">
          🛒 Création de Commandes Fournisseurs
        </h1>
        <p className="text-gray-600">
          Workflow de commande avec tarifs fournisseurs spécifiques
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Supplier Selection */}
        <div className="bg-white rounded-lg shadow-sm">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold flex items-center">
              <span className="mr-2">🏢</span>
              1. Sélectionner le Fournisseur
            </h3>
          </div>
          <div className="p-6">
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {suppliers.map((supplier) => (
                <div
                  key={supplier.id}
                  className={`p-3 border rounded-lg cursor-pointer transition-all ${
                    selectedSupplier?.id === supplier.id
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => handleSupplierSelect(supplier)}
                >
                  <div className="font-medium">{supplier.nom}</div>
                  <div className="text-sm text-gray-600">
                    {supplier.telephone && (
                      <span className="mr-3">📞 {supplier.telephone}</span>
                    )}
                    {supplier.email && (
                      <span>📧 {supplier.email}</span>
                    )}
                  </div>
                  {supplier.specialites && (
                    <div className="text-xs text-gray-500 mt-1">
                      Spécialités: {supplier.specialites}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Products Selection */}
        <div className="bg-white rounded-lg shadow-sm">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold flex items-center">
              <span className="mr-2">📦</span>
              2. Produits Disponibles
            </h3>
            {selectedSupplier && (
              <p className="text-sm text-gray-600 mt-1">
                Fournisseur: {selectedSupplier.nom}
              </p>
            )}
          </div>
          <div className="p-6">
            {!selectedSupplier ? (
              <div className="text-center py-8 text-gray-500">
                <div className="text-4xl mb-2">🏢</div>
                <p>Sélectionnez un fournisseur pour voir ses produits</p>
              </div>
            ) : loading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto"></div>
                <p className="mt-2 text-gray-600">Chargement des produits...</p>
              </div>
            ) : supplierProducts.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <div className="text-4xl mb-2">📦</div>
                <p>Aucun produit disponible pour ce fournisseur</p>
              </div>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {supplierProducts.map((productRelation) => (
                  <div
                    key={productRelation.product_id}
                    className="p-3 border border-gray-200 rounded-lg"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="font-medium">{productRelation.product_name}</div>
                        <div className="text-sm text-gray-600">
                          {formatCurrency(productRelation.price)} / {productRelation.product_unit}
                        </div>
                        {productRelation.product_category && (
                          <div className="text-xs text-gray-500">
                            {productRelation.product_category}
                          </div>
                        )}
                        {productRelation.min_order_quantity && (
                          <div className="text-xs text-orange-600">
                            Commande min: {productRelation.min_order_quantity}
                          </div>
                        )}
                      </div>
                      <button
                        onClick={() => addToOrder(productRelation)}
                        className="bg-primary-500 hover:bg-primary-600 text-white px-3 py-1 rounded text-sm"
                      >
                        Ajouter
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Order Summary */}
        <div className="bg-white rounded-lg shadow-sm">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold flex items-center">
              <span className="mr-2">🛒</span>
              3. Panier de Commande
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              {orderItems.length} article{orderItems.length > 1 ? 's' : ''}
            </p>
          </div>
          <div className="p-6">
            {orderItems.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <div className="text-4xl mb-2">🛒</div>
                <p>Panier vide</p>
                <p className="text-sm">Ajoutez des produits pour créer une commande</p>
              </div>
            ) : (
              <>
                <div className="space-y-3 max-h-64 overflow-y-auto mb-4">
                  {orderItems.map((item) => (
                    <div
                      key={item.product_id}
                      className="p-3 border border-gray-200 rounded-lg"
                    >
                      <div className="flex justify-between items-start mb-2">
                        <div className="font-medium">{item.product_name}</div>
                        <button
                          onClick={() => updateQuantity(item.product_id, 0)}
                          className="text-red-500 hover:text-red-700 text-sm"
                        >
                          ✕
                        </button>
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="text-sm text-gray-600">
                          {formatCurrency(item.unit_price)} / {item.unit}
                        </div>
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => updateQuantity(item.product_id, item.quantity - 1)}
                            className="bg-gray-200 hover:bg-gray-300 text-gray-700 w-6 h-6 rounded text-sm"
                          >
                            -
                          </button>
                          <span className="w-8 text-center">{item.quantity}</span>
                          <button
                            onClick={() => updateQuantity(item.product_id, item.quantity + 1)}
                            className="bg-gray-200 hover:bg-gray-300 text-gray-700 w-6 h-6 rounded text-sm"
                          >
                            +
                          </button>
                        </div>
                      </div>
                      <div className="text-right text-sm font-medium mt-1">
                        Total: {formatCurrency(item.unit_price * item.quantity)}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Order Total */}
                <div className="border-t border-gray-200 pt-4">
                  <div className="flex justify-between items-center mb-4">
                    <span className="text-lg font-semibold">Total Commande:</span>
                    <span className="text-xl font-bold text-primary-600">
                      {formatCurrency(getTotalOrder())}
                    </span>
                  </div>
                  
                  {selectedSupplier && (
                    <div className="bg-gray-50 p-3 rounded-lg mb-4">
                      <div className="text-sm">
                        <div className="font-medium">Fournisseur: {selectedSupplier.nom}</div>
                        {selectedSupplier.conditions_paiement && (
                          <div className="text-gray-600">
                            Conditions: {selectedSupplier.conditions_paiement}
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  <button
                    onClick={handleCreateOrder}
                    className="w-full bg-primary-500 hover:bg-primary-600 text-white py-2 rounded-lg font-medium"
                  >
                    Créer la Commande
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Order History Preview */}
      <div className="mt-8 bg-white rounded-lg shadow-sm">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold flex items-center">
            <span className="mr-2">📋</span>
            Historique des Commandes (Aperçu)
          </h3>
        </div>
        <div className="p-6">
          <div className="text-center py-8 text-gray-500">
            <div className="text-4xl mb-2">📋</div>
            <p>Fonctionnalité à venir</p>
            <p className="text-sm">L'historique des commandes sera affiché ici</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PurchaseOrderPage;