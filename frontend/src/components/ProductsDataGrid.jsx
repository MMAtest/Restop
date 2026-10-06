import React, { useMemo } from 'react';
import DataGrid from './DataGrid';

const ProductsDataGrid = ({ products = [], loading, onProductSelect, onProductEdit, onProductDelete }) => {

  // Actions renderer
  const ActionsRenderer = ({ data }) => (
    <div className="flex space-x-2">
      <button
        onClick={() => onProductEdit && onProductEdit(data)}
        className="text-blue-600 hover:text-blue-800 font-medium text-sm"
        title="Modifier"
      >
        ✏️
      </button>
      <button
        onClick={() => onProductDelete && onProductDelete(data)}
        className="text-red-600 hover:text-red-800 font-medium text-sm"
        title="Supprimer"
      >
      🗑️
      </button>
    </div>
  );

  // Status renderer
  const StatusRenderer = ({ data }) => {
    // Get stock status (you might want to fetch this separately)
    const status = data.quantite_actuelle <= data.quantite_min ? 'critique' : 'ok';
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
        status === 'critique' 
          ? 'bg-red-100 text-red-800' 
          : 'bg-green-100 text-green-800'
      }`}>
        {status === 'critique' ? 'Critique' : 'OK'}
      </span>
    );
  };

  // Price renderer
  const PriceRenderer = ({ value }) => {
    if (!value) return '-';
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR'
    }).format(value);
  };

  // Date renderer
  const DateRenderer = ({ value }) => {
    if (!value) return '-';
    return new Date(value).toLocaleDateString('fr-FR');
  };

  // Category renderer with icon
  const CategoryRenderer = ({ value }) => {
    const categoryIcons = {
      'Viandes et Poissons': '🥩',
      'Légumes et Fruits': '🥕',
      'Épices et Assaisonnements': '🌶️',
      'Produits Laitiers': '🧀',
      'Céréales et Légumineuses': '🌾',
      'Boissons': '🍷',
      'Autres': '📦'
    };
    
    const icon = categoryIcons[value] || '📦';
    return (
      <span className="flex items-center">
        <span className="mr-2">{icon}</span>
        {value || 'Non classé'}
      </span>
    );
  };

  // Column definitions
  const columnDefs = useMemo(() => [
    {
      headerName: 'Nom',
      field: 'nom',
      pinned: 'left',
      width: 200,
      cellStyle: { fontWeight: 'bold' }
    },
    {
      headerName: 'Catégorie',
      field: 'categorie',
      width: 180,
      cellRenderer: CategoryRenderer,
      filter: 'agTextColumnFilter'
    },
    {
      headerName: 'Prix Référence',
      field: 'reference_price',
      width: 130,
      cellRenderer: PriceRenderer,
      type: 'numericColumn',
      filter: 'agNumberColumnFilter'
    },
    {
      headerName: 'Prix Achat',
      field: 'prix_achat',
      width: 120,
      cellRenderer: PriceRenderer,
      type: 'numericColumn',
      filter: 'agNumberColumnFilter'
    },
    {
      headerName: 'Unité',
      field: 'unite',
      width: 80,
      filter: 'agTextColumnFilter'
    },
    {
      headerName: 'Fournisseur',
      field: 'fournisseur_nom',
      width: 150,
      filter: 'agTextColumnFilter'
    },
    {
      headerName: 'Créé le',
      field: 'created_at',
      width: 120,
      cellRenderer: DateRenderer,
      filter: 'agDateColumnFilter'
    },
    {
      headerName: 'Actions',
      field: 'actions',
      width: 120,
      cellRenderer: ActionsRenderer,
      sortable: false,
      filter: false,
      pinned: 'right'
    }
  ], []);

  const handleRowClicked = (event) => {
    if (onProductSelect) {
      onProductSelect(event.data);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto"></div>
          <p className="mt-2 text-gray-600">Chargement des produits...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm">
      <div className="p-4 border-b border-gray-200">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-lg font-semibold flex items-center">
              <span className="mr-2">🥕</span>
              Gestion des Produits & Ingrédients
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              {products.length} produits • Clic pour sélectionner • Filtrage et tri avancés
            </p>
          </div>
          <button
            onClick={() => window.location.reload()}
            className="text-primary-500 hover:text-primary-600 font-medium flex items-center"
          >
            <span className="mr-1">🔄</span>
            Actualiser
          </button>
        </div>
      </div>
      
      <div className="p-4">
        <DataGrid
          data={products}
          columns={columnDefs}
          height="500px"
          onRowClicked={handleRowClicked}
          paginationPageSize={25}
          className="rounded-lg overflow-hidden border border-gray-200"
        />
      </div>
    </div>
  );
};

export default ProductsDataGrid;