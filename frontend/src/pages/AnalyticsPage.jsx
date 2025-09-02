import React, { useEffect, useState } from 'react';

const AnalyticsPage = () => {
  const [profitabilityData, setProfitabilityData] = useState([]);
  const [salesPerformance, setSalesPerformance] = useState(null);
  const [alertCenter, setAlertCenter] = useState(null);
  const [costAnalysis, setCostAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    fetchAnalyticsData();
  }, []);

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      
      const [profitResponse, salesResponse, alertsResponse, costResponse] = await Promise.all([
        fetch(`${backendUrl}/api/analytics/profitability`),
        fetch(`${backendUrl}/api/analytics/sales-performance`),
        fetch(`${backendUrl}/api/analytics/alerts`),
        fetch(`${backendUrl}/api/analytics/cost-analysis`)
      ]);

      const [profit, sales, alerts, costs] = await Promise.all([
        profitResponse.json(),
        salesResponse.json(),
        alertsResponse.json(),
        costResponse.json()
      ]);

      setProfitabilityData(profit);
      setSalesPerformance(sales);
      setAlertCenter(alerts);
      setCostAnalysis(costs);
    } catch (error) {
      console.error('Erreur lors du chargement des analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleResolveAlert = async (alertType, alertId) => {
    try {
      if (alertType === 'price_anomaly') {
        const response = await fetch(`${backendUrl}/api/price-anomalies/${alertId}/resolve`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ resolution_note: 'Résolu depuis le dashboard' })
        });
        if (response.ok) {
          // Refresh alerts data
          fetchAnalyticsData();
          alert('Alerte résolue avec succès');
        }
      } else if (alertType === 'low_stock') {
        alert('Pour résoudre cette alerte, ajustez le stock depuis le module de Gestion de Stocks');
      } else if (alertType === 'expiring') {
        alert('Pour cette alerte, vérifiez le produit dans le module Gestion de Stocks > Lots');
      }
    } catch (error) {
      console.error('Erreur lors de la résolution de l\'alerte:', error);
      alert('Erreur lors de la résolution de l\'alerte');
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR'
    }).format(amount);
  };

  const formatPercentage = (value) => {
    return `${value.toFixed(1)}%`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-500"></div>
          <p className="mt-4 text-gray-600">Chargement des analytics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-gradient-to-br from-gray-100 to-gray-200 min-h-screen">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">
          📊 Analytics & Profitabilité
        </h1>
        <p className="text-gray-600">Tableau de bord complet pour la gestion et l'analyse des performances</p>
      </div>

      {/* Alert Summary Banner - CLIQUABLE */}
      {alertCenter && alertCenter.total_alerts > 0 && (
        <div 
          className="mb-6 bg-gradient-to-r from-red-50 to-orange-50 border-l-4 border-red-400 p-4 rounded-lg shadow-sm cursor-pointer hover:shadow-md transition-all"
          onClick={() => setActiveTab('alerts')}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="text-red-400 text-2xl mr-3">⚠️</div>
              <div>
                <h3 className="text-lg font-semibold text-red-800">
                  {alertCenter.total_alerts} Alerte{alertCenter.total_alerts > 1 ? 's' : ''} Nécessitant Attention
                </h3>
                <p className="text-red-600">
                  {alertCenter.expiring_products.length} produits expirant, {alertCenter.low_stock_items.length} stocks faibles, {alertCenter.price_anomalies.length} anomalies prix
                </p>
              </div>
            </div>
            <div className="text-blue-600 font-medium">
              Cliquez pour voir les détails →
            </div>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="mb-6">
        <div className="flex space-x-1 bg-white p-1 rounded-lg shadow-sm">
          {[
            { id: 'overview', label: 'Vue d\'ensemble', icon: '📊' },
            { id: 'profitability', label: 'Profitabilité', icon: '💰' },
            { id: 'sales', label: 'Ventes', icon: '📈' },
            { id: 'alerts', label: 'Alertes', icon: '⚠️' },
            { id: 'costs', label: 'Coûts', icon: '💸' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-all ${
                activeTab === tab.id
                  ? 'bg-primary-500 text-white shadow-sm'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* KPI Cards */}
          <div className="bg-white p-6 rounded-lg shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">CA Total</p>
                <p className="text-2xl font-bold text-green-600">
                  {salesPerformance ? formatCurrency(salesPerformance.total_sales) : '€0'}
                </p>
              </div>
              <div className="text-3xl text-green-500">💰</div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Commandes Totales</p>
                <p className="text-2xl font-bold text-blue-600">
                  {salesPerformance ? salesPerformance.total_orders : 0}
                </p>
              </div>
              <div className="text-3xl text-blue-500">📋</div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Panier Moyen</p>
                <p className="text-2xl font-bold text-purple-600">
                  {salesPerformance ? formatCurrency(salesPerformance.average_order_value) : '€0'}
                </p>
              </div>
              <div className="text-3xl text-purple-500">🛒</div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Valeur Stock</p>
                <p className="text-2xl font-bold text-orange-600">
                  {costAnalysis ? formatCurrency(costAnalysis.total_inventory_value) : '€0'}
                </p>
              </div>
              <div className="text-3xl text-orange-500">📦</div>
            </div>
          </div>

          {/* Top Recipes */}
          <div className="md:col-span-2 bg-white p-6 rounded-lg shadow-sm">
            <h3 className="text-lg font-semibold mb-4">🏆 Top 5 Recettes par CA</h3>
            <div className="space-y-3">
              {salesPerformance?.top_recipes?.slice(0, 5).map((recipe, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center">
                    <span className="text-lg mr-3">{index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : '🏅'}</span>
                    <div>
                      <p className="font-medium">{recipe.name}</p>
                      <p className="text-sm text-gray-600">{recipe.quantity} portions vendues</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-green-600">{formatCurrency(recipe.revenue)}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Sales by Category */}
          <div className="md:col-span-2 bg-white p-6 rounded-lg shadow-sm">
            <h3 className="text-lg font-semibold mb-4">🍽️ Ventes par Catégorie</h3>
            <div className="space-y-3">
              {salesPerformance?.sales_by_category && Object.entries(salesPerformance.sales_by_category).map(([category, amount]) => (
                <div key={category} className="flex items-center justify-between">
                  <div className="flex items-center">
                    <span className="text-lg mr-3">
                      {category === 'Bar' ? '🍷' : category === 'Entrées' ? '🥗' : category === 'Plats' ? '🍽️' : '🍰'}
                    </span>
                    <span className="font-medium">{category}</span>
                  </div>
                  <span className="font-semibold text-gray-800">{formatCurrency(amount)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'profitability' && (
        <div className="bg-white rounded-lg shadow-sm">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold">💰 Analyse de Profitabilité par Recette</h3>
            <p className="text-sm text-gray-600 mt-1">Marge bénéficiaire et rentabilité de chaque recette</p>
          </div>
          <div className="p-6">
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Recette</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Prix Vente</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Coût Ingrédients</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Marge</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">% Marge</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Portions Vendues</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Profit Total</th>
                  </tr>
                </thead>
                <tbody>
                  {profitabilityData.slice(0, 10).map((recipe, index) => (
                    <tr key={recipe.recipe_id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4 font-medium">{recipe.recipe_name}</td>
                      <td className="py-3 px-4">{formatCurrency(recipe.selling_price || 0)}</td>
                      <td className="py-3 px-4">{formatCurrency(recipe.ingredient_cost)}</td>
                      <td className="py-3 px-4">
                        <span className={recipe.profit_margin >= 0 ? 'text-green-600' : 'text-red-600'}>
                          {formatCurrency(recipe.profit_margin)}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          recipe.profit_percentage >= 50 ? 'bg-green-100 text-green-800' :
                          recipe.profit_percentage >= 25 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {formatPercentage(recipe.profit_percentage)}
                        </span>
                      </td>
                      <td className="py-3 px-4">{recipe.portions_sold}</td>
                      <td className="py-3 px-4 font-semibold">
                        <span className={recipe.total_profit >= 0 ? 'text-green-600' : 'text-red-600'}>
                          {formatCurrency(recipe.total_profit)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'alerts' && alertCenter && (
        <div className="space-y-6">
          {/* Expiring Products */}
          {alertCenter.expiring_products.length > 0 && (
            <div className="bg-white rounded-lg shadow-sm">
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-red-600">⏰ Produits Expirant Bientôt</h3>
                <p className="text-sm text-gray-600 mt-1">{alertCenter.expiring_products.length} produit(s) expire(nt) dans les 7 prochains jours</p>
              </div>
              <div className="p-6">
                <div className="space-y-3">
                  {alertCenter.expiring_products.map((product, index) => (
                    <div key={index} className={`p-4 rounded-lg border-l-4 ${
                      product.urgency === 'critical' ? 'bg-red-50 border-red-400' : 'bg-yellow-50 border-yellow-400'
                    }`}>
                      <div className="flex justify-between items-center">
                        <div className="flex-1">
                          <p className="font-medium">{product.product_name}</p>
                          <p className="text-sm text-gray-600">
                            Quantité: {product.quantity} • Expire dans {product.days_to_expiry} jour(s)
                          </p>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                            product.urgency === 'critical' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {product.urgency === 'critical' ? 'CRITIQUE' : 'ATTENTION'}
                          </span>
                          <button
                            onClick={() => handleResolveAlert('expiring', product.batch_id)}
                            className="px-3 py-1 bg-blue-500 text-white rounded text-xs hover:bg-blue-600"
                          >
                            Vérifier
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Low Stock Items */}
          {alertCenter.low_stock_items.length > 0 && (
            <div className="bg-white rounded-lg shadow-sm">
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-orange-600">📉 Stocks Faibles</h3>
                <p className="text-sm text-gray-600 mt-1">{alertCenter.low_stock_items.length} produit(s) sous le seuil minimum</p>
              </div>
              <div className="p-6">
                <div className="space-y-3">
                  {alertCenter.low_stock_items.map((item, index) => (
                    <div key={index} className="p-4 bg-orange-50 border-l-4 border-orange-400 rounded-lg">
                      <div className="flex justify-between items-center">
                        <div>
                          <p className="font-medium">{item.product_name}</p>
                          <p className="text-sm text-gray-600">
                            Stock actuel: {item.current_quantity} • Minimum: {item.minimum_quantity}
                          </p>
                        </div>
                        <span className="px-3 py-1 bg-orange-100 text-orange-800 rounded-full text-xs font-medium">
                          Manque {item.shortage.toFixed(1)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Price Anomalies */}
          {alertCenter.price_anomalies.length > 0 && (
            <div className="bg-white rounded-lg shadow-sm">
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-purple-600">💲 Anomalies de Prix</h3>
                <p className="text-sm text-gray-600 mt-1">{alertCenter.price_anomalies.length} écart(s) de prix détecté(s)</p>
              </div>
              <div className="p-6">
                <div className="space-y-3">
                  {alertCenter.price_anomalies.map((anomaly, index) => (
                    <div key={index} className="p-4 bg-purple-50 border-l-4 border-purple-400 rounded-lg">
                      <div className="flex justify-between items-center">
                        <div>
                          <p className="font-medium">{anomaly.product_name}</p>
                          <p className="text-sm text-gray-600">
                            Fournisseur: {anomaly.supplier_name} • Prix référence: {formatCurrency(anomaly.reference_price)}
                          </p>
                          <p className="text-sm text-red-600">
                            Prix facturé: {formatCurrency(anomaly.actual_price)}
                          </p>
                        </div>
                        <span className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-xs font-medium">
                          +{formatPercentage(anomaly.difference_percentage)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'costs' && costAnalysis && (
        <div className="space-y-6">
          {/* Cost Overview */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Valeur Totale Stock</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {formatCurrency(costAnalysis.total_inventory_value)}
                  </p>
                </div>
                <div className="text-3xl text-blue-500">📦</div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Coût Moyen par Recette</p>
                  <p className="text-2xl font-bold text-green-600">
                    {formatCurrency(costAnalysis.avg_cost_per_recipe)}
                  </p>
                </div>
                <div className="text-3xl text-green-500">🍽️</div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Gaspillage Estimé</p>
                  <p className="text-2xl font-bold text-red-600">
                    {formatCurrency(costAnalysis.waste_analysis.estimated_waste_value)}
                  </p>
                  <p className="text-xs text-gray-500">
                    ({formatPercentage(costAnalysis.waste_analysis.estimated_waste_percentage)})
                  </p>
                </div>
                <div className="text-3xl text-red-500">🗑️</div>
              </div>
            </div>
          </div>

          {/* Most Expensive Ingredients */}
          <div className="bg-white rounded-lg shadow-sm">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold">💎 Ingrédients les Plus Coûteux</h3>
              <p className="text-sm text-gray-600 mt-1">Top 10 des ingrédients par prix unitaire</p>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {costAnalysis.most_expensive_ingredients.slice(0, 10).map((ingredient, index) => (
                  <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center">
                      <span className="text-lg mr-3">
                        {index < 3 ? '💰' : '💸'}
                      </span>
                      <div>
                        <p className="font-medium">{ingredient.name}</p>
                        <p className="text-sm text-gray-600">{ingredient.category}</p>
                      </div>
                    </div>
                    <span className="font-semibold text-red-600">{formatCurrency(ingredient.unit_price)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Cost Trends */}
          <div className="bg-white rounded-lg shadow-sm">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold">📈 Tendances des Coûts</h3>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium mb-3">Évolution des Prix</h4>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span>Ce mois</span>
                      <span className="text-green-600">+{formatPercentage(costAnalysis.cost_trends.monthly_change)}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Ce trimestre</span>
                      <span className="text-orange-600">+{formatPercentage(costAnalysis.cost_trends.quarterly_change)}</span>
                    </div>
                  </div>
                </div>
                <div>
                  <h4 className="font-medium mb-3">Catégories de Coût</h4>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span>Plus coûteuse</span>
                      <span className="font-medium">{costAnalysis.cost_trends.highest_cost_category}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Moins coûteuse</span>
                      <span className="font-medium">{costAnalysis.cost_trends.lowest_cost_category}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Refresh Button */}
      <div className="mt-8 text-center">
        <button
          onClick={fetchAnalyticsData}
          className="bg-primary-500 hover:bg-primary-600 text-white px-6 py-2 rounded-lg font-medium transition-colors"
        >
          🔄 Actualiser les Données
        </button>
      </div>
    </div>
  );
};

export default AnalyticsPage;