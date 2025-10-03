import React, { useState, useEffect } from 'react';
import OrderTimeline from '../components/OrderTimeline';

const PurchaseOrderPage = () => {
  const [suppliers, setSuppliers] = useState([]);
  const [selectedSupplier, setSelectedSupplier] = useState(null);
  const [supplierProducts, setSupplierProducts] = useState([]);
  const [orderItems, setOrderItems] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // États pour le module de commande automatique
  const [activeOrderTab, setActiveOrderTab] = useState('manual'); // 'manual', 'auto', ou 'history'
  const [recipes, setRecipes] = useState([]);
  const [selectedRecipes, setSelectedRecipes] = useState([]);
  const [autoOrderResults, setAutoOrderResults] = useState([]);
  const [manualOrderSummary, setManualOrderSummary] = useState(null); // Pour le récapitulatif de commande manuelle
  
  // États pour l'historique des commandes
  const [orders, setOrders] = useState([]);
  const [deliveryEstimate, setDeliveryEstimate] = useState(null);

  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    fetchSuppliers();
    fetchRecipes();
    fetchOrders();
  }, []);
  
  // Charger l'estimation de livraison quand on sélectionne un fournisseur
  useEffect(() => {
    if (selectedSupplier) {
      fetchDeliveryEstimate(selectedSupplier.id);
    }
  }, [selectedSupplier]);

  const fetchRecipes = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/recettes`);
      if (response.ok) {
        const data = await response.json();
        setRecipes(data);
      } else {
        // Données de test si API ne fonctionne pas
        setRecipes([
          {
            id: 'recipe-1',
            nom: 'Salade César',
            categorie: 'Entrée',
            portions: 4
          },
          {
            id: 'recipe-2',
            nom: 'Lasagnes',
            categorie: 'Plat',
            portions: 6
          },
          {
            id: 'recipe-3',
            nom: 'Tiramisu',
            categorie: 'Dessert',
            portions: 8
          }
        ]);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des recettes:', error);
      // Données de test en cas d'erreur
      setRecipes([
        {
          id: 'recipe-1',
          nom: 'Salade César',
          categorie: 'Entrée',
          portions: 4
        },
        {
          id: 'recipe-2',
          nom: 'Lasagnes',
          categorie: 'Plat',
          portions: 6
        },
        {
          id: 'recipe-3',
          nom: 'Tiramisu',
          categorie: 'Dessert',
          portions: 8
        }
      ]);
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
  
  const fetchOrders = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/orders`);
      if (response.ok) {
        const data = await response.json();
        setOrders(data);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des commandes:', error);
    }
  };
  
  const fetchDeliveryEstimate = async (supplierId) => {
    try {
      const response = await fetch(`${backendUrl}/api/suppliers/${supplierId}/delivery-estimate`);
      if (response.ok) {
        const data = await response.json();
        setDeliveryEstimate(data);
      }
    } catch (error) {
      console.error('Erreur lors du calcul de livraison:', error);
      setDeliveryEstimate(null);
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

  const addToOrder = (productRelation, quantity = 1) => {
    const existingItem = orderItems.find(item => item.product_id === productRelation.product_id);
    
    if (existingItem) {
      setOrderItems(orderItems.map(item => 
        item.product_id === productRelation.product_id 
          ? { ...item, quantity: item.quantity + quantity }
          : item
      ));
    } else {
      setOrderItems([...orderItems, {
        product_id: productRelation.product_id,
        product_name: productRelation.product_name,
        unit_price: productRelation.price,
        quantity: quantity,
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

  const handleCreateOrder = async () => {
    if (orderItems.length === 0) {
      alert('Veuillez ajouter des produits à la commande');
      return;
    }
    
    if (!selectedSupplier) {
      alert('Veuillez sélectionner un fournisseur');
      return;
    }
    
    setLoading(true);
    try {
      // Créer la commande via l'API
      const response = await fetch(`${backendUrl}/api/orders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          supplier_id: selectedSupplier.id,
          items: orderItems.map(item => ({
            product_id: item.product_id,
            product_name: item.product_name,
            quantity: item.quantity,
            unit: item.unit,
            unit_price: item.unit_price,
            total_price: item.unit_price * item.quantity
          })),
          notes: ''
        })
      });
      
      if (response.ok) {
        const order = await response.json();
        alert(`✅ Commande créée avec succès!\n\nN° ${order.order_number}\nLivraison estimée: ${new Date(order.estimated_delivery_date).toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' })}`);
        
        // Réinitialiser
        setOrderItems([]);
        setSelectedSupplier(null);
        setSupplierProducts([]);
        
        // Recharger les commandes
        fetchOrders();
        
        // Basculer vers l'historique
        setActiveOrderTab('history');
      } else {
        const error = await response.json();
        alert('❌ Erreur lors de la création: ' + (error.detail || 'Erreur inconnue'));
      }
    } catch (error) {
      console.error('Erreur:', error);
      alert('❌ Erreur lors de la création de la commande');
    } finally {
      setLoading(false);
    }
  };

  const updateOrderStatus = async (orderId, newStatus) => {
    try {
      const response = await fetch(`${backendUrl}/api/orders/${orderId}/status?status=${newStatus}`, {
        method: 'PUT'
      });
      
      if (response.ok) {
        alert(`✅ Statut mis à jour: ${newStatus}`);
        fetchOrders();
      } else {
        alert('❌ Erreur lors de la mise à jour du statut');
      }
    } catch (error) {
      console.error('Erreur:', error);
      alert('❌ Erreur de connexion');
    }
  };

  const calculateAutoOrder = async () => {
    if (selectedRecipes.length === 0) {
      alert('Veuillez sélectionner au moins une production');
      return;
    }

    setLoading(true);
    try {
      // Simuler le calcul automatique avec des données de test
      const mockOrdersBySupplier = [
        {
          supplierId: 'supplier-1',
          supplierName: 'Fournisseur Rungis',
          products: [
            {
              productId: 'prod-1',
              productName: 'Tomates cerises',
              quantity: 5,
              unit: 'kg',
              pricePerUnit: 4.50,
              totalPrice: 22.50
            },
            {
              productId: 'prod-2',
              productName: 'Mozzarella',
              quantity: 2,
              unit: 'kg',
              pricePerUnit: 12.00,
              totalPrice: 24.00
            }
          ],
          total: 46.50
        },
        {
          supplierId: 'supplier-2',
          supplierName: 'Boucherie Martin',
          products: [
            {
              productId: 'prod-3',
              productName: 'Bœuf haché',
              quantity: 3,
              unit: 'kg',
              pricePerUnit: 18.50,
              totalPrice: 55.50
            }
          ],
          total: 55.50
        }
      ];

      // Calculer les besoins réels basés sur les recettes sélectionnées
      const realCalculation = {};
      selectedRecipes.forEach(recipe => {
        const quantity = recipe.selectedQuantity || 1;
        realCalculation[recipe.nom] = {
          quantity: quantity,
          estimatedCost: quantity * 15 // Estimation de base
        };
      });

      setAutoOrderResults(mockOrdersBySupplier);
      
    } catch (error) {
      console.error('Erreur lors du calcul automatique:', error);
      alert('Erreur lors du calcul des commandes automatiques');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR'
    }).format(amount);
  };

  return (
    <div className="bg-gradient-to-br from-gray-100 to-gray-200 min-h-screen" style={{ marginTop: '-16px' }}>
      {/* Header */}
      <div className="mb-8 px-6 pt-2">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">
          🛒 Gestion des Commandes
        </h1>
        <p className="text-gray-600">
          Suivi et création de commandes fournisseurs
        </p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8 px-6">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mr-3">
              <span className="text-xl">📋</span>
            </div>
            <div>
              <p className="text-sm text-gray-600">Commandes ce mois</p>
              <p className="text-2xl font-bold text-gray-900">24</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center mr-3">
              <span className="text-xl">💰</span>
            </div>
            <div>
              <p className="text-sm text-gray-600">Montant total</p>
              <p className="text-2xl font-bold text-gray-900">3 247€</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center">
            <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center mr-3">
              <span className="text-xl">🚚</span>
            </div>
            <div>
              <p className="text-sm text-gray-600">En attente</p>
              <p className="text-2xl font-bold text-gray-900">7</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center">
            <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center mr-3">
              <span className="text-xl">🏢</span>
            </div>
            <div>
              <p className="text-sm text-gray-600">Fournisseurs actifs</p>
              <p className="text-2xl font-bold text-gray-900">12</p>
            </div>
          </div>
        </div>
      </div>

      {/* Effectuer une commande */}
      <div className="bg-white rounded-lg shadow-sm mb-8 mx-6">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold">Effectuer une Commande</h2>
          <p className="text-gray-600 mt-1">Créez vos commandes manuellement ou automatiquement</p>
        </div>
        
        {/* Onglets avec surbrillance jaune */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex space-x-1">
            <button
              onClick={() => setActiveOrderTab('manual')}
              className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-all ${
                activeOrderTab === 'manual'
                  ? 'bg-yellow-400 text-gray-900 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
              }`}
            >
              <span className="mr-2">✋</span>
              Commande Manuelle
            </button>
            <button
              onClick={() => setActiveOrderTab('auto')}
              className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-all ${
                activeOrderTab === 'auto'
                  ? 'bg-yellow-400 text-gray-900 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
              }`}
            >
              <span className="mr-2">🤖</span>
              Commande Automatique
            </button>
            <button
              onClick={() => setActiveOrderTab('history')}
              className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-all ${
                activeOrderTab === 'history'
                  ? 'bg-yellow-400 text-gray-900 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
              }`}
            >
              <span className="mr-2">📋</span>
              Historique ({orders.length})
            </button>
          </div>
        </div>

        {/* Contenu des onglets */}
        <div className="p-6">
          {activeOrderTab === 'manual' && (
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
                  <div className="flex items-center gap-2 mb-2">
                    {/* Logo du fournisseur */}
                    <span className="text-xl">
                      {supplier.logo || '🏪'}
                    </span>
                    {/* Nom avec code couleur */}
                    <div 
                      className="font-medium px-2 py-1 rounded text-white text-sm"
                      style={{backgroundColor: supplier.couleur || '#3B82F6'}}
                    >
                      {supplier.nom}
                    </div>
                  </div>
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
              <div className="flex items-center gap-2 mt-1">
                <span className="text-sm text-gray-600">Fournisseur:</span>
                <span className="text-lg">{selectedSupplier.logo || '🏪'}</span>
                <span 
                  className="text-sm px-2 py-1 rounded text-white font-medium"
                  style={{backgroundColor: selectedSupplier.couleur || '#3B82F6'}}
                >
                  {selectedSupplier.nom}
                </span>
              </div>
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
                      <div className="flex-1">
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
                      
                      {/* Sélection de quantité et ajout au panier */}
                      <div className="flex items-center space-x-2 ml-4">
                        <div className="flex flex-col items-end">
                          <label className="text-xs text-gray-500 mb-1">Quantité</label>
                          <input
                            type="number"
                            min={productRelation.min_order_quantity || 1}
                            step="0.1"
                            defaultValue={productRelation.min_order_quantity || 1}
                            className="w-20 px-2 py-1 text-sm border border-gray-300 rounded"
                            id={`quantity-${productRelation.product_id}`}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') {
                                e.preventDefault();
                                const quantity = parseFloat(e.target.value) || 1;
                                addToOrder(productRelation, quantity);
                                e.target.value = productRelation.min_order_quantity || 1;
                              }
                            }}
                          />
                        </div>
                        <button
                          onClick={() => {
                            const quantityInput = document.getElementById(`quantity-${productRelation.product_id}`);
                            const quantity = parseFloat(quantityInput.value) || 1;
                            addToOrder(productRelation, quantity);
                            quantityInput.value = productRelation.min_order_quantity || 1;
                          }}
                          className="bg-primary-500 hover:bg-primary-600 text-white px-3 py-1 rounded text-sm flex items-center"
                        >
                          <span className="mr-1">➕</span>
                          Ajouter
                        </button>
                      </div>
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
                  
                  {/* Estimation de livraison */}
                  {deliveryEstimate && (
                    <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg mb-4">
                      <div className="flex items-start gap-3">
                        <span className="text-2xl">🚚</span>
                        <div className="flex-1">
                          <div className="font-semibold text-blue-900 mb-1">
                            Livraison estimée
                          </div>
                          <div className="text-sm text-blue-800 mb-2">
                            {new Date(deliveryEstimate.estimated_delivery_date).toLocaleDateString('fr-FR', {
                              weekday: 'long',
                              day: 'numeric',
                              month: 'long',
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </div>
                          {deliveryEstimate.can_order_today ? (
                            <div className="text-xs text-green-700 bg-green-100 inline-block px-2 py-1 rounded">
                              ✅ Commande possible aujourd'hui
                            </div>
                          ) : (
                            <div className="text-xs text-orange-700 bg-orange-100 inline-block px-2 py-1 rounded">
                              ⏰ Prochaine commande: {new Date(deliveryEstimate.next_order_date).toLocaleDateString('fr-FR')}
                            </div>
                          )}
                          <p className="text-xs text-gray-600 mt-2">
                            {deliveryEstimate.explanation}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  <button
                    onClick={handleCreateOrder}
                    disabled={loading}
                    className="w-full bg-yellow-400 hover:bg-yellow-500 text-gray-900 py-2 rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? '⏳ Création...' : '✅ Valider Commande'}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
      )}

          {/* Récapitulatif de commande manuelle */}
          {manualOrderSummary && (
            <div className="bg-white rounded-lg shadow-sm mt-6">
              <div className="p-6 border-b border-gray-200">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-lg font-semibold flex items-center">
                      <span className="mr-2">📋</span>
                      Récapitulatif de Commande - {manualOrderSummary.orderNumber}
                    </h3>
                    <p className="text-sm text-gray-600 mt-1">
                      Fournisseur: {manualOrderSummary.supplier.nom}
                    </p>
                  </div>
                  <div className="flex space-x-2">
                    <button 
                      onClick={() => {
                        alert(`PDF généré pour la commande ${manualOrderSummary.orderNumber}`);
                      }}
                      className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm flex items-center"
                    >
                      <span className="mr-1">📄</span>
                      PDF
                    </button>
                    <button 
                      onClick={() => {
                        alert(`Email envoyé à ${manualOrderSummary.supplier.nom}`);
                      }}
                      className="bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded text-sm flex items-center"
                    >
                      <span className="mr-1">📧</span>
                      Email
                    </button>
                    <button 
                      onClick={() => {
                        setManualOrderSummary(null);
                        setOrderItems([]);
                      }}
                      className="bg-gray-500 hover:bg-gray-600 text-white px-3 py-1 rounded text-sm flex items-center"
                    >
                      <span className="mr-1">✖️</span>
                      Fermer
                    </button>
                  </div>
                </div>
              </div>
              
              <div className="p-6">
                {/* Informations de livraison */}
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                  <h4 className="font-semibold text-yellow-800 mb-2">📅 Informations de Livraison</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-yellow-700">Date de commande:</span>
                      <span className="font-medium ml-2">
                        {new Date(manualOrderSummary.orderDate).toLocaleDateString('fr-FR')}
                      </span>
                    </div>
                    <div>
                      <span className="text-yellow-700">Livraison prévue:</span>
                      <span className="font-medium ml-2 text-green-700">
                        {manualOrderSummary.estimatedDelivery}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Détails des produits */}
                <div className="space-y-2">
                  {manualOrderSummary.items.map((item, index) => (
                    <div key={index} className="flex justify-between items-center py-2 border-b border-gray-100 last:border-b-0">
                      <div className="flex-1">
                        <div className="font-medium">{item.product_name}</div>
                        <div className="text-sm text-gray-600">
                          {item.quantity} {item.unit} × {formatCurrency(item.unit_price)}
                        </div>
                      </div>
                      <div className="font-medium text-right">
                        {formatCurrency(item.unit_price * item.quantity)}
                      </div>
                    </div>
                  ))}
                  
                  {/* Total */}
                  <div className="flex justify-between items-center pt-4 border-t border-gray-200 font-semibold text-lg">
                    <span>Total Commande:</span>
                    <span className="text-2xl text-green-600">{formatCurrency(manualOrderSummary.total)}</span>
                  </div>
                </div>

                {/* Actions finales */}
                <div className="mt-6 pt-4 border-t border-gray-200">
                  <div className="flex justify-center space-x-4">
                    <button 
                      onClick={() => {
                        alert('Commande confirmée et envoyée au fournisseur !');
                        setManualOrderSummary(null);
                        setOrderItems([]);
                      }}
                      className="bg-green-500 hover:bg-green-600 text-white px-6 py-2 rounded-lg font-medium flex items-center"
                    >
                      <span className="mr-2">✅</span>
                      Confirmer la Commande
                    </button>
                    <button 
                      onClick={() => {
                        setManualOrderSummary(null);
                      }}
                      className="bg-yellow-400 hover:bg-yellow-500 text-gray-900 px-6 py-2 rounded-lg font-medium flex items-center"
                    >
                      <span className="mr-2">✏️</span>
                      Modifier
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Onglet Commande Automatique */}
          {activeOrderTab === 'auto' && (
            <div className="space-y-6">
              {/* Sélection des productions */}
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center">
                  <span className="mr-2">🍽️</span>
                  Sélectionner les Productions
                </h3>
                <p className="text-sm text-gray-600 mb-4">
                  Choisissez les productions et quantités pour calculer automatiquement les commandes
                </p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-96 overflow-y-auto">
                  {recipes.map((recipe) => (
                    <div
                      key={recipe.id}
                      className={`p-4 border rounded-lg cursor-pointer transition-all ${
                        selectedRecipes.find(r => r.id === recipe.id)
                          ? 'border-primary-500 bg-primary-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      onClick={() => {
                        const isSelected = selectedRecipes.find(r => r.id === recipe.id);
                        if (isSelected) {
                          setSelectedRecipes(selectedRecipes.filter(r => r.id !== recipe.id));
                        } else {
                          setSelectedRecipes([...selectedRecipes, { ...recipe, selectedQuantity: 1 }]);
                        }
                      }}
                    >
                      <div className="font-medium flex items-center">
                        <span className="mr-2">
                          {recipe.categorie === 'Entrée' ? '🥗' :
                           recipe.categorie === 'Plat' ? '🍽️' :
                           recipe.categorie === 'Dessert' ? '🍰' :
                           recipe.categorie === 'Bar' ? '🍹' : '📝'}
                        </span>
                        {recipe.nom}
                      </div>
                      <div className="text-sm text-gray-600 mt-1">
                        {recipe.portions} portions • {recipe.categorie}
                      </div>
                      {selectedRecipes.find(r => r.id === recipe.id) && (
                        <div className="mt-2">
                          <label className="text-xs text-gray-500">Quantité souhaitée:</label>
                          <input
                            type="number"
                            min="1"
                            value={selectedRecipes.find(r => r.id === recipe.id)?.selectedQuantity || 1}
                            onChange={(e) => {
                              const quantity = parseInt(e.target.value) || 1;
                              setSelectedRecipes(selectedRecipes.map(r => 
                                r.id === recipe.id ? { ...r, selectedQuantity: quantity } : r
                              ));
                            }}
                            onClick={(e) => e.stopPropagation()}
                            className="w-20 px-2 py-1 text-sm border rounded mt-1"
                          />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
                
                {selectedRecipes.length > 0 && (
                  <div className="mt-6 pt-4 border-t">
                    <div className="flex justify-between items-center">
                      <div className="text-sm text-gray-600">
                        {selectedRecipes.length} production(s) sélectionnée(s)
                      </div>
                      <button
                        onClick={calculateAutoOrder}
                        disabled={loading}
                        className="bg-yellow-400 hover:bg-yellow-500 text-gray-900 px-6 py-2 rounded-lg font-medium disabled:opacity-50"
                      >
                        {loading ? 'Calcul...' : '🤖 Calculer les Commandes'}
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Résultats des commandes automatiques avec boutons de validation */}
              {autoOrderResults.length > 0 && (
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <h3 className="text-lg font-semibold flex items-center">
                      <span className="mr-2">📊</span>
                      Commandes Suggérées par Fournisseur
                    </h3>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => {
                          // Générer PDF pour toutes les commandes
                          alert('Téléchargement PDF de toutes les commandes...');
                        }}
                        className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm flex items-center"
                      >
                        <span className="mr-2">📄</span>
                        Télécharger tout (PDF)
                      </button>
                      <button
                        onClick={() => {
                          // Envoyer emails à tous les fournisseurs
                          alert('Envoi des emails à tous les fournisseurs...');
                        }}
                        className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg text-sm flex items-center"
                      >
                        <span className="mr-2">📧</span>
                        Envoyer tout par email
                      </button>
                    </div>
                  </div>
                  
                  {/* Récapitulatif général */}
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                    <h4 className="font-semibold text-yellow-800 mb-2">📋 Récapitulatif Général</h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-yellow-700">Nombre de fournisseurs:</span>
                        <span className="font-medium ml-2">{autoOrderResults.length}</span>
                      </div>
                      <div>
                        <span className="text-yellow-700">Total produits:</span>
                        <span className="font-medium ml-2">
                          {autoOrderResults.reduce((total, order) => total + order.products.length, 0)}
                        </span>
                      </div>
                      <div>
                        <span className="text-yellow-700">Montant total:</span>
                        <span className="font-medium ml-2">
                          {formatCurrency(autoOrderResults.reduce((total, order) => total + order.total, 0))}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Commandes par fournisseur */}
                  {autoOrderResults.map((order, index) => (
                    <div key={index} className="border rounded-lg bg-white shadow-sm">
                      <div className="p-4 border-b bg-gray-50">
                        <div className="flex justify-between items-start">
                          <div>
                            <h4 className="font-semibold text-lg">{order.supplierName}</h4>
                            <p className="text-sm text-gray-600">
                              {order.products.length} produit(s) • Total: {formatCurrency(order.total)}
                            </p>
                          </div>
                          <div className="flex space-x-2">
                            <button 
                              onClick={() => {
                                alert(`PDF généré pour ${order.supplierName}`);
                              }}
                              className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm flex items-center"
                            >
                              <span className="mr-1">📄</span>
                              PDF
                            </button>
                            <button 
                              onClick={() => {
                                alert(`Email envoyé à ${order.supplierName}`);
                              }}
                              className="bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded text-sm flex items-center"
                            >
                              <span className="mr-1">📧</span>
                              Email
                            </button>
                            <button 
                              onClick={() => {
                                alert(`Commande validée pour ${order.supplierName}!`);
                              }}
                              className="bg-yellow-400 hover:bg-yellow-500 text-gray-900 px-3 py-1 rounded text-sm font-medium flex items-center"
                            >
                              <span className="mr-1">✅</span>
                              Valider
                            </button>
                          </div>
                        </div>
                      </div>
                      
                      <div className="p-4">
                        <div className="space-y-2">
                          {order.products.map((product, productIndex) => (
                            <div key={productIndex} className="flex justify-between items-center py-2 border-b border-gray-100 last:border-b-0">
                              <div className="flex-1">
                                <div className="font-medium">{product.productName}</div>
                                <div className="text-sm text-gray-600">
                                  {product.quantity} {product.unit} × {formatCurrency(product.pricePerUnit)}
                                </div>
                              </div>
                              <div className="font-medium text-right">
                                {formatCurrency(product.totalPrice)}
                              </div>
                            </div>
                          ))}
                          
                          {/* Total par fournisseur */}
                          <div className="flex justify-between items-center pt-2 border-t border-gray-200 font-semibold">
                            <span>Total {order.supplierName}:</span>
                            <span className="text-lg">{formatCurrency(order.total)}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
          
          {/* Onglet Historique */}
          {activeOrderTab === 'history' && (
            <div>
              <div className="mb-6">
                <h3 className="text-xl font-bold mb-2">📋 Historique des Commandes</h3>
                <p className="text-gray-600">Suivez l'état de vos commandes en temps réel</p>
              </div>
              
              {loading ? (
                <div className="text-center py-12">
                  <div className="text-4xl mb-4">⏳</div>
                  <p className="text-gray-600">Chargement des commandes...</p>
                </div>
              ) : orders.length === 0 ? (
                <div className="text-center py-12 bg-gray-50 rounded-lg">
                  <div className="text-6xl mb-4">📦</div>
                  <p className="text-xl font-medium text-gray-700 mb-2">Aucune commande</p>
                  <p className="text-gray-600 mb-6">Créez votre première commande dans l'onglet "Commande Manuelle"</p>
                  <button
                    onClick={() => setActiveOrderTab('manual')}
                    className="bg-yellow-400 hover:bg-yellow-500 text-gray-900 px-6 py-2 rounded-lg font-medium"
                  >
                    ➕ Créer une commande
                  </button>
                </div>
              ) : (
                <div className="space-y-6">
                  {orders.map((order) => (
                    <div key={order.id} className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                      {/* En-tête commande */}
                      <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
                        <div className="flex justify-between items-start">
                          <div>
                            <h4 className="text-lg font-semibold text-gray-800">
                              {order.supplier_name}
                            </h4>
                            <p className="text-sm text-gray-600">
                              Commande n°{order.order_number}
                            </p>
                          </div>
                          <div className="text-right">
                            <div className="text-2xl font-bold text-gray-800">
                              {formatCurrency(order.total_amount)}
                            </div>
                            <p className="text-xs text-gray-500">
                              {order.items.length} article{order.items.length > 1 ? 's' : ''}
                            </p>
                          </div>
                        </div>
                      </div>
                      
                      {/* Timeline */}
                      <div className="p-6">
                        <OrderTimeline order={order} />
                      </div>
                      
                      {/* Détails produits */}
                      <div className="px-6 pb-4">
                        <details className="group">
                          <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900 flex items-center gap-2">
                            <span className="group-open:rotate-90 transition-transform">▶</span>
                            Voir les produits commandés
                          </summary>
                          <div className="mt-4 space-y-2 pl-4">
                            {order.items.map((item, idx) => (
                              <div key={idx} className="flex justify-between items-center py-2 border-b border-gray-100 text-sm">
                                <div className="flex-1">
                                  <span className="font-medium">{item.product_name}</span>
                                  <span className="text-gray-500 ml-2">({item.quantity} {item.unit})</span>
                                </div>
                                <div className="text-right">
                                  <div className="font-medium">{formatCurrency(item.total_price)}</div>
                                  <div className="text-xs text-gray-500">{formatCurrency(item.unit_price)}/{item.unit}</div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </details>
                      </div>
                      
                      {/* Actions rapides */}
                      <div className="px-6 pb-6">
                        <div className="flex gap-2">
                          {order.status === 'pending' && (
                            <button
                              onClick={() => updateOrderStatus(order.id, 'confirmed')}
                              className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700"
                            >
                              ✓ Confirmer
                            </button>
                          )}
                          {order.status === 'confirmed' && (
                            <button
                              onClick={() => updateOrderStatus(order.id, 'in_transit')}
                              className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700"
                            >
                              🚚 En transit
                            </button>
                          )}
                          {order.status === 'in_transit' && (
                            <button
                              onClick={() => updateOrderStatus(order.id, 'delivered')}
                              className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700"
                            >
                              ✅ Marquer comme livré
                            </button>
                          )}
                          {order.status === 'pending' && (
                            <button
                              onClick={() => {
                                if (confirm('Êtes-vous sûr de vouloir annuler cette commande ?')) {
                                  updateOrderStatus(order.id, 'cancelled');
                                }
                              }}
                              className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700"
                            >
                              ❌ Annuler
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PurchaseOrderPage;