import React from 'react';

const Pagination = ({ 
  currentPage, 
  totalPages, 
  onPageChange, 
  startIndex, 
  endIndex, 
  totalItems,
  itemLabel = 'éléments'
}) => {
  if (totalPages <= 1) return null;

  return (
    <div className="pagination-container">
      <div className="pagination-info">
        Page {currentPage} sur {totalPages} • 
        {startIndex + 1}-{Math.min(endIndex, totalItems)} sur {totalItems} {itemLabel}
      </div>
      
      <div className="pagination-buttons">
        <button 
          className="button small" 
          onClick={() => onPageChange(1)}
          disabled={currentPage === 1}
          style={{
            opacity: currentPage === 1 ? 0.5 : 1,
            cursor: currentPage === 1 ? 'not-allowed' : 'pointer'
          }}
        >
          ⏮️ Début
        </button>
        <button 
          className="button small" 
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          style={{
            opacity: currentPage === 1 ? 0.5 : 1,
            cursor: currentPage === 1 ? 'not-allowed' : 'pointer'
          }}
        >
          ⬅️ Préc.
        </button>
        <button 
          className="button small" 
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          style={{
            opacity: currentPage === totalPages ? 0.5 : 1,
            cursor: currentPage === totalPages ? 'not-allowed' : 'pointer'
          }}
        >
          Suiv. ➡️
        </button>
        <button 
          className="button small" 
          onClick={() => onPageChange(totalPages)}
          disabled={currentPage === totalPages}
          style={{
            opacity: currentPage === totalPages ? 0.5 : 1,
            cursor: currentPage === totalPages ? 'not-allowed' : 'pointer'
          }}
        >
          Fin ⏭️
        </button>
      </div>
    </div>
  );
};

export default Pagination;
