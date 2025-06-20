import React, { useState } from 'react';

const TariffsModal = ({ isOpen, onClose, packages, currencies, onSelectPackage }) => {
  const [selectedPackage, setSelectedPackage] = useState(null);

  const getCurrencySymbol = (currencyId) => {
    const currency = currencies.find(c => c.id === currencyId);
    return currency?.symbol || '₽';
  };

  const handleSelectTariff = () => {
    if (selectedPackage) {
      onSelectPackage(selectedPackage.id);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg w-full max-w-md max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-white border-b px-6 py-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Tariffs</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-xl"
            >
              ←
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <h3 className="text-lg font-semibold text-center mb-6">Choose a tariff</h3>
          
          <div className="space-y-4">
            {packages.map(pkg => (
              <div
                key={pkg.id}
                onClick={() => setSelectedPackage(pkg)}
                className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                  selectedPackage?.id === pkg.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                {/* Package Header */}
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-lg font-semibold capitalize">{pkg.name_ru}</h4>
                  <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${
                    selectedPackage?.id === pkg.id
                      ? 'border-blue-500 bg-blue-500'
                      : 'border-gray-300'
                  }`}>
                    {selectedPackage?.id === pkg.id && (
                      <div className="w-2 h-2 bg-white rounded-full"></div>
                    )}
                  </div>
                </div>

                {/* Price */}
                <div className="mb-3">
                  {pkg.price === 0 ? (
                    <span className="text-2xl font-bold text-green-600">Бесплатно</span>
                  ) : (
                    <span className="text-2xl font-bold text-gray-900">
                      {new Intl.NumberFormat('ru-RU').format(pkg.price)} {getCurrencySymbol(pkg.currency_id)}
                    </span>
                  )}
                  <span className="text-gray-500 ml-2">на {pkg.duration_days} дней</span>
                </div>

                {/* Features */}
                <div className="space-y-2">
                  {pkg.features_ru.map((feature, index) => (
                    <div key={index} className="flex items-center text-sm text-gray-600">
                      <span className="text-green-500 mr-2">✓</span>
                      {feature}
                    </div>
                  ))}
                </div>

                {/* Special styling for Basic (free) package */}
                {pkg.package_type === 'basic' && (
                  <div className="mt-3 p-2 bg-green-50 border border-green-200 rounded text-sm text-green-700">
                    <div className="flex items-center">
                      <span className="mr-2">ℹ️</span>
                      1 бесплатное объявление в неделю. Далее по тарифу.
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="border-t bg-white p-6">
          <button
            onClick={handleSelectTariff}
            disabled={!selectedPackage}
            className={`w-full py-3 px-4 rounded-lg font-medium ${
              selectedPackage
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }`}
          >
            {selectedPackage?.price === 0 ? 'Выбрать бесплатный тариф' : 'Select tariff'}
          </button>

          {selectedPackage && selectedPackage.price > 0 && (
            <p className="text-center text-sm text-gray-500 mt-3">
              Оплата через Telegram Payments
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default TariffsModal;