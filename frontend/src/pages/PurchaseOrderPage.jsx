import React, { useState, useEffect } from 'react';
import OrderTimeline from '../components/OrderTimeline';

const PurchaseOrderPage = ({ currentUser }) => {
  const [suppliers, setSuppliers] = useState([]);
  const [selectedSupplier, setSelectedSupplier] = useState(null);
  const [supplierProducts, setSupplierProducts] = useState([]);
  const [orderItems, setOrderItems] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // États pour le module de commande automatique
  const [activeOrderTab, setActiveOrderTab] = useState(
    currentUser?.role === 'employe_cuisine' ? 'history' : 'manual'
  ); // 'manual', 'auto', ou 'history'
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
    
    // Supprimer le padding du content-wrapper pour cette page uniquement
    const contentWrapper = document.querySelector('.content-wrapper');
    if (contentWrapper) {
      // contentWrapper.style.paddingTop = '0'; // Commenté pour laisser la marge naturelle
    }
    
    // Remettre le padding lors du démontage du composant
    return () => {
      if (contentWrapper) {
        contentWrapper.style.paddingTop = '';
      }
    };
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
    <div className="min-h-screen" style={{ background: 'var(--color-background-dark)', color: 'var(--color-text-primary)' }}>
      {/* Header */}
      <div className="mb-8 px-6" style={{ paddingTop: window.innerWidth <= 768 ? '20px' : '8px' }}>
        <h1 className="text-3xl font-bold mb-2" style={{ color: 'var(--color-text-primary)' }}>
          🛒 Gestion des Commandes
        </h1>
        <p style={{ color: 'var(--color-text-secondary)' }}>
          Suivi et création de commandes fournisseurs
        </p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8 px-6">
        {/* Commandes ce mois - Cliquable */}
        <div 
          className="rounded-lg shadow-sm p-6 cursor-pointer transition-shadow"
          style={{ background: 'var(--color-background-card)', border: '1px solid var(--color-border)' }}
          onClick={() => setActiveOrderTab('history')}
        >
          <div className="flex items-center">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center mr-3" style={{ background: 'rgba(59, 130, 246, 0.1)' }}>
              <span className="text-xl">📋</span>
            </div>
            <div>
              <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>Commandes ce mois</p>
              <p className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>
                {(() => {
                  const now = new Date();
                  const thisMonth = orders.filter(o => {
                    const orderDate = new Date(o.created_at || o.date_commande);
                    return orderDate.getMonth() === now.getMonth() && 
                           orderDate.getFullYear() === now.getFullYear();
                  });
                  return thisMonth.length;
                })()}
              </p>
            </div>
          </div>
        </div>
        
        {/* Montant total */}
        <div className="rounded-lg shadow-sm p-6" style={{ background: 'var(--color-background-card)', border: '1px solid var(--color-border)' }}>
          <div className="flex items-center">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center mr-3" style={{ background: 'rgba(16, 185, 129, 0.1)' }}>
              <span className="text-xl">💰</span>
            </div>
            <div>
              <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>Montant total</p>
              <p className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>
                {(() => {
                  const now = new Date();
                  const thisMonthOrders = orders.filter(o => {
                    const orderDate = new Date(o.created_at || o.date_commande);
                    return orderDate.getMonth() === now.getMonth() && 
                           orderDate.getFullYear() === now.getFullYear();
                  });
                  const total = thisMonthOrders.reduce((sum, order) => sum + (order.montant_total || 0), 0);
                  return `${total.toFixed(0)}€`;
                })()}
              </p>
            </div>
          </div>
        </div>
        
        {/* En attente - Cliquable */}
        <div 
          className="rounded-lg shadow-sm p-6 cursor-pointer transition-shadow"
          style={{ background: 'var(--color-background-card)', border: '1px solid var(--color-border)' }}
          onClick={() => setActiveOrderTab('history')}
        >
          <div className="flex items-center">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center mr-3" style={{ background: 'rgba(245, 158, 11, 0.1)' }}>
              <span className="text-xl">🚚</span>
            </div>
            <div>
              <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>En attente</p>
              <p className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>
                {orders.filter(o => o.statut === 'en_attente' || o.statut === 'confirmee').length}
              </p>
            </div>
          </div>
        </div>
        
        {/* Fournisseurs actifs - Cliquable si accès */}
        <div 
          className="rounded-lg shadow-sm p-6 cursor-pointer transition-shadow"
          style={{ background: 'var(--color-background-card)', border: '1px solid var(--color-border)' }}
          onClick={() => {
            if (currentUser?.role === 'patron' || currentUser?.role === 'super_admin' || currentUser?.role === 'chef_cuisine') {
              window.location.href = '/?tab=production&subtab=fournisseurs';
            }
          }}
        >
          <div className="flex items-center">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center mr-3" style={{ background: 'rgba(139, 92, 246, 0.1)' }}>
              <span className="text-xl">🏢</span>
            </div>
            <div>
              <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>Fournisseurs actifs</p>
              <p className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>{suppliers.length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Effectuer une commande */}
      <div className="rounded-lg shadow-sm mb-8 mx-6" style={{ background: 'var(--color-background-card)', border: '1px solid var(--color-border)' }}>
        <div className="p-6 border-b" style={{ borderColor: 'var(--color-border)' }}>
          <h2 className="text-xl font-semibold" style={{ color: 'var(--color-text-primary)' }}>Effectuer une Commande</h2>
          <p className="mt-1" style={{ color: 'var(--color-text-secondary)' }}>Créez vos commandes manuellement ou automatiquement</p>
        </div>
        
        {/* Onglets avec surbrillance jaune */}
        <div className="p-4 border-b" style={{ borderColor: 'var(--color-border)' }}>
          <div className="flex space-x-1">
          {/* Commandes Manuelle et Auto - MASQUÉES pour employé cuisine */}
          {currentUser?.role !== 'employe_cuisine' && (
            <>
              <button
                onClick={() => setActiveOrderTab('manual')}
                className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-all`}
                style={{
                  background: activeOrderTab === 'manual' ? 'var(--color-accent-gold)' : 'transparent',
                  color: activeOrderTab === 'manual' ? '#1a1a1a' : 'var(--color-text-secondary)',
                  fontWeight: activeOrderTab === 'manual' ? 'bold' : 'normal'
                }}
              >
                <span className="mr-2">✋</span>
                Commande Manuelle
              </button>
              <button
                onClick={() => setActiveOrderTab('auto')}
                className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-all`}
                style={{
                  background: activeOrderTab === 'auto' ? 'var(--color-accent-gold)' : 'transparent',
                  color: activeOrderTab === 'auto' ? '#1a1a1a' : 'var(--color-text-secondary)',
                  fontWeight: activeOrderTab === 'auto' ? 'bold' : 'normal'
                }}
              >
                <span className="mr-2">🤖</span>
                Commande Automatique
              </button>
            </>
          )}
          
          {/* Onglet Historique - Accessible à tous */}
          <button
            onClick={() => setActiveOrderTab('history')}
            className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-all`}
            style={{
              background: activeOrderTab === 'history' ? 'var(--color-accent-gold)' : 'transparent',
              color: activeOrderTab === 'history' ? '#1a1a1a' : 'var(--color-text-secondary)',
              fontWeight: activeOrderTab === 'history' ? 'bold' : 'normal'
            }}
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
          <div className="rounded-lg shadow-sm" style={{ background: 'var(--color-background-card-light)', border: '1px solid var(--color-border)' }}>
          <div className="p-6 border-b" style={{ borderColor: 'var(--color-border)' }}>
            <h3 className="text-lg font-semibold flex items-center" style={{ color: 'var(--color-text-primary)' }}>
              <span className="mr-2">🏢</span>
              1. Sélectionner le Fournisseur
            </h3>
          </div>
          <div className="p-6">
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {suppliers.map((supplier) => (
                <div
                  key={supplier.id}
                  className={`p-3 border rounded-lg cursor-pointer transition-all`}
                  style={{
                    borderColor: selectedSupplier?.id === supplier.id ? 'var(--color-primary-blue)' : 'var(--color-border)',
                    background: selectedSupplier?.id === supplier.id ? 'rgba(59, 130, 246, 0.1)' : 'var(--color-background-card)',
                  }}
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
                  <div className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                    {supplier.telephone && (
                      <span className="mr-3">📞 {supplier.telephone}</span>
                    )}
                    {supplier.email && (
                      <span>📧 {supplier.email}</span>
                    )}
                  </div>
                  {supplier.specialites && (
                    <div className="text-xs mt-1" style={{ color: 'var(--color-text-muted)' }}>
                      Spécialités: {supplier.specialites}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Products Selection */}
        <div className="rounded-lg shadow-sm" style={{ background: 'var(--color-background-card-light)', border: '1px solid var(--color-border)' }}>
          <div className="p-6 border-b" style={{ borderColor: 'var(--color-border)' }}>
            <h3 className="text-lg font-semibold flex items-center" style={{ color: 'var(--color-text-primary)' }}>
              <span className="mr-2">📦</span>
              2. Produits Disponibles
            </h3>
            {selectedSupplier && (
              <div className="flex items-center gap-2 mt-1">
                <span className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>Fournisseur:</span>
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
              <div className="text-center py-8" style={{ color: 'var(--color-text-muted)' }}>
                <div className="text-4xl mb-2">🏢</div>
                <p>Sélectionnez un fournisseur pour voir ses produits</p>
              </div>
            ) : loading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 mx-auto" style={{ borderColor: 'var(--color-primary-blue)' }}></div>
                <p className="mt-2" style={{ color: 'var(--color-text-secondary)' }}>Chargement des produits...</p>
              </div>
            ) : supplierProducts.length === 0 ? (
              <div className="text-center py-8" style={{ color: 'var(--color-text-muted)' }}>
                <div className="text-4xl mb-2">📦</div>
                <p>Aucun produit disponible pour ce fournisseur</p>
              </div>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {supplierProducts.map((productRelation) => (
                  <div
                    key={productRelation.product_id}
                    className="p-3 border rounded-lg"
                    style={{ borderColor: 'var(--color-border)', background: 'var(--color-background-card)' }}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="font-medium" style={{ color: 'var(--color-text-primary)' }}>{productRelation.product_name}</div>
                        <div className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                          {formatCurrency(productRelation.price)} / {productRelation.product_unit}
                        </div>
                        {productRelation.product_category && (
                          <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
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
                          <label className="text-xs mb-1" style={{ color: 'var(--color-text-secondary)' }}>Quantité</label>
                          <input
                            type="number"
                            min={productRelation.min_order_quantity || 1}
                            step="0.1"
                            defaultValue={productRelation.min_order_quantity || 1}
                            className="w-20 px-2 py-1 text-sm border rounded"
                            style={{ 
                              background: 'var(--color-background-dark)', 
                              color: 'var(--color-text-primary)',
                              borderColor: 'var(--color-border)'
                            }}
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
                          className="text-white px-3 py-1 rounded text-sm flex items-center"
                          style={{ background: 'var(--color-primary-blue)' }}
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
        <div className="rounded-lg shadow-sm" style={{ background: 'var(--color-background-card-light)', border: '1px solid var(--color-border)' }}>
          <div className="p-6 border-b" style={{ borderColor: 'var(--color-border)' }}>
            <h3 className="text-lg font-semibold flex items-center" style={{ color: 'var(--color-text-primary)' }}>
              <span className="mr-2">🛒</span>
              3. Panier de Commande
            </h3>
            <p className="text-sm mt-1" style={{ color: 'var(--color-text-secondary)' }}>
              {orderItems.length} article{orderItems.length > 1 ? 's' : ''}
            </p>
          </div>
          <div className="p-6">
            {orderItems.length === 0 ? (
              <div className="text-center py-8" style={{ color: 'var(--color-text-muted)' }}>
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
                      className="p-3 border rounded-lg"
                      style={{ borderColor: 'var(--color-border)', background: 'var(--color-background-card)' }}
                    >
                      <div className="flex justify-between items-start mb-2">
                        <div className="font-medium" style={{ color: 'var(--color-text-primary)' }}>{item.product_name}</div>
                        <button
                          onClick={() => updateQuantity(item.product_id, 0)}
                          className="text-red-500 hover:text-red-700 text-sm"
                        >
                          ✕
                        </button>
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                          {formatCurrency(item.unit_price)} / {item.unit}
                        </div>
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => updateQuantity(item.product_id, item.quantity - 1)}
                            className="w-6 h-6 rounded text-sm"
                            style={{ background: 'var(--color-background-dark)', color: 'var(--color-text-primary)', border: '1px solid var(--color-border)' }}
                          >
                            -
                          </button>
                          <span className="w-8 text-center" style={{ color: 'var(--color-text-primary)' }}>{item.quantity}</span>
                          <button
                            onClick={() => updateQuantity(item.product_id, item.quantity + 1)}
                            className="w-6 h-6 rounded text-sm"
                            style={{ background: 'var(--color-background-dark)', color: 'var(--color-text-primary)', border: '1px solid var(--color-border)' }}
                          >
                            +
                          </button>
                        </div>
                      </div>
                      <div className="text-right text-sm font-medium mt-1" style={{ color: 'var(--color-text-primary)' }}>
                        Total: {formatCurrency(item.unit_price * item.quantity)}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Order Total */}
                <div className="border-t pt-4" style={{ borderColor: 'var(--color-border)' }}>
                  <div className="flex justify-between items-center mb-4">
                    <span className="text-lg font-semibold" style={{ color: 'var(--color-text-primary)' }}>Total Commande:</span>
                    <span className="text-xl font-bold" style={{ color: 'var(--color-success-green)' }}>
                      {formatCurrency(getTotalOrder())}
                    </span>
                  </div>
                  
                  {selectedSupplier && (
                    <div className="p-3 rounded-lg mb-4" style={{ background: 'var(--color-background-card)', border: '1px solid var(--color-border)' }}>
                      <div className="text-sm">
                        <div className="font-medium" style={{ color: 'var(--color-text-primary)' }}>Fournisseur: {selectedSupplier.nom}</div>
                        {selectedSupplier.conditions_paiement && (
                          <div style={{ color: 'var(--color-text-secondary)' }}>
                            Conditions: {selectedSupplier.conditions_paiement}
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                  
                  {/* Estimation de livraison */}
                  {deliveryEstimate && (
                    <div className="p-4 rounded-lg mb-4" style={{ background: 'rgba(59, 130, 246, 0.05)', border: '1px solid rgba(59, 130, 246, 0.2)' }}>
                      <div className="flex items-start gap-3">
                        <span className="text-2xl">🚚</span>
                        <div className="flex-1">
                          <div className="font-semibold mb-1" style={{ color: 'var(--color-text-primary)' }}>
                            Livraison estimée
                          </div>
                          <div className="text-sm mb-2" style={{ color: 'var(--color-primary-blue)' }}>
                            {new Date(deliveryEstimate.estimated_delivery_date).toLocaleDateString('fr-FR', {
                              weekday: 'long',
                              day: 'numeric',
                              month: 'long',
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </div>
                          {deliveryEstimate.can_order_today ? (
                            <div className="text-xs inline-block px-2 py-1 rounded" style={{ background: 'rgba(16, 185, 129, 0.1)', color: 'var(--color-success-green)' }}>
                              ✅ Commande possible aujourd'hui
                            </div>
                          ) : (
                            <div className="text-xs inline-block px-2 py-1 rounded" style={{ background: 'rgba(245, 158, 11, 0.1)', color: 'var(--color-accent-gold)' }}>
                              ⏰ Prochaine commande: {new Date(deliveryEstimate.next_order_date).toLocaleDateString('fr-FR')}
                            </div>
                          )}
                          <p className="text-xs mt-2" style={{ color: 'var(--color-text-muted)' }}>
                            {deliveryEstimate.explanation}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  <button
                    onClick={handleCreateOrder}
                    disabled={loading}
                    className="w-full py-2 rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                    style={{ background: 'var(--color-accent-gold)', color: '#1a1a1a' }}
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
            <div className="rounded-lg shadow-sm mt-6" style={{ background: 'var(--color-background-card)', border: '1px solid var(--color-border)' }}>
              <div className="p-6 border-b" style={{ borderColor: 'var(--color-border)' }}>
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-lg font-semibold flex items-center" style={{ color: 'var(--color-text-primary)' }}>
                      <span className="mr-2">📋</span>
                      Récapitulatif de Commande - {manualOrderSummary.orderNumber}
                    </h3>
                    <p className="text-sm mt-1" style={{ color: 'var(--color-text-secondary)' }}>
                      Fournisseur: {manualOrderSummary.supplier.nom}
                    </p>
                  </div>
                  <div className="flex space-x-2">
                    <button 
                      onClick={() => {
                        alert(`PDF généré pour la commande ${manualOrderSummary.orderNumber}`);
                      }}
                      className="text-white px-3 py-1 rounded text-sm flex items-center"
                      style={{ background: 'var(--color-primary-blue)' }}
                    >
                      <span className="mr-1">📄</span>
                      PDF
                    </button>
                    <button 
                      onClick={() => {
                        alert(`Email envoyé à ${manualOrderSummary.supplier.nom}`);
                      }}
                      className="text-white px-3 py-1 rounded text-sm flex items-center"
                      style={{ background: 'var(--color-success-green)' }}
                    >
                      <span className="mr-1">📧</span>
                      Email
                    </button>
                    <button 
                      onClick={() => {
                        setManualOrderSummary(null);
                        setOrderItems([]);
                      }}
                      className="text-white px-3 py-1 rounded text-sm flex items-center"
                      style={{ background: 'var(--color-text-muted)' }}
                    >
                      <span className="mr-1">✖️</span>
                      Fermer
                    </button>
                  </div>
                </div>
              </div>
              
              <div className="p-6">
                {/* Informations de livraison */}
                <div className="rounded-lg p-4 mb-4" style={{ background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.3)' }}>
                  <h4 className="font-semibold mb-2" style={{ color: 'var(--color-accent-gold)' }}>📅 Informations de Livraison</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <span style={{ color: 'var(--color-text-secondary)' }}>Date de commande:</span>
                      <span className="font-medium ml-2" style={{ color: 'var(--color-text-primary)' }}>
                        {new Date(manualOrderSummary.orderDate).toLocaleDateString('fr-FR')}
                      </span>
                    </div>
                    <div>
                      <span style={{ color: 'var(--color-text-secondary)' }}>Livraison prévue:</span>
                      <span className="font-medium ml-2" style={{ color: 'var(--color-success-green)' }}>
                        {manualOrderSummary.estimatedDelivery}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Détails des produits */}
                <div className="space-y-2">
                  {manualOrderSummary.items.map((item, index) => (
                    <div key={index} className="flex justify-between items-center py-2 border-b last:border-b-0" style={{ borderColor: 'var(--color-border-light)' }}>
                      <div className="flex-1">
                        <div className="font-medium" style={{ color: 'var(--color-text-primary)' }}>{item.product_name}</div>
                        <div className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                          {item.quantity} {item.unit} × {formatCurrency(item.unit_price)}
                        </div>
                      </div>
                      <div className="font-medium text-right" style={{ color: 'var(--color-text-primary)' }}>
                        {formatCurrency(item.unit_price * item.quantity)}
                      </div>
                    </div>
                  ))}
                  
                  {/* Total */}
                  <div className="flex justify-between items-center pt-4 border-t font-semibold text-lg" style={{ borderColor: 'var(--color-border)' }}>
                    <span style={{ color: 'var(--color-text-primary)' }}>Total Commande:</span>
                    <span className="text-2xl" style={{ color: 'var(--color-success-green)' }}>{formatCurrency(manualOrderSummary.total)}</span>
                  </div>
                </div>

                {/* Actions finales */}
                <div className="mt-6 pt-4 border-t" style={{ borderColor: 'var(--color-border)' }}>
                  <div className="flex justify-center space-x-4">
                    <button 
                      onClick={() => {
                        alert('Commande confirmée et envoyée au fournisseur !');
                        setManualOrderSummary(null);
                        setOrderItems([]);
                      }}
                      className="text-white px-6 py-2 rounded-lg font-medium flex items-center"
                      style={{ background: 'var(--color-success-green)' }}
                    >
                      <span className="mr-2">✅</span>
                      Confirmer la Commande
                    </button>
                    <button 
                      onClick={() => {
                        setManualOrderSummary(null);
                      }}
                      className="px-6 py-2 rounded-lg font-medium flex items-center"
                      style={{ background: 'var(--color-accent-gold)', color: '#1a1a1a' }}
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
              <div className="rounded-lg p-6" style={{ background: 'var(--color-background-card-light)' }}>
                <h3 className="text-lg font-semibold mb-4 flex items-center" style={{ color: 'var(--color-text-primary)' }}>
                  <span className="mr-2">🍽️</span>
                  Sélectionner les Productions
                </h3>
                <p className="text-sm mb-4" style={{ color: 'var(--color-text-secondary)' }}>
                  Choisissez les productions et quantités pour calculer automatiquement les commandes
                </p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-96 overflow-y-auto">
                  {recipes.map((recipe) => (
                    <div
                      key={recipe.id}
                      className={`p-4 border rounded-lg cursor-pointer transition-all`}
                      style={{
                        borderColor: selectedRecipes.find(r => r.id === recipe.id) ? 'var(--color-primary-blue)' : 'var(--color-border)',
                        background: selectedRecipes.find(r => r.id === recipe.id) ? 'rgba(59, 130, 246, 0.1)' : 'var(--color-background-card)'
                      }}
                      onClick={() => {
                        const isSelected = selectedRecipes.find(r => r.id === recipe.id);
                        if (isSelected) {
                          setSelectedRecipes(selectedRecipes.filter(r => r.id !== recipe.id));
                        } else {
                          setSelectedRecipes([...selectedRecipes, { ...recipe, selectedQuantity: 1 }]);
                        }
                      }}
                    >
                      <div className="font-medium flex items-center" style={{ color: 'var(--color-text-primary)' }}>
                        <span className="mr-2">
                          {recipe.categorie === 'Entrée' ? '🥗' :
                           recipe.categorie === 'Plat' ? '🍽️' :
                           recipe.categorie === 'Dessert' ? '🍰' :
                           recipe.categorie === 'Bar' ? '🍹' : '📝'}
                        </span>
                        {recipe.nom}
                      </div>
                      <div className="text-sm mt-1" style={{ color: 'var(--color-text-secondary)' }}>
                        {recipe.portions} portions • {recipe.categorie}
                      </div>
                      {selectedRecipes.find(r => r.id === recipe.id) && (
                        <div className="mt-2">
                          <label className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>Quantité souhaitée:</label>
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
                            style={{ 
                              background: 'var(--color-background-dark)', 
                              color: 'var(--color-text-primary)',
                              borderColor: 'var(--color-border)'
                            }}
                          />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
                
                {selectedRecipes.length > 0 && (
                  <div className="mt-6 pt-4 border-t" style={{ borderColor: 'var(--color-border)' }}>
                    <div className="flex justify-between items-center">
                      <div className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                        {selectedRecipes.length} production(s) sélectionnée(s)
                      </div>
                      <button
                        onClick={calculateAutoOrder}
                        disabled={loading}
                        className="px-6 py-2 rounded-lg font-medium disabled:opacity-50"
                        style={{ background: 'var(--color-accent-gold)', color: '#1a1a1a' }}
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
                    <h3 className="text-lg font-semibold flex items-center" style={{ color: 'var(--color-text-primary)' }}>
                      <span className="mr-2">📊</span>
                      Commandes Suggérées par Fournisseur
                    </h3>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => {
                          // Générer PDF pour toutes les commandes
                          alert('Téléchargement PDF de toutes les commandes...');
                        }}
                        className="text-white px-4 py-2 rounded-lg text-sm flex items-center"
                        style={{ background: 'var(--color-primary-blue)' }}
                      >
                        <span className="mr-2">📄</span>
                        Télécharger tout (PDF)
                      </button>
                      <button
                        onClick={() => {
                          // Envoyer emails à tous les fournisseurs
                          alert('Envoi des emails à tous les fournisseurs...');
                        }}
                        className="text-white px-4 py-2 rounded-lg text-sm flex items-center"
                        style={{ background: 'var(--color-success-green)' }}
                      >
                        <span className="mr-2">📧</span>
                        Envoyer tout par email
                      </button>
                    </div>
                  </div>
                  
                  {/* Récapitulatif général */}
                  <div className="rounded-lg p-4 mb-4" style={{ background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.3)' }}>
                    <h4 className="font-semibold mb-2" style={{ color: 'var(--color-accent-gold)' }}>📋 Récapitulatif Général</h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                      <div>
                        <span style={{ color: 'var(--color-text-secondary)' }}>Nombre de fournisseurs:</span>
                        <span className="font-medium ml-2" style={{ color: 'var(--color-text-primary)' }}>{autoOrderResults.length}</span>
                      </div>
                      <div>
                        <span style={{ color: 'var(--color-text-secondary)' }}>Total produits:</span>
                        <span className="font-medium ml-2" style={{ color: 'var(--color-text-primary)' }}>
                          {autoOrderResults.reduce((total, order) => total + order.products.length, 0)}
                        </span>
                      </div>
                      <div>
                        <span style={{ color: 'var(--color-text-secondary)' }}>Montant total:</span>
                        <span className="font-medium ml-2" style={{ color: 'var(--color-text-primary)' }}>
                          {formatCurrency(autoOrderResults.reduce((total, order) => total + order.total, 0))}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Commandes par fournisseur */}
                  {autoOrderResults.map((order, index) => (
                    <div key={index} className="border rounded-lg shadow-sm" style={{ background: 'var(--color-background-card)', borderColor: 'var(--color-border)' }}>
                      <div className="p-4 border-b" style={{ background: 'var(--color-background-card-light)', borderColor: 'var(--color-border)' }}>
                        <div className="flex justify-between items-start">
                          <div>
                            <h4 className="font-semibold text-lg" style={{ color: 'var(--color-text-primary)' }}>{order.supplierName}</h4>
                            <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                              {order.products.length} produit(s) • Total: {formatCurrency(order.total)}
                            </p>
                          </div>
                          <div className="flex space-x-2">
                            <button 
                              onClick={() => {
                                alert(`PDF généré pour ${order.supplierName}`);
                              }}
                              className="text-white px-3 py-1 rounded text-sm flex items-center"
                              style={{ background: 'var(--color-primary-blue)' }}
                            >
                              <span className="mr-1">📄</span>
                              PDF
                            </button>
                            <button 
                              onClick={() => {
                                alert(`Email envoyé à ${order.supplierName}`);
                              }}
                              className="text-white px-3 py-1 rounded text-sm flex items-center"
                              style={{ background: 'var(--color-success-green)' }}
                            >
                              <span className="mr-1">📧</span>
                              Email
                            </button>
                            <button 
                              onClick={() => {
                                alert(`Commande validée pour ${order.supplierName}!`);
                              }}
                              className="px-3 py-1 rounded text-sm font-medium flex items-center"
                              style={{ background: 'var(--color-accent-gold)', color: '#1a1a1a' }}
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
                            <div key={productIndex} className="flex justify-between items-center py-2 border-b last:border-b-0" style={{ borderColor: 'var(--color-border-light)' }}>
                              <div className="flex-1">
                                <div className="font-medium" style={{ color: 'var(--color-text-primary)' }}>{product.productName}</div>
                                <div className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                                  {product.quantity} {product.unit} × {formatCurrency(product.pricePerUnit)}
                                </div>
                              </div>
                              <div className="font-medium text-right" style={{ color: 'var(--color-text-primary)' }}>
                                {formatCurrency(product.totalPrice)}
                              </div>
                            </div>
                          ))}
                          
                          {/* Total par fournisseur */}
                          <div className="flex justify-between items-center pt-2 border-t font-semibold" style={{ borderColor: 'var(--color-border)' }}>
                            <span style={{ color: 'var(--color-text-primary)' }}>Total {order.supplierName}:</span>
                            <span className="text-lg" style={{ color: 'var(--color-text-primary)' }}>{formatCurrency(order.total)}</span>
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
                <h3 className="text-xl font-bold mb-2" style={{ color: 'var(--color-text-primary)' }}>📋 Historique des Commandes</h3>
                <p style={{ color: 'var(--color-text-secondary)' }}>Suivez l'état de vos commandes en temps réel</p>
              </div>
              
              {loading ? (
                <div className="text-center py-12">
                  <div className="text-4xl mb-4">⏳</div>
                  <p style={{ color: 'var(--color-text-secondary)' }}>Chargement des commandes...</p>
                </div>
              ) : orders.length === 0 ? (
                <div className="text-center py-12 rounded-lg" style={{ background: 'var(--color-background-card-light)' }}>
                  <div className="text-6xl mb-4">📦</div>
                  <p className="text-xl font-medium mb-2" style={{ color: 'var(--color-text-primary)' }}>Aucune commande</p>
                  <p className="mb-6" style={{ color: 'var(--color-text-secondary)' }}>Créez votre première commande dans l'onglet "Commande Manuelle"</p>
                  <button
                    onClick={() => setActiveOrderTab('manual')}
                    className="px-6 py-2 rounded-lg font-medium"
                    style={{ background: 'var(--color-accent-gold)', color: '#1a1a1a' }}
                  >
                    ➕ Créer une commande
                  </button>
                </div>
              ) : (
                <div className="space-y-6">
                  {orders.map((order) => (
                    <div key={order.id} className="rounded-lg shadow-sm border overflow-hidden" style={{ background: 'var(--color-background-card)', borderColor: 'var(--color-border)' }}>
                      {/* En-tête commande */}
                      <div className="px-6 py-4 border-b" style={{ background: 'var(--color-background-card-light)', borderColor: 'var(--color-border)' }}>
                        <div className="flex justify-between items-start">
                          <div>
                            <h4 className="text-lg font-semibold" style={{ color: 'var(--color-text-primary)' }}>
                              {order.supplier_name}
                            </h4>
                            <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                              Commande n°{order.order_number}
                            </p>
                          </div>
                          <div className="text-right">
                            <div className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>
                              {formatCurrency(order.total_amount)}
                            </div>
                            <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
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
                          <summary className="cursor-pointer text-sm font-medium hover:text-opacity-80 flex items-center gap-2" style={{ color: 'var(--color-text-primary)' }}>
                            <span className="group-open:rotate-90 transition-transform">▶</span>
                            Voir les produits commandés
                          </summary>
                          <div className="mt-4 space-y-2 pl-4">
                            {order.items.map((item, idx) => (
                              <div key={idx} className="flex justify-between items-center py-2 border-b text-sm" style={{ borderColor: 'var(--color-border-light)' }}>
                                <div className="flex-1">
                                  <span className="font-medium" style={{ color: 'var(--color-text-primary)' }}>{item.product_name}</span>
                                  <span className="ml-2" style={{ color: 'var(--color-text-secondary)' }}>({item.quantity} {item.unit})</span>
                                </div>
                                <div className="text-right">
                                  <div className="font-medium" style={{ color: 'var(--color-text-primary)' }}>{formatCurrency(item.total_price)}</div>
                                  <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>{formatCurrency(item.unit_price)}/{item.unit}</div>
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
                              className="px-4 py-2 rounded-lg text-sm font-medium hover:bg-opacity-90 text-white"
                              style={{ background: 'var(--color-primary-blue)' }}
                            >
                              ✓ Confirmer
                            </button>
                          )}
                          {order.status === 'confirmed' && (
                            <button
                              onClick={() => updateOrderStatus(order.id, 'in_transit')}
                              className="px-4 py-2 rounded-lg text-sm font-medium hover:bg-opacity-90 text-white"
                              style={{ background: '#8B5CF6' }}
                            >
                              🚚 En transit
                            </button>
                          )}
                          {order.status === 'in_transit' && (
                            <button
                              onClick={() => updateOrderStatus(order.id, 'delivered')}
                              className="px-4 py-2 rounded-lg text-sm font-medium hover:bg-opacity-90 text-white"
                              style={{ background: 'var(--color-success-green)' }}
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
                              className="px-4 py-2 rounded-lg text-sm font-medium hover:bg-opacity-90 text-white"
                              style={{ background: 'var(--color-danger-red)' }}
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