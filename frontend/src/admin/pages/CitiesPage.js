import React, { useState, useEffect } from 'react';

const CitiesPage = () => {
  const [cities, setCities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadCities();
  }, []);

  const loadCities = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/categories/cities`);
      const data = await response.json();
      setCities(data);
    } catch (err) {
      setError('Ошибка загрузки городов');
      console.error('Cities loading error:', err);
    } finally {
      setLoading(false);
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
          onClick={loadCities}
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
        <h1 className="text-2xl font-bold text-gray-900">Управление городами</h1>
        <button className="admin-btn admin-btn-primary">
          Добавить город
        </button>
      </div>

      {/* Cities Table */}
      <div className="data-table">
        <div className="p-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            Города ({cities.length})
          </h3>
        </div>
        <table>
          <thead>
            <tr>
              <th>Название (RU)</th>
              <th>Название (UA)</th>
              <th>Статус</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            {cities.map((city) => (
              <tr key={city.id}>
                <td className="font-medium">{city.name_ru}</td>
                <td>{city.name_ua}</td>
                <td>
                  <span className={`admin-badge ${
                    city.is_active ? 'admin-badge-success' : 'admin-badge-danger'
                  }`}>
                    {city.is_active ? 'Активен' : 'Неактивен'}
                  </span>
                </td>
                <td>
                  <div className="flex space-x-2">
                    <button className="admin-btn admin-btn-outline text-xs">
                      Редактировать
                    </button>
                    <button className="admin-btn admin-btn-danger text-xs">
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

export default CitiesPage;