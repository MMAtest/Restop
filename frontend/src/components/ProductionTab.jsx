import React from "react";
import "../App.css";
import axios from "axios";
import { Pie } from 'react-chartjs-2';
import DataGridsPage from "../pages/DataGridsPage";
import { getCategoryColor, getCategoryIcon } from "../utils/categoryHelpers";

// Constantes locales (dupliquées pour éviter les problèmes d'export/import)
const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const getProductionCategoryIcon = (category) => {
  const icons = {
    'Entrée': '🥗',
    'Plat': '🍽️',
    'Dessert': '🍰',
    'Bar': '🍹',
    'Autres': '📝'
  };
  return icons[category] || '🍽️';
};

const ProductionTab = (props) => {
  // Search states
  const [productSearch, setProductSearch] = React.useState("");
  const [supplierSearch, setSupplierSearch] = React.useState("");
  const [preparationSearch, setPreparationSearch] = React.useState("");
  const [recipeSearch, setRecipeSearch] = React.useState("");

  // Placeholder for props destructuring
  const NOW = Date.now();
  const { activeTab, activeProductionTab, setActiveProductionTab, preparations, currentUser, fetchArchives, setShowProduitModal, showCategoriesView, setShowCategoriesView, fetchProduitsParCategories, setProduitsParCategories, categoriesExpanded, setCategoriesExpanded, canEditItems, handleEdit, canArchiveItems, archiveItem, handleDelete, selectedCategoryFilter, filteredProduits, filteredRecettes, produits, fournisseurs, produitsParCategories, setShowFournisseurModal, showFournisseursCategoriesView, setShowFournisseursCategoriesView, restoreItem, deleteArchivePermanently, fetchHistoriqueProduction, historiqueProduction, showRecetteModal, setShowRecetteModal, handleExportRecettes, showRecettesCategoriesView, setShowRecettesCategoriesView, filterRecettesByCategory, categoriesProduction, loading, handleCalculerCouts, showPreparationModal, setShowPreparationModal, handleAutoGeneratePreparations, showPreparationsCategoriesView, setShowPreparationsCategoriesView, preparationForm, handlePreparationSubmit, resetPreparationForm, calculatePerte, calculatePortions, formesDecoupe, stocksPreparations, mouvementsPreparations, showMovementPreparationModal, setShowMovementPreparationModal, movementPreparationForm, preparationsParCategories, categoriesPreparationsExpanded, handleMovementPreparation, archivedItems, selectedArchiveType, setSelectedArchiveType, filterProduitsByCategory, canCreateItems, recettes, setEditingItem, setPreparationForm, setMovementPreparationForm, setCategoriesPreparationsExpanded } = props;

  return (
    <>
              <div id="production" className={`wireframe-section ${activeTab === "production" ? "active" : ""}`}>
          <div className="section-card">
            <div className="section-title">Production & Historique</div>
            
            {/* Sous-navigation Production */}
            <div className="sub-nav-tabs">
              <button 
                className="button" 
                onClick={() => setActiveProductionTab('produits')}
                style={{
                  background: activeProductionTab === 'produits' ? 'var(--color-primary-blue)' : 'var(--color-background-card-light)',
                  color: activeProductionTab === 'produits' ? 'white' : 'var(--color-text-secondary)'
                }}
              >
                Produits
              </button>
              <button 
                className="button" 
                onClick={() => setActiveProductionTab('fournisseurs')}
                style={{
                  background: activeProductionTab === 'fournisseurs' ? 'var(--color-primary-blue)' : 'var(--color-background-card-light)',
                  color: activeProductionTab === 'fournisseurs' ? 'white' : 'var(--color-text-secondary)'
                }}
              >
                Fournisseurs
              </button>
              <button 
                className="button" 
                onClick={() => setActiveProductionTab('preparations')}
                style={{
                  background: activeProductionTab === 'preparations' ? 'var(--color-primary-blue)' : 'var(--color-background-card-light)',
                  color: activeProductionTab === 'preparations' ? 'white' : 'var(--color-text-secondary)'
                }}
              >
                Préparations ({preparations.length})
              </button>
              <button 
                className="button" 
                onClick={() => setActiveProductionTab('recettes')}
                style={{
                  background: activeProductionTab === 'recettes' ? 'var(--color-primary-blue)' : 'var(--color-background-card-light)',
                  color: activeProductionTab === 'recettes' ? 'white' : 'var(--color-text-secondary)'
                }}
              >
                Productions
              </button>
              {/* Onglets réservés au super admin */}
              {currentUser?.role === 'super_admin' && (
                <>
                  <button 
                    className="button" 
                    onClick={() => setActiveProductionTab('datagrids')}
                    style={{
                      background: activeProductionTab === 'datagrids' ? 'var(--color-primary-blue)' : 'var(--color-background-card-light)',
                      color: activeProductionTab === 'datagrids' ? 'white' : 'var(--color-text-secondary)'
                    }}
                  >
                    Grilles de données
                  </button>
                  <button 
                    className="button" 
                    onClick={() => setActiveProductionTab('historique')}
                    style={{
                      background: activeProductionTab === 'historique' ? 'var(--color-primary-blue)' : 'var(--color-background-card-light)',
                      color: activeProductionTab === 'historique' ? 'white' : 'var(--color-text-secondary)'
                    }}
                  >
                    Historique
                  </button>
                </>
              )}
              <button 
                className="button" 
                onClick={() => {
                  setActiveProductionTab('archives');
                  fetchArchives();
                }}
                style={{
                  background: activeProductionTab === 'archives' ? 'var(--color-primary-blue)' : 'var(--color-background-card-light)',
                  color: activeProductionTab === 'archives' ? 'white' : 'var(--color-text-secondary)'
                }}
              >
                Archives
              </button>
            </div>

            {/* ONGLET PRODUITS */}
            {activeProductionTab === 'produits' && (
              <div className="item-list">
                <div className="section-title">Gestion des Produits (Ingrédients)</div>
                
                <div style={{display: 'flex', gap: '10px', marginBottom: '20px', flexWrap: 'wrap'}}>
                  <button className="button" onClick={() => setShowProduitModal(true)}>Nouveau Produit</button>
                  <button 
                    className={`button ${showCategoriesView ? 'secondary' : ''}`}
                    onClick={async () => {
                      if (!showCategoriesView) {
                        // Charger les données par catégories
                        const data = await fetchProduitsParCategories();
                        setProduitsParCategories(data);
                        // Ouvrir toutes les catégories par défaut
                        const expanded = {};
                        Object.keys(data.categories).forEach(cat => {
                          expanded[cat] = true;
                        });
                        setCategoriesExpanded(expanded);
                      }
                      setShowCategoriesView(!showCategoriesView);
                    }}
                    style={{backgroundColor: showCategoriesView ? '#6366f1' : '', color: showCategoriesView ? 'white' : ''}}
                  >
                    {showCategoriesView ? 'Vue Liste' : 'Vue Catégories'}
                  </button>
                </div>

                {/* Filtre par catégorie - Section Produits */}
                {!showCategoriesView && (
                  <div className="filter-section" style={{marginBottom: '20px'}}>
                    {/* Barre de recherche Produits */}
                    <div style={{marginBottom: '10px'}}>
                      <input
                        type="text"
                        placeholder="Rechercher un produit..."
                        value={productSearch}
                        onChange={(e) => setProductSearch(e.target.value)}
                        className="form-input"
                        style={{width: '100%'}}
                      />
                    </div>
                    <div className="filter-group">
                      <label className="filter-label">Filtrer par catégorie d'ingrédients :</label>
                      <select 
                        className="filter-select"
                        onChange={(e) => filterProduitsByCategory(e.target.value)}
                        style={{
                          padding: '8px 12px',
                          borderRadius: '6px',
                          border: '1px solid var(--color-border)',
                          background: 'var(--color-background-card)',
                          color: 'var(--color-text-primary)',
                          minWidth: '150px'
                        }}
                      >
                        <option value="">Tous les ingrédients</option>
                        <option value="Légumes">Légumes</option>
                        <option value="Viandes">Viandes</option>
                        <option value="Poissons">Poissons</option>
                        <option value="Crêmerie">Crêmerie</option>
                        <option value="Épices">Épices & Condiments</option>
                        <option value="Fruits">Fruits</option>
                        <option value="Épicerie">Épicerie</option>
                        <option value="Céréales">Céréales & Féculents</option>
                        <option value="Boissons">Boissons</option>
                        <option value="Autres">Autres</option>
                      </select>
                      
                      <div className="filter-info" style={{
                        fontSize: '14px', 
                        color: 'var(--color-text-secondary)',
                        marginLeft: '10px'
                      }}>
                        {filteredProduits.length} produit(s) affiché(s)
                      </div>
                    </div>
                  </div>
                )}

                {/* Vue accordéon par catégories */}
                {showCategoriesView ? (
                  <div style={{display: 'grid', gap: '16px'}}>
                    <div style={{
                      padding: '16px', 
                      background: 'var(--color-background-secondary)',
                      borderRadius: '8px',
                      border: '1px solid var(--color-border)',
                      marginBottom: '16px'
                    }}>
                      <div style={{fontSize: '16px', fontWeight: 'bold', marginBottom: '8px'}}>
                        Résumé par catégories
                      </div>
                      <div style={{fontSize: '14px', color: 'var(--color-text-secondary)'}}>
                        {produitsParCategories.total_categories} catégories • {produitsParCategories.total_products} produits total
                      </div>
                    </div>

                    {Object.entries(produitsParCategories.categories).map(([categoryName, categoryData]) => (
                      <div key={categoryName} style={{
                        border: '1px solid var(--color-border)',
                        borderRadius: '8px',
                        overflow: 'hidden'
                      }}>
                        {/* En-tête de catégorie cliquable */}
                        <div 
                          style={{
                            padding: '16px',
                            background: categoriesExpanded[categoryName] ? '#4CAF50' : 'var(--color-background-secondary)',
                            color: categoriesExpanded[categoryName] ? 'white' : 'var(--color-text-primary)',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            fontWeight: 'bold',
                            borderBottom: categoriesExpanded[categoryName] ? '1px solid var(--color-border)' : 'none'
                          }}
                          onClick={() => {
                            setCategoriesExpanded(prev => ({
                              ...prev,
                              [categoryName]: !prev[categoryName]
                            }));
                          }}
                        >
                          <div style={{display: 'flex', alignItems: 'center', gap: '12px'}}>
                            <span style={{fontSize: '20px'}}>{categoryData.icon}</span>
                            <span>{categoryName}</span>
                            <span style={{
                              fontSize: '12px',
                              padding: '4px 8px',
                              borderRadius: '12px',
                              background: categoriesExpanded[categoryName] ? 'rgba(255,255,255,0.2)' : 'var(--color-accent-orange)',
                              color: 'white'
                            }}>
                              {categoryData.total_products}
                            </span>
                          </div>
                          <span style={{fontSize: '18px'}}>
                            {categoriesExpanded[categoryName] ? '▼' : '▶'}
                          </span>
                        </div>

                        {/* Contenu de la catégorie */}
                        {categoriesExpanded[categoryName] && (
                          <div style={{padding: '0'}}>
                            {categoryData.products.map((produit, index) => (
                              <div key={produit.id} style={{
                                padding: '12px 16px',
                                borderBottom: index < categoryData.products.length - 1 ? '1px solid var(--color-border)' : 'none',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'space-between',
                                background: index % 2 === 0 ? 'transparent' : 'var(--color-background-secondary)'
                              }}>
                                <div style={{display: 'flex', alignItems: 'center', gap: '12px'}}>
                                  <div style={{
                                    fontSize: '16px',
                                    fontWeight: 'bold',
                                    color: 'var(--color-text-primary)'
                                  }}>
                                    {produit.nom}
                                  </div>
                                  {produit.prix_achat && (
                                    <div style={{
                                      fontSize: '14px',
                                      color: 'var(--color-text-secondary)',
                                      padding: '2px 6px',
                                      background: 'var(--color-background-tertiary)',
                                      borderRadius: '4px'
                                    }}>
                                      {produit.prix_achat}€/{produit.unite}
                                    </div>
                                  )}
                                  {produit.fournisseur_nom && (
                                    <div style={{
                                      fontSize: '12px',
                                      color: 'var(--color-accent-green)',
                                      fontStyle: 'italic'
                                    }}>
                                      {produit.fournisseur_nom}
                                    </div>
                                  )}
                                </div>
                                
                                <div style={{display: 'flex', gap: '6px'}}>
                                  {/* Éditer produit accordéon - MASQUÉ pour employé cuisine */}
                                  {canEditItems() && (
                                    <button 
                                      className="button small"
                                      onClick={() => handleEdit(produit, 'produit')}
                                      style={{fontSize: '12px', padding: '4px 8px'}}
                                    >
                                      ✏️
                                    </button>
                                  )}
                                  
                                  {/* Archiver produit accordéon - MASQUÉ pour employé cuisine */}
                                  {canArchiveItems() && (
                                    <button 
                                      className="button small warning"
                                    onClick={async () => {
                                      const reason = window.prompt(`Raison de l'archivage de "${produit.nom}" (optionnel):`);
                                      if (reason !== null) {
                                        const success = await archiveItem(produit.id, 'produit', reason || null);
                                        if (success) {
                                          alert(`${produit.nom} archivé avec succès !`);
                                          // Recharger les données des catégories
                                          const data = await fetchProduitsParCategories();
                                          setProduitsParCategories(data);
                                        } else {
                                          alert("Erreur lors de l'archivage");
                                        }
                                      }
                                    }}
                                    style={{fontSize: '12px', padding: '4px 8px'}}
                                  >
                                    🗃️
                                  </button>
                                  )}
                                  
                                  {/* Supprimer produit - MASQUÉ pour employé cuisine */}
                                  {canEditItems() && (
                                    <button 
                                      className="button small danger"
                                      onClick={() => handleDelete(produit.id, 'produit')}
                                      style={{fontSize: '12px', padding: '4px 8px'}}
                                    >
                                      🗑️
                                    </button>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <>
                {/* Liste des produits filtrés */}
                {selectedCategoryFilter && filteredProduits.length === 0 && (
                  <div className="empty-state-message" style={{padding: '20px', textAlign: 'center', color: 'var(--color-text-secondary)'}}>
                    Aucun produit dans cette catégorie.
                  </div>
                )}
                {filteredProduits.filter(p => p.nom.toLowerCase().includes(productSearch.toLowerCase())).map((produit, index) => {
                    // Fonction pour obtenir l'icône selon la catégorie
                    const getCategoryIcon = (categorie) => {
                    if (!categorie) return '⚠️'; // Icône d'alerte si pas de catégorie
                    
                    switch(categorie) {
                      case 'Légumes': return '🥕';
                      case 'Viandes': return '🥩';
                      case 'Poissons': return '🐟';
                      case 'Crêmerie': return '🧀';
                      case 'Épices': return '🌶️';
                      case 'Fruits': return '🍎';
                      case 'Céréales': return '🌾';
                      case 'Boissons': return '🥤';
                      case 'Autres': return '📦';
                      default: return '⚠️'; // Icône d'alerte pour catégorie non reconnue
                    }
                  };

                  return (
                    <div key={index} className="item-row">
                      <div className="item-info">
                        <div className="item-name">
                          {getCategoryIcon(produit.categorie)} {produit.nom}
                          {produit.categorie ? (
                            <span className="category-badge" style={{
                              marginLeft: '8px',
                              padding: '4px 8px',
                              borderRadius: '12px',
                              fontSize: '12px',
                              background: 'var(--color-accent-orange)',
                              color: 'white'
                            }}>
                              {produit.categorie}
                            </span>
                          ) : (
                            <span className="category-badge" style={{
                              marginLeft: '8px',
                              padding: '4px 8px',
                              borderRadius: '12px',
                              fontSize: '12px',
                              background: 'var(--color-warning-orange)',
                              color: 'white'
                            }}>
                              Sans catégorie
                            </span>
                          )}
                        </div>
                        <div className="item-details">
                          {produit.description} • Prix: {produit.prix_achat || produit.reference_price || 'N/A'}€
                        </div>
                      </div>
                      <div className="item-actions">
                        {/* Éditer produit - MASQUÉ pour employé cuisine */}
                        {canEditItems() && (
                          <button className="button small" onClick={() => handleEdit(produit, 'produit')}>Éditer</button>
                        )}
                        
                        {/* Archiver produit - MASQUÉ pour employé cuisine */}
                        {canArchiveItems() && (
                          <button 
                            className="button small warning" 
                            onClick={async () => {
                              const reason = window.prompt(`Raison de l'archivage de "${produit.nom}" (optionnel):`);
                              if (reason !== null) {
                                const success = await archiveItem(produit.id, 'produit', reason || null);
                                if (success) {
                                  alert(`${produit.nom} archivé avec succès !`);
                                } else {
                                  alert("Erreur lors de l'archivage");
                                }
                              }
                            }}
                          >
                            Archiver
                          </button>
                        )}
                      </div>
                    </div>
                  )
                })}
                </>
                )}
              </div>
            )}

            {/* ONGLET FOURNISSEURS */}
            {activeProductionTab === 'fournisseurs' && (
              <div className="item-list">
                <div className="section-title">Gestion des Fournisseurs</div>
                
                <div style={{display: 'flex', gap: '10px', marginBottom: '20px', flexWrap: 'wrap'}}>
                  <button className="button" onClick={() => setShowFournisseurModal(true)}>Nouveau Fournisseur</button>
                  <button className="button">Évaluation</button>
                  <button 
                    className={`button ${showFournisseursCategoriesView ? 'secondary' : ''}`}
                    onClick={() => setShowFournisseursCategoriesView(!showFournisseursCategoriesView)}
                    style={{backgroundColor: showFournisseursCategoriesView ? '#6366f1' : '', color: showFournisseursCategoriesView ? 'white' : ''}}
                  >
                    {showFournisseursCategoriesView ? 'Vue Liste' : 'Vue Catégories'}
                  </button>
                </div>

                {/* Vue par catégorie ou liste des fournisseurs */}
                {showFournisseursCategoriesView ? (
                  <div style={{display: 'grid', gap: '16px'}}>
                    {(() => {
                      // Grouper les fournisseurs par catégorie
                      const fournisseursByCategorie = fournisseurs.reduce((acc, f) => {
                        const categorie = f.categorie || 'Autres';
                        if (!acc[categorie]) acc[categorie] = [];
                        acc[categorie].push(f);
                        return acc;
                      }, {});
                      
                      const getIcon = (cat) => {
                        switch(cat.toLowerCase()) {
                          case 'frais': return '🥩';
                          case 'epicerie': return '🛒';
                          case 'boissons': return '🍷';
                          case 'légumes': return '🥬';
                          default: return '🏪';
                        }
                      };
                      
                      return Object.entries(fournisseursByCategorie).map(([categorie, fourns]) => (
                        <div key={categorie} style={{border: '1px solid var(--color-border)', borderRadius: '8px', overflow: 'hidden'}}>
                          <div style={{padding: '16px', background: '#4CAF50', color: 'white', fontWeight: 'bold'}}>
                            <div style={{display: 'flex', alignItems: 'center', gap: '12px'}}>
                              <span style={{fontSize: '20px'}}>{getIcon(categorie)}</span>
                              <span>{categorie} ({fourns.length})</span>
                            </div>
                          </div>
                          <div style={{padding: '16px', display: 'grid', gap: '12px'}}>
                            {fourns.map((fournisseur) => (
                              <div key={fournisseur.id} style={{padding: '12px', background: 'var(--color-background-secondary)', borderRadius: '8px', border: '1px solid var(--color-border)'}}>
                                <div style={{display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px'}}>
                                  <span style={{fontSize: '18px'}}>{fournisseur.logo || '🏪'}</span>
                                  <span style={{backgroundColor: fournisseur.couleur || '#3B82F6', color: 'white', padding: '4px 8px', borderRadius: '4px', fontWeight: '500', fontSize: '14px'}}>
                                    {fournisseur.nom}
                                  </span>
                                </div>
                                <div style={{fontSize: '13px', color: 'var(--color-text-secondary)'}}>
                                  {fournisseur.email} • {fournisseur.telephone}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ));
                    })()}
                  </div>
                ) : (
                  <>
                  {/* Barre de recherche Fournisseurs */}
                  <div style={{marginBottom: '15px'}}>
                    <input
                      type="text"
                      placeholder="Rechercher un fournisseur..."
                      value={supplierSearch}
                      onChange={(e) => setSupplierSearch(e.target.value)}
                      className="form-input"
                      style={{width: '100%'}}
                    />
                  </div>
                {fournisseurs.filter(f => f.nom.toLowerCase().includes(supplierSearch.toLowerCase())).map((fournisseur, index) => (
                  <div key={index} className="item-row">
                    <div className="item-info">
                      <div className="item-name" style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
                        {/* Logo du fournisseur */}
                        <span style={{fontSize: '20px'}}>
                          {fournisseur.logo || '🏪'}
                        </span>
                        {/* Nom avec code couleur */}
                        <span style={{
                          backgroundColor: fournisseur.couleur || '#3B82F6',
                          color: 'white',
                          padding: '4px 8px',
                          borderRadius: '4px',
                          fontWeight: '500',
                          fontSize: '14px'
                        }}>
                          {fournisseur.nom}
                        </span>
                      </div>
                      <div className="item-details">
                        {fournisseur.email} • Tel: {fournisseur.telephone}
                      </div>
                    </div>
                    <div className="item-actions">
                      <button className="button small" onClick={() => handleEdit(fournisseur, 'fournisseur')}>Éditer</button>
                      <button 
                        className="button small warning" 
                        onClick={async () => {
                          const reason = window.prompt(`Raison de l'archivage de "${fournisseur.nom}" (optionnel):`);
                          if (reason !== null) { // null = annulé, empty string = OK sans raison
                            const success = await archiveItem(fournisseur.id, 'fournisseur', reason || null);
                            if (success) {
                              alert(`${fournisseur.nom} archivé avec succès !`);
                            } else {
                              alert("Erreur lors de l'archivage");
                            }
                          }
                        }}
                      >
                        Archiver
                      </button>
                    </div>
                  </div>
                ))}
                </>
                )}
              </div>
            )}

            {/* ONGLET PRÉPARATIONS */}
            {activeProductionTab === 'preparations' && (
              <div className="item-list">
                <div className="section-title">Préparations</div>
                
                <div style={{display: 'flex', gap: '10px', marginBottom: '20px', flexWrap: 'wrap'}}>
                  <button className="button" onClick={() => setShowPreparationModal(true)}>Nouvelle Préparation</button>
                  <button 
                    className="button secondary" 
                    onClick={handleAutoGeneratePreparations}
                    disabled={loading}
                    style={{backgroundColor: '#10b981', color: 'white', border: 'none'}}
                  >
                    🤖 {loading ? 'Génération...' : 'Auto-générer'}
                  </button>
                  <button 
                    className={`button ${showPreparationsCategoriesView ? 'secondary' : ''}`}
                    onClick={() => setShowPreparationsCategoriesView(!showPreparationsCategoriesView)}
                    style={{backgroundColor: showPreparationsCategoriesView ? '#6366f1' : '', color: showPreparationsCategoriesView ? 'white' : ''}}
                  >
                    {showPreparationsCategoriesView ? 'Vue Liste' : 'Vue Catégories'}
                  </button>
                  <div style={{fontSize: '14px', alignSelf: 'center', color: 'var(--color-text-secondary)'}}>
                    L&apos;auto-génération crée 2-3 préparations par produit
                  </div>
                </div>

                {/* Alertes DLC */}
                {preparations.filter(p => p.dlc && new Date(p.dlc) < new Date(NOW + 3 * 24 * 60 * 60 * 1000)).length > 0 && (
                  <div style={{background: '#fef3c7', border: '1px solid #fbbf24', borderRadius: '8px', padding: '12px', marginBottom: '20px'}}>
                    <div style={{fontWeight: 'bold', color: '#92400e', marginBottom: '8px'}}>
                      Alertes DLC - {preparations.filter(p => p.dlc && new Date(p.dlc) < new Date(NOW + 3 * 24 * 60 * 60 * 1000)).length} préparation(s)
                    </div>
                    {preparations.filter(p => p.dlc && new Date(p.dlc) < new Date(NOW + 3 * 24 * 60 * 60 * 1000)).map(prep => (
                      <div key={prep.id} style={{fontSize: '14px', color: '#78350f', marginTop: '4px'}}>
                        • {prep.nom} - DLC: {new Date(prep.dlc).toLocaleDateString('fr-FR')}
                      </div>
                    ))}
                  </div>
                )}

                {/* Liste ou Vue par catégories des préparations */}
                {showPreparationsCategoriesView ? (
                  <div style={{display: 'grid', gap: '16px'}}>
                    {(() => {
                      // Grouper les préparations par forme de découpe
                      const prepsByForme = preparations.reduce((acc, prep) => {
                        const forme = prep.forme_decoupe_custom || prep.forme_decoupe || 'Autre';
                        if (!acc[forme]) acc[forme] = [];
                        acc[forme].push(prep);
                        return acc;
                      }, {});
                      
                      return Object.entries(prepsByForme).map(([forme, preps]) => (
                        <div key={forme} style={{border: '1px solid var(--color-border)', borderRadius: '8px', overflow: 'hidden'}}>
                          <div style={{padding: '16px', background: '#4CAF50', color: 'white', fontWeight: 'bold', cursor: 'pointer'}}>
                            <div style={{display: 'flex', alignItems: 'center', gap: '12px'}}>
                              <span style={{fontSize: '20px'}}>🔪</span>
                              <span>{forme} ({preps.length})</span>
                            </div>
                          </div>
                          <div style={{padding: '16px', display: 'grid', gap: '12px'}}>
                            {preps.map((prep) => {
                              const dlcDate = prep.dlc ? new Date(prep.dlc) : null;
                              const isDlcSoon = dlcDate && dlcDate < new Date(NOW + 3 * 24 * 60 * 60 * 1000);
                              const isDlcExpired = dlcDate && dlcDate < new Date();
                              
                              return (
                                <div key={prep.id} style={{padding: '12px', background: 'var(--color-background-secondary)', borderRadius: '8px', border: isDlcExpired ? '2px solid #dc2626' : isDlcSoon ? '2px solid #f59e0b' : '1px solid var(--color-border)'}}>
                                  <div style={{fontSize: '16px', fontWeight: 'bold', marginBottom: '8px'}}>{prep.nom}</div>
                                  <div style={{fontSize: '13px', color: 'var(--color-text-secondary)'}}>
                                    Produit: {prep.produit_nom} • {prep.quantite_preparee} {prep.unite_preparee}
                                    {dlcDate && <span style={{marginLeft: '8px', color: isDlcExpired ? '#dc2626' : isDlcSoon ? '#f59e0b' : '#10b981'}}>
                                      DLC: {dlcDate.toLocaleDateString('fr-FR')}
                                    </span>}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      ));
                    })()}
                  </div>
                ) : (
                  <div style={{display: 'grid', gap: '12px'}}>
                    {/* Barre de recherche Préparations */}
                    <div style={{marginBottom: '10px'}}>
                      <input
                        type="text"
                        placeholder="Rechercher une préparation..."
                        value={preparationSearch}
                        onChange={(e) => setPreparationSearch(e.target.value)}
                        className="form-input"
                        style={{width: '100%'}}
                      />
                    </div>
                    {preparations.length === 0 ? (
                      <div style={{textAlign: 'center', padding: '40px', color: 'var(--color-text-secondary)'}}>
                        <div style={{fontSize: '48px', marginBottom: '16px'}}>🔪</div>
                        <div style={{fontSize: '18px', fontWeight: 'bold', marginBottom: '8px'}}>Aucune préparation</div>
                        <div>Créez votre première préparation pour commencer</div>
                      </div>
                    ) : (
                    preparations.filter(p => p.nom.toLowerCase().includes(preparationSearch.toLowerCase())).map((prep) => {
                      const dlcDate = prep.dlc ? new Date(prep.dlc) : null;
                      const isDlcSoon = dlcDate && dlcDate < new Date(NOW + 3 * 24 * 60 * 60 * 1000);
                      const isDlcExpired = dlcDate && dlcDate < new Date();
                      
                      return (
                        <div key={prep.id} className="card" style={{padding: '16px', border: isDlcExpired ? '2px solid #dc2626' : isDlcSoon ? '2px solid #f59e0b' : '1px solid var(--color-border)'}}>
                          <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '12px'}}>
                            <div style={{flex: 1}}>
                              <div style={{fontSize: '18px', fontWeight: 'bold', color: 'var(--color-text-primary)', marginBottom: '4px'}}>
                                {prep.nom}
                              </div>
                              <div style={{fontSize: '14px', color: 'var(--color-text-secondary)', marginBottom: '8px'}}>
                                Produit source: {prep.produit_nom}
                              </div>
                              <div style={{display: 'flex', gap: '12px', flexWrap: 'wrap', fontSize: '13px'}}>
                                <div>
                                  <span style={{fontWeight: 'bold'}}>Forme:</span> {prep.forme_decoupe_custom || prep.forme_decoupe}
                                </div>
                                <div>
                                  <span style={{fontWeight: 'bold'}}>Quantité:</span> {prep.quantite_preparee} {prep.unite_preparee}
                                </div>
                                <div>
                                  <span style={{fontWeight: 'bold'}}>Portions:</span> {prep.nombre_portions} × {prep.taille_portion}{prep.unite_portion}
                                </div>
                                <div>
                                  <span style={{fontWeight: 'bold', color: '#dc2626'}}>Perte:</span> {prep.perte} {prep.unite_produit_brut} ({prep.perte_pourcentage}%)
                                </div>
                                {dlcDate && (
                                  <div>
                                    <span style={{fontWeight: 'bold', color: isDlcExpired ? '#dc2626' : isDlcSoon ? '#f59e0b' : '#10b981'}}>
                                      DLC:
                                    </span> {dlcDate.toLocaleDateString('fr-FR')}
                                    {isDlcExpired && <span style={{marginLeft: '4px', color: '#dc2626'}}>Expirée</span>}
                                    {isDlcSoon && !isDlcExpired && <span style={{marginLeft: '4px', color: '#f59e0b'}}>Bientôt</span>}
                                  </div>
                                )}
                              </div>
                            </div>
                            <div style={{display: 'flex', gap: '8px'}}>
                              <button 
                                className="button" 
                                onClick={() => {
                                  setEditingItem(prep);
                                  handleEdit(prep, 'preparation');
                                }}
                                style={{padding: '6px 12px', fontSize: '14px'}}
                              >
                                ✏️
                              </button>
                              <button 
                                className="button" 
                                onClick={() => handleDelete(prep.id, 'preparation')}
                                style={{padding: '6px 12px', fontSize: '14px', background: '#dc2626', color: 'white'}}
                              >
                                🗑️
                              </button>
                            </div>
                          </div>
                        </div>
                      );
                    })
                  )}
                  </div>
                )}
              </div>
            )}

            {/* ONGLET RECETTES */}
            {activeProductionTab === 'recettes' && (
              <div className="item-list">
                <div className="section-title">Productions</div>
                
                <div style={{display: 'flex', gap: '10px', marginBottom: '20px', flexWrap: 'wrap'}}>
                  <button className="button" onClick={() => setShowRecetteModal(true)}>Nouvelle Production</button>
                  <button className="button" onClick={handleExportRecettes}>Export Excel</button>
                  <button 
                    className={`button ${showRecettesCategoriesView ? 'secondary' : ''}`}
                    onClick={() => setShowRecettesCategoriesView(!showRecettesCategoriesView)}
                    style={{backgroundColor: showRecettesCategoriesView ? '#6366f1' : '', color: showRecettesCategoriesView ? 'white' : ''}}
                  >
                    {showRecettesCategoriesView ? 'Vue Liste' : 'Vue Catégories'}
                  </button>
                </div>

                {/* Filtre par catégorie - uniquement en vue liste */}
                {!showRecettesCategoriesView && (
                  <div className="filter-section" style={{marginBottom: '20px'}}>
                    {/* Barre de recherche Recettes */}
                    <div style={{marginBottom: '10px'}}>
                      <input
                        type="text"
                        placeholder="Rechercher une production..."
                        value={recipeSearch}
                        onChange={(e) => setRecipeSearch(e.target.value)}
                        className="form-input"
                        style={{width: '100%'}}
                      />
                    </div>
                    <div className="filter-group">
                      <label className="filter-label">Filtrer par catégorie :</label>
                      <select 
                      className="filter-select"
                      value={selectedCategoryFilter}
                      onChange={(e) => filterRecettesByCategory(e.target.value)}
                      style={{
                        padding: '8px 12px',
                        borderRadius: '6px',
                        border: '1px solid var(--color-border)',
                        background: 'var(--color-background-card)',
                        color: 'var(--color-text-primary)',
                        minWidth: '150px'
                      }}
                    >
                      <option value="">Toutes les catégories</option>
                      {categoriesProduction.map(category => (
                        <option key={category} value={category}>
                          {category === 'Entrée' ? '🥗' : 
                           category === 'Plat' ? '🍽️' : 
                           category === 'Dessert' ? '🍰' :
                           category === 'Bar' ? '🍹' : '📝'} {category}
                        </option>
                      ))}
                    </select>
                    
                    {selectedCategoryFilter && (
                      <div className="filter-info" style={{
                        fontSize: '14px', 
                        color: 'var(--color-text-secondary)',
                        marginLeft: '10px'
                      }}>
                        {filteredRecettes.length} plat(s) trouvé(s)
                      </div>
                    )}
                    </div>
                  </div>
                )}

                {/* Vue par catégorie ou liste des recettes */}
                {showRecettesCategoriesView ? (
                  <div style={{display: 'grid', gap: '16px'}}>
                    {(() => {
                      // Grouper les recettes par catégorie
                      const recettesToDisplay = filteredRecettes.length > 0 || !selectedCategoryFilter ? filteredRecettes : [];
                      
                      if (recettesToDisplay.length === 0 && selectedCategoryFilter) {
                        return (
                          <div style={{
                            padding: '40px',
                            textAlign: 'center',
                            background: 'var(--color-background-card-light)',
                            borderRadius: '8px'
                          }}>
                            <div style={{fontSize: '48px', marginBottom: '16px'}}>🔍</div>
                            <h3 style={{color: 'var(--color-text-primary)', marginBottom: '8px'}}>
                              Aucune recette trouvée
                            </h3>
                            <p style={{color: 'var(--color-text-secondary)', fontSize: '14px'}}>
                              Aucune recette ne correspond à cette catégorie.
                            </p>
                          </div>
                        );
                      }
                      
                      const recettesByCategorie = recettesToDisplay.reduce((acc, recette) => {
                        const categorie = recette.categorie || 'Autres';
                        if (!acc[categorie]) acc[categorie] = [];
                        acc[categorie].push(recette);
                        return acc;
                      }, {});
                      
                      const getIcon = (cat) => {
                        switch(cat) {
                          case 'Entrée': return '🥗';
                          case 'Plat': return '🍽️';
                          case 'Dessert': return '🍰';
                          case 'Bar': return '🍹';
                          default: return '📝';
                        }
                      };
                      
                      return Object.entries(recettesByCategorie).map(([categorie, recs]) => (
                        <div key={categorie} style={{border: '1px solid var(--color-border)', borderRadius: '8px', overflow: 'hidden'}}>
                          <div style={{padding: '16px', background: '#4CAF50', color: 'white', fontWeight: 'bold'}}>
                            <div style={{display: 'flex', alignItems: 'center', gap: '12px'}}>
                              <span style={{fontSize: '20px'}}>{getIcon(categorie)}</span>
                              <span>{categorie} ({recs.length})</span>
                            </div>
                          </div>
                          <div style={{padding: '16px', display: 'grid', gap: '12px'}}>
                            {recs.map((recette) => (
                              <div key={recette.id} style={{padding: '12px', background: 'var(--color-background-secondary)', borderRadius: '8px', border: '1px solid var(--color-border)'}}>
                                <div style={{fontSize: '16px', fontWeight: 'bold', marginBottom: '8px'}}>{recette.nom}</div>
                                <div style={{fontSize: '13px', color: 'var(--color-text-secondary)'}}>
                                  {recette.portions} portions • {recette.ingredients?.length || 0} ingrédient(s)
                                  {recette.prix_vente && <span style={{marginLeft: '8px', color: '#10b981', fontWeight: 'bold'}}>{recette.prix_vente.toFixed(2)}€</span>}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ));
                    })()}
                  </div>
                ) : (
                  <>
                {/* Liste des recettes filtrées */}
                {selectedCategoryFilter && filteredRecettes.length === 0 && (
                  <div className="empty-state-message" style={{padding: '20px', textAlign: 'center', color: 'var(--color-text-secondary)'}}>
                    Aucune recette dans cette catégorie.
                  </div>
                )}
                {filteredRecettes.filter(r => r.nom.toLowerCase().includes(recipeSearch.toLowerCase())).map((recette, index) => {
                  // Fonction pour obtenir l'icône selon la catégorie de production
                  const getProductionCategoryIcon = (categorie) => {
                    if (!categorie) return '⚠️'; // Icône d'alerte si pas de catégorie
                    
                    switch(categorie) {
                      case 'Entrée': return '🥗';
                      case 'Plat': return '🍽️';
                      case 'Dessert': return '🍰';
                      case 'Bar': return '🍹';
                      case 'Autres': return '📝';
                      default: return '⚠️'; // Icône d'alerte pour catégorie non reconnue
                    }
                  };

                  return (
                    <div key={index} className="item-row">
                      <div className="item-info">
                        <div className="item-name">
                          {getProductionCategoryIcon(recette.categorie)} {recette.nom}
                          {recette.categorie ? (
                            <span className="category-badge" style={{
                              marginLeft: '8px',
                              padding: '4px 8px',
                              borderRadius: '12px',
                              fontSize: '12px',
                              background: 'var(--color-primary-blue)',
                              color: 'white'
                            }}>
                              {recette.categorie}
                            </span>
                          ) : (
                            <span className="category-badge" style={{
                              marginLeft: '8px',
                              padding: '4px 8px',
                              borderRadius: '12px',
                              fontSize: '12px',
                              background: 'var(--color-warning-orange)',
                              color: 'white'
                            }}>
                              Sans catégorie
                            </span>
                          )}
                        </div>
                        <div className="item-details">
                          Prix: {recette.prix_vente}€ • Marge: {recette.marge_beneficiaire || 'N/A'}%
                        </div>
                      </div>
                      <div className="item-actions">
                        {/* Éditer production - MASQUÉ pour employé cuisine */}
                        {canEditItems() && (
                          <button className="button small" onClick={() => handleEdit(recette, 'recette')}>Éditer</button>
                        )}
                        
                        {/* Archiver production - MASQUÉ pour employé cuisine */}
                        {canArchiveItems() && (
                          <button 
                            className="button small warning" 
                            onClick={async () => {
                              const reason = window.prompt(`Raison de l'archivage de "${recette.nom}" (optionnel):`);
                              if (reason !== null) {
                                const success = await archiveItem(recette.id, 'production', reason || null);
                                if (success) {
                                  alert(`${recette.nom} archivé avec succès !`);
                                } else {
                                  alert("Erreur lors de l'archivage");
                                }
                              }
                            }}
                          >
                            Archiver
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
                </>
                )}
              </div>
            )}

            {/* ONGLET GRILLES DE DONNÉES */}
            {activeProductionTab === 'datagrids' && (
              <div>
                <DataGridsPage />
              </div>
            )}

            {/* ONGLET ARCHIVES */}
            {activeProductionTab === 'archives' && (
              <div>
                <div className="section-card">
                  <div className="section-title">Gestion des Archives</div>
                  
                  {/* Filtres par type */}
                  <div className="filter-section" style={{marginBottom: '20px'}}>
                    <div style={{display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap'}}>
                      <label className="filter-label">Afficher :</label>
                      <select 
                        className="filter-select"
                        value={selectedArchiveType}
                        onChange={(e) => {
                          setSelectedArchiveType(e.target.value);
                          fetchArchives(e.target.value === 'tous' ? null : e.target.value);
                        }}
                        style={{
                          padding: '6px 10px',
                          borderRadius: '4px',
                          border: '1px solid var(--color-border)',
                          background: 'var(--color-background-card)',
                          color: 'var(--color-text-primary)',
                          fontSize: '13px'
                        }}
                      >
                        <option value="tous">Tous les éléments</option>
                        <option value="produit">Produits</option>
                        <option value="production">Productions</option>
                        <option value="fournisseur">Fournisseurs</option>
                      </select>
                      
                      <div className="filter-info" style={{
                        fontSize: '12px', 
                        color: 'var(--color-text-secondary)',
                        marginLeft: '10px'
                      }}>
                        {archivedItems.length} élément(s) archivé(s)
                      </div>
                    </div>
                  </div>

                  {/* Liste des éléments archivés */}
                  <div className="item-list">
                    {archivedItems.length === 0 ? (
                      <div style={{
                        textAlign: 'center',
                        padding: '40px',
                        color: 'var(--color-text-secondary)'
                      }}>
                        Aucun élément archivé
                      </div>
                    ) : (
                      archivedItems.map((archive, index) => (
                        <div key={archive.id} className="item-row">
                          <div className="item-info">
                            <div className="item-name">
                              {archive.item_type === 'produit' ? '📦' : 
                               archive.item_type === 'production' ? '🍽️' : '🚚'} {archive.original_data.nom}
                              <span className="category-badge" style={{
                                marginLeft: '8px',
                                padding: '2px 6px',
                                borderRadius: '8px',
                                fontSize: '10px',
                                background: 'var(--color-warning-orange)',
                                color: 'white'
                              }}>
                                {archive.item_type}
                              </span>
                            </div>
                            <div className="item-details">
                              Archivé le {new Date(archive.archived_at).toLocaleDateString('fr-FR')} • 
                              {archive.reason && ` Raison: ${archive.reason}`}
                            </div>
                          </div>
                          <div className="item-actions">
                            <button 
                              className="button small success"
                              onClick={async () => {
                                if (window.confirm(`Restaurer ${archive.original_data.nom} ?`)) {
                                  const success = await restoreItem(archive.id);
                                  if (success) {
                                    alert(`${archive.original_data.nom} restauré avec succès !`);
                                  } else {
                                    alert("Erreur lors de la restauration");
                                  }
                                }
                              }}
                            >
                              Restaurer
                            </button>
                            <button 
                              className="button small danger"
                              onClick={async () => {
                                if (window.confirm(`Supprimer définitivement ${archive.original_data.nom} ?\n\nCette action est irréversible !`)) {
                                  const success = await deleteArchivePermanently(archive.id);
                                  if (success) {
                                    alert(`${archive.original_data.nom} supprimé définitivement`);
                                  } else {
                                    alert("Erreur lors de la suppression");
                                  }
                                }
                              }}
                            >
                              Supprimer
                            </button>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* ONGLET HISTORIQUE */}
            {activeProductionTab === 'historique' && (
              <div>
                <div className="section-title">Historique des Opérations</div>
                
                {/* Bouton actualiser et indicateur auto-refresh */}
                <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px'}}>
                  <button 
                    className="button secondary"
                    onClick={fetchHistoriqueProduction}
                    style={{fontSize: '14px', padding: '8px 16px'}}
                  >
                    Actualiser
                  </button>
                  
                  <div style={{fontSize: '12px', color: '#6b7280', textAlign: 'right'}}>
                    Dernière mise à jour : {new Date().toLocaleTimeString('fr-FR')}
                    <br />
                    Auto-refresh toutes les 30s
                  </div>
                </div>
                
                <div className="item-list">
                  {historiqueProduction.length > 0 ? (
                    historiqueProduction.map((operation, index) => (
                      <div key={operation.id || index} className="item-row">
                        <div className="item-info">
                          <div className="item-name">{operation.nom}</div>
                          <div className="item-details">{operation.details}</div>
                        </div>
                        <div className={`item-value ${operation.couleur}`}>{operation.statut}</div>
                      </div>
                    ))
                  ) : (
                    <div style={{textAlign: 'center', padding: '40px', color: '#6b7280'}}>
                      <div style={{fontSize: '48px', marginBottom: '16px'}}>📊</div>
                      <div style={{fontSize: '16px', marginBottom: '8px'}}>Aucune opération récente</div>
                      <div style={{fontSize: '14px'}}>L&apos;historique se remplira automatiquement avec l&apos;activité</div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

    </>
  );
};

export default ProductionTab;
