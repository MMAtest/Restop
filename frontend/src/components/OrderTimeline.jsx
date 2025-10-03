import React from 'react';

const OrderTimeline = ({ order }) => {
  const getStatusInfo = (status) => {
    const statusMap = {
      pending: { label: 'En attente', color: 'yellow', icon: '⏳', step: 1 },
      confirmed: { label: 'Confirmée', color: 'blue', icon: '✓', step: 2 },
      in_transit: { label: 'En cours', color: 'purple', icon: '🚚', step: 3 },
      delivered: { label: 'Livrée', color: 'green', icon: '✅', step: 4 },
      cancelled: { label: 'Annulée', color: 'red', icon: '❌', step: 0 }
    };
    return statusMap[status] || statusMap.pending;
  };

  const currentStatus = getStatusInfo(order.status);
  const isCancelled = order.status === 'cancelled';

  const steps = [
    { id: 'pending', label: 'Commandé', step: 1 },
    { id: 'confirmed', label: 'Confirmé', step: 2 },
    { id: 'in_transit', label: 'En transit', step: 3 },
    { id: 'delivered', label: 'Livré', step: 4 }
  ];

  const getStepStatus = (stepNumber) => {
    if (isCancelled) return 'cancelled';
    if (stepNumber <= currentStatus.step) return 'completed';
    if (stepNumber === currentStatus.step + 1) return 'current';
    return 'upcoming';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', { 
      weekday: 'short', 
      day: '2-digit', 
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (isCancelled) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center gap-3 mb-4">
          <span className="text-3xl">❌</span>
          <div>
            <h3 className="font-bold text-red-800">Commande annulée</h3>
            <p className="text-sm text-red-600">
              Commandée le {formatDate(order.order_date)}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      {/* En-tête avec statut actuel */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <span className="text-3xl">{currentStatus.icon}</span>
          <div>
            <h3 className="font-bold text-gray-800">
              {currentStatus.label}
            </h3>
            <p className="text-sm text-gray-500">
              Commande n°{order.order_number}
            </p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-sm text-gray-500">Livraison estimée</p>
          <p className="font-semibold text-blue-600">
            {formatDate(order.estimated_delivery_date)}
          </p>
        </div>
      </div>

      {/* Timeline horizontale */}
      <div className="relative">
        {/* Ligne de progression */}
        <div className="absolute top-5 left-0 right-0 h-1 bg-gray-200 rounded">
          <div 
            className={`h-full rounded transition-all duration-500 ${
              currentStatus.step >= 4 ? 'bg-green-500' : 
              currentStatus.step >= 3 ? 'bg-purple-500' :
              currentStatus.step >= 2 ? 'bg-blue-500' : 'bg-yellow-500'
            }`}
            style={{ width: `${(currentStatus.step / 4) * 100}%` }}
          />
        </div>

        {/* Étapes */}
        <div className="relative flex justify-between">
          {steps.map((step, index) => {
            const stepStatus = getStepStatus(step.step);
            const isCompleted = stepStatus === 'completed';
            const isCurrent = stepStatus === 'current';
            
            return (
              <div key={step.id} className="flex flex-col items-center" style={{ width: '25%' }}>
                {/* Cercle d'étape */}
                <div className={`w-10 h-10 rounded-full border-4 flex items-center justify-center font-bold transition-all duration-300 ${
                  isCompleted ? 'bg-blue-500 border-blue-500 text-white' :
                  isCurrent ? 'bg-white border-blue-500 text-blue-500 ring-4 ring-blue-100' :
                  'bg-white border-gray-300 text-gray-400'
                }`}>
                  {isCompleted ? '✓' : step.step}
                </div>
                
                {/* Label */}
                <p className={`mt-2 text-xs font-medium text-center ${
                  isCompleted || isCurrent ? 'text-gray-800' : 'text-gray-400'
                }`}>
                  {step.label}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Informations supplémentaires */}
      <div className="mt-6 pt-4 border-t border-gray-200 grid grid-cols-2 gap-4 text-sm">
        <div>
          <p className="text-gray-500">Date de commande</p>
          <p className="font-medium">{formatDate(order.order_date)}</p>
        </div>
        {order.actual_delivery_date && (
          <div>
            <p className="text-gray-500">Livré le</p>
            <p className="font-medium text-green-600">{formatDate(order.actual_delivery_date)}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default OrderTimeline;