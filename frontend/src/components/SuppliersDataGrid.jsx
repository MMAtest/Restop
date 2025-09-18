import React, { useMemo } from 'react';
import DataGrid from './DataGrid';

const SuppliersDataGrid = ({ suppliers = [], loading, onSupplierSelect, onSupplierEdit, onSupplierDelete }) => {

  // Actions renderer
  const ActionsRenderer = ({ data }) => (
    <div className="flex space-x-2">
      <button
        onClick={() => onSupplierEdit && onSupplierEdit(data)}
        className="text-blue-600 hover:text-blue-800 font-medium text-sm"
        title="Modifier"
      >
        ✏️
      </button>
      <button
        onClick={() => window.open(`tel:${data.telephone}`, '_self')}
        className="text-green-600 hover:text-green-800 font-medium text-sm"
        title="Appeler"
        disabled={!data.telephone}
      >
        📞
      </button>
      <button
        onClick={() => window.open(`mailto:${data.email}`, '_self')}
        className="text-orange-600 hover:text-orange-800 font-medium text-sm"
        title="Email"
        disabled={!data.email}
      >
        📧
      </button>
      <button
        onClick={() => onSupplierDelete && onSupplierDelete(data)}
        className="text-red-600 hover:text-red-800 font-medium text-sm"
        title="Supprimer"
      >
        🗑️
      </button>
    </div>
  );

  // Contact renderer
  const ContactRenderer = ({ data }) => (
    <div className="space-y-1">
      {data.telephone && (
        <div className="text-sm flex items-center">
          <span className="mr-1">📞</span>
          {data.telephone}
        </div>
      )}
      {data.email && (
        <div className="text-sm flex items-center">
          <span className="mr-1">📧</span>
          {data.email}
        </div>
      )}
      {!data.telephone && !data.email && (
        <span className="text-gray-400 text-sm">Non renseigné</span>
      )}
    </div>
  );

  // Address renderer
  const AddressRenderer = ({ data }) => {
    const addressParts = [
      data.adresse,
      data.ville,
      data.code_postal
    ].filter(Boolean);

    return (
      <div className="text-sm">
        {addressParts.length > 0 ? (
          <div>
            {data.adresse && <div>{data.adresse}</div>}
            {(data.ville || data.code_postal) && (
              <div className="text-gray-600">
                {data.code_postal} {data.ville}
              </div>
            )}
          </div>
        ) : (
          <span className="text-gray-400">Non renseignée</span>
        )}
      </div>
    );
  };

  // Date renderer
  const DateRenderer = ({ value }) => {
    if (!value) return '-';
    return new Date(value).toLocaleDateString('fr-FR');
  };

  // Status renderer based on recent activity
  const StatusRenderer = ({ data }) => {
    // Simple status logic - could be enhanced with real activity data
    const hasContact = data.telephone || data.email;
    const hasAddress = data.adresse || data.ville;
    
    let status = 'complet';
    let statusText = '✅ Complet';
    let statusColor = 'bg-green-100 text-green-800';
    
    if (!hasContact && !hasAddress) {
      status = 'incomplet';
      statusText = '❌ Incomplet';
      statusColor = 'bg-red-100 text-red-800';
    } else if (!hasContact || !hasAddress) {
      status = 'partiel';
      statusText = '⚠️ Partiel';
      statusColor = 'bg-yellow-100 text-yellow-800';
    }

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColor}`}>
        {statusText}
      </span>
    );
  };

  // Column definitions
  const columnDefs = useMemo(() => [
    {
      headerName: 'Fournisseur',
      field: 'nom',
      pinned: 'left',
      width: 200,
      cellStyle: { fontWeight: 'bold' }
    },
    {
      headerName: 'Contact',
      field: 'contact',
      width: 200,
      cellRenderer: ContactRenderer,
      sortable: false,
      filter: false
    },
    {
      headerName: 'Adresse',
      field: 'adresse_complete',
      width: 250,
      cellRenderer: AddressRenderer,
      sortable: false,
      filter: 'agTextColumnFilter'
    },
    {
      headerName: 'Spécialités',
      field: 'specialites',
      width: 180,
      filter: 'agTextColumnFilter',
      cellRenderer: ({ value }) => value || 'Non spécifiées'
    },
    {
      headerName: 'Conditions Paiement',
      field: 'conditions_paiement',
      width: 160,
      filter: 'agTextColumnFilter',
      cellRenderer: ({ value }) => value || 'Standard'
    },
    {
      headerName: 'Statut',
      field: 'statut',
      width: 120,
      cellRenderer: StatusRenderer,
      filter: 'agSetColumnFilter'
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
      width: 150,
      cellRenderer: ActionsRenderer,
      sortable: false,
      filter: false,
      pinned: 'right'
    }
  ], []);

  const handleRowClicked = (event) => {
    if (onSupplierSelect) {
      onSupplierSelect(event.data);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto"></div>
          <p className="mt-2 text-gray-600">Chargement des fournisseurs...</p>
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
              <span className="mr-2">🏢</span>
              Gestion des Fournisseurs
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              {suppliers.length} fournisseurs • Actions rapides : Appel, Email, Modification
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
          data={suppliers}
          columns={columnDefs}
          height="500px"
          onRowClicked={handleRowClicked}
          paginationPageSize={20}
          className="rounded-lg overflow-hidden border border-gray-200"
        />
      </div>
    </div>
  );
};

export default SuppliersDataGrid;