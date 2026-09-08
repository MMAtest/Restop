import React, { useMemo } from 'react';
import { AgGridReact } from 'ag-grid-react';
import { ModuleRegistry, AllCommunityModule } from 'ag-grid-community';
import 'ag-grid-community/styles/ag-theme-quartz.css';

// Register AG Grid modules
ModuleRegistry.registerModules([AllCommunityModule]);

const DataGrid = ({ 
  data = [], 
  columns = [], 
  height = '400px',
  pagination = true,
  paginationPageSize = 20,
  sortable = true,
  filterable = true,
  resizable = true,
  className = '',
  onRowClicked = null,
  rowSelection = 'single',
  suppressRowClickSelection = false
}) => {
  
  // Default grid options
  const defaultColDef = useMemo(() => ({
    sortable: sortable,
    filter: filterable,
    resizable: resizable,
    flex: 1,
    minWidth: 100
  }), [sortable, filterable, resizable]);

  // Grid options
  const gridOptions = useMemo(() => ({
    defaultColDef,
    pagination,
    paginationPageSize,
    paginationPageSizeSelector: [10, 20, 25, 50, 100],
    rowSelection: { mode: 'singleRow', enableClickSelection: !suppressRowClickSelection },
    animateRows: true,
    enableCellTextSelection: true,
    localeText: {
      // French localization for common grid terms
      page: 'Page',
      to: 'à',
      of: 'sur',
      next: 'Suivant',
      previous: 'Précédent',
      loadingOoo: 'Chargement...',
      noRowsToShow: 'Aucune donnée à afficher',
      contains: 'Contient',
      notContains: 'Ne contient pas',
      equals: 'Égal à',
      notEqual: 'Différent de',
      startsWith: 'Commence par',
      endsWith: 'Finit par',
      filterOoo: 'Filtrer...',
      applyFilter: 'Appliquer',
      resetFilter: 'Réinitialiser',
      andCondition: 'ET',
      orCondition: 'OU'
    }
  }), [defaultColDef, pagination, paginationPageSize, suppressRowClickSelection]);

  return (
    <div 
      className={`ag-theme-quartz ${className}`} 
      style={{ height, width: '100%' }}
    >
      <AgGridReact
        rowData={data}
        columnDefs={columns}
        gridOptions={gridOptions}
        onRowClicked={onRowClicked}
        suppressCellFocus={true}
      />
    </div>
  );
};

export default DataGrid;