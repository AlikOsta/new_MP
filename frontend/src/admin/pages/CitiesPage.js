import React, { useState, useEffect } from 'react';

const CitiesPage = () => {
  const [cities, setCities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedCity, setSelectedCity] = useState(null);
  const [formData, setFormData] = useState({
    name_ru: '',
    name_ua: '',
    is_active: true
  });

  useEffect(() => {
    loadCities();
  }, []);

  const loadCities = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('admin_token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/cities`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setCities(data);
    } catch (err) {
      setError('Ошибка загрузки городов');
      console.error('Cities loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('admin_token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/cities`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        setShowCreateModal(false);
        setFormData({ name_ru: '', name_ua: '', is_active: true });
        loadCities();
      } else {
        const error = await response.json();
        alert(error.error || 'Ошибка создания города');
      }
    } catch (err) {
      console.error('Error creating city:', err);
      alert('Ошибка создания города');
    }
  };

  const handleEdit = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('admin_token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/cities/${selectedCity.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        setShowEditModal(false);
        setSelectedCity(null);
        setFormData({ name_ru: '', name_ua: '', is_active: true });
        loadCities();
      } else {
        const error = await response.json();
        alert(error.error || 'Ошибка редактирования города');
      }
    } catch (err) {
      console.error('Error updating city:', err);
      alert('Ошибка редактирования города');
    }
  };

  const handleDelete = async (city) => {
    if (!window.confirm(`Вы уверены, что хотите удалить город "${city.name_ru}"?`)) {
      return;
    }

    try {
      const token = localStorage.getItem('admin_token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/cities/${city.id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        loadCities();
      } else {
        const error = await response.json();
        alert(error.error || 'Ошибка удаления города');
      }
    } catch (err) {
      console.error('Error deleting city:', err);
      alert('Ошибка удаления города');
    }
  };

  const openEditModal = (city) => {
    setSelectedCity(city);
    setFormData({
      name_ru: city.name_ru,
      name_ua: city.name_ua,
      is_active: city.is_active
    });
    setShowEditModal(true);
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
        <button 
          onClick={() => setShowCreateModal(true)}
          className="admin-btn admin-btn-primary"
        >
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
                    <button 
                      onClick={() => openEditModal(city)}
                      className="admin-btn admin-btn-outline text-xs"
                    >
                      Редактировать
                    </button>
                    <button 
                      onClick={() => handleDelete(city)}
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
        
        {cities.length === 0 && (
          <div className="p-8 text-center text-gray-500">
            <div className="text-4xl mb-2">🏙️</div>
            <p>Города не найдены</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="mt-2 admin-btn admin-btn-primary"
            >
              Добавить первый город
            </button>
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full">
            <div className="p-6 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <h3 className="text-xl font-semibold">Добавить город</h3>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
            </div>
            
            <form onSubmit={handleCreate} className="p-6 space-y-4">
              <div>
                <label className="admin-form-label">Название (Русский) *</label>
                <input
                  type="text"
                  required
                  value={formData.name_ru}
                  onChange={(e) => setFormData({...formData, name_ru: e.target.value})}
                  className="admin-form-input"
                  placeholder="Москва"
                />
              </div>
              
              <div>
                <label className="admin-form-label">Название (Украинский) *</label>
                <input
                  type="text"
                  required
                  value={formData.name_ua}
                  onChange={(e) => setFormData({...formData, name_ua: e.target.value})}
                  className="admin-form-input"
                  placeholder="Москва"
                />
              </div>
              
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({...formData, is_active: e.target.checked})}
                  className="mr-2"
                />
                <label htmlFor="is_active" className="text-sm text-gray-700">
                  Активный город
                </label>
              </div>
              
              <div className="flex space-x-3 pt-4">
                <button
                  type="submit"
                  className="admin-btn admin-btn-primary flex-1"
                >
                  Создать
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="admin-btn admin-btn-outline flex-1"
                >
                  Отмена
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && selectedCity && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full">
            <div className="p-6 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <h3 className="text-xl font-semibold">Редактировать город</h3>
                <button
                  onClick={() => setShowEditModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
            </div>
            
            <form onSubmit={handleEdit} className="p-6 space-y-4">
              <div>
                <label className="admin-form-label">Название (Русский) *</label>
                <input
                  type="text"
                  required
                  value={formData.name_ru}
                  onChange={(e) => setFormData({...formData, name_ru: e.target.value})}
                  className="admin-form-input"
                />
              </div>
              
              <div>
                <label className="admin-form-label">Название (Украинский) *</label>
                <input
                  type="text"
                  required
                  value={formData.name_ua}
                  onChange={(e) => setFormData({...formData, name_ua: e.target.value})}
                  className="admin-form-input"
                />
              </div>
              
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="edit_is_active"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({...formData, is_active: e.target.checked})}
                  className="mr-2"
                />
                <label htmlFor="edit_is_active" className="text-sm text-gray-700">
                  Активный город
                </label>
              </div>
              
              <div className="flex space-x-3 pt-4">
                <button
                  type="submit"
                  className="admin-btn admin-btn-primary flex-1"
                >
                  Сохранить
                </button>
                <button
                  type="button"
                  onClick={() => setShowEditModal(false)}
                  className="admin-btn admin-btn-outline flex-1"
                >
                  Отмена
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default CitiesPage;