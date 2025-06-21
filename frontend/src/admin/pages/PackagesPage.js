import React, { useState, useEffect } from 'react';

const PackagesPage = () => {
  const [packages, setPackages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadPackages();
  }, []);

  const loadPackages = async () => {
    try {
      setLoading(true);
      // Mock data since we don't have packages endpoint in API
      const mockPackages = [
        {
          id: 'basic-package',
          name_ru: 'Базовый',
          name_ua: 'Базовий',
          package_type: 'basic',
          price: 0,
          currency_code: 'RUB',
          duration_days: 7,
          features_ru: ['1 бесплатное объявление в неделю', 'Стандартное размещение'],
          features_ua: ['1 безкоштовне оголошення на тиждень', 'Стандартне розміщення'],
          is_active: true
        },
        {
          id: 'standard-package',
          name_ru: 'Стандарт',
          name_ua: 'Стандарт',
          package_type: 'standard',
          price: 100,
          currency_code: 'RUB',
          duration_days: 14,
          features_ru: ['Приоритетное размещение', 'Выделение цветом', 'Больше просмотров'],
          features_ua: ['Пріоритетне розміщення', 'Виділення кольором', 'Більше переглядів'],
          is_active: true
        },
        {
          id: 'premium-package',
          name_ru: 'Премиум',
          name_ua: 'Преміум',
          package_type: 'premium',
          price: 250,
          currency_code: 'RUB',
          duration_days: 30,
          features_ru: ['Топ размещение', 'Особое выделение', 'Максимум просмотров', 'Поддержка'],
          features_ua: ['Топ розміщення', 'Особливе виділення', 'Максимум переглядів', 'Підтримка'],
          is_active: true
        }
      ];
      setPackages(mockPackages);
    } catch (err) {
      setError('Ошибка загрузки тарифов');
      console.error('Packages loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getPackageIcon = (type) => {
    switch (type) {
      case 'basic': return '📦';
      case 'standard': return '⭐';
      case 'premium': return '💎';
      default: return '📋';
    }
  };

  if (loading) {
    return (
      <div className="admin-loading">
        <div className="admin-spinner"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="text-red-800">{error}</div>
        <button 
          onClick={loadPackages}
          className="mt-2 admin-btn admin-btn-primary"
        >
          Попробовать снова
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Управление тарифами</h1>
        <button 
          onClick={() => alert('Создание тарифов будет добавлено в следующем обновлении')}
          className="admin-btn admin-btn-primary"
        >
          Добавить тариф
        </button>
      </div>

      {/* Packages Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {packages.map((pkg) => (
          <div key={pkg.id} className="bg-white rounded-lg shadow border border-gray-200">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">{getPackageIcon(pkg.package_type)}</span>
                  <h3 className="text-lg font-semibold text-gray-900">{pkg.name_ru}</h3>
                </div>
                <span className={`admin-badge ${
                  pkg.is_active ? 'admin-badge-success' : 'admin-badge-danger'
                }`}>
                  {pkg.is_active ? 'Активен' : 'Неактивен'}
                </span>
              </div>
              
              <div className="mb-4">
                <div className="text-3xl font-bold text-gray-900">
                  {pkg.price === 0 ? 'Бесплатно' : `${pkg.price} ${pkg.currency_code}`}
                </div>
                <div className="text-sm text-gray-500">
                  на {pkg.duration_days} дней
                </div>
              </div>
              
              <div className="mb-6">
                <h4 className="font-medium text-gray-900 mb-2">Возможности:</h4>
                <ul className="space-y-1">
                  {pkg.features_ru.map((feature, index) => (
                    <li key={index} className="text-sm text-gray-600 flex items-start">
                      <span className="text-green-500 mr-2 mt-0.5">✓</span>
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>
              
              <div className="flex space-x-2">
                <button 
                  onClick={() => alert(`Редактирование тарифа "${pkg.name_ru}" будет добавлено в следующем обновлении`)}
                  className="admin-btn admin-btn-outline text-xs flex-1"
                >
                  Редактировать
                </button>
                <button 
                  onClick={() => alert(`Удаление тарифа "${pkg.name_ru}" будет добавлено в следующем обновлении`)}
                  className="admin-btn admin-btn-danger text-xs"
                >
                  Удалить
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {/* Table View */}
      <div className="data-table">
        <div className="p-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            Детальный список тарифов
          </h3>
        </div>
        <table>
          <thead>
            <tr>
              <th>Тариф</th>
              <th>Тип</th>
              <th>Цена</th>
              <th>Продолжительность</th>
              <th>Статус</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            {packages.map((pkg) => (
              <tr key={pkg.id}>
                <td>
                  <div className="flex items-center space-x-3">
                    <span className="text-xl">{getPackageIcon(pkg.package_type)}</span>
                    <div>
                      <div className="font-medium">{pkg.name_ru}</div>
                      <div className="text-sm text-gray-500">{pkg.name_ua}</div>
                    </div>
                  </div>
                </td>
                <td className="capitalize">{pkg.package_type}</td>
                <td className="font-medium">
                  {pkg.price === 0 ? 'Бесплатно' : `${pkg.price} ${pkg.currency_code}`}
                </td>
                <td>{pkg.duration_days} дней</td>
                <td>
                  <span className={`admin-badge ${
                    pkg.is_active ? 'admin-badge-success' : 'admin-badge-danger'
                  }`}>
                    {pkg.is_active ? 'Активен' : 'Неактивен'}
                  </span>
                </td>
                <td>
                  <div className="flex space-x-2">
                    <button 
                      onClick={() => alert(`Редактирование тарифа "${pkg.name_ru}" будет добавлено в следующем обновлении`)}
                      className="admin-btn admin-btn-outline text-xs"
                    >
                      Редактировать
                    </button>
                    <button 
                      onClick={() => alert(`Удаление тарифа "${pkg.name_ru}" будет добавлено в следующем обновлении`)}
                      className="admin-btn admin-btn-danger text-xs"
                    >
                      Удалить
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default PackagesPage;