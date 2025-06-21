import React, { useState, useEffect } from 'react';

const CurrenciesPage = () => {
  const [currencies, setCurrencies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedCurrency, setSelectedCurrency] = useState(null);
  const [formData, setFormData] = useState({
    code: '',
    name_ru: '',
    name_ua: '',
    symbol: '',
    is_active: true
  });

  useEffect(() => {
    loadCurrencies();
  }, []);

  const loadCurrencies = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('admin_token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/currencies`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setCurrencies(data);
    } catch (err) {
      setError('Ошибка загрузки валют');
      console.error('Currencies loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('admin_token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/currencies`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        setShowCreateModal(false);
        setFormData({
          code: '',
          name_ru: '',
          name_ua: '',
          symbol: '',
          is_active: true
        });
        loadCurrencies();
      }
    } catch (err) {
      console.error('Error creating currency:', err);
    }
  };

  const handleEdit = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('admin_token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/currencies/${selectedCurrency.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        setShowEditModal(false);
        setSelectedCurrency(null);
        setFormData({
          code: '',
          name_ru: '',
          name_ua: '',
          symbol: '',
          is_active: true
        });
        loadCurrencies();
      }
    } catch (err) {
      console.error('Error updating currency:', err);
    }
  };

  const handleDelete = async (currencyId) => {
    if (!window.confirm('Вы уверены, что хотите удалить эту валюту?')) {
      return;
    }

    try {
      const token = localStorage.getItem('admin_token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/currencies/${currencyId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        loadCurrencies();
      }
    } catch (err) {
      console.error('Error deleting currency:', err);
    }
  };

  const openEditModal = (currency) => {
    setSelectedCurrency(currency);
    setFormData({
      code: currency.code,
      name_ru: currency.name_ru,
      name_ua: currency.name_ua,
      symbol: currency.symbol,
      is_active: currency.is_active
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
          onClick={loadCurrencies}
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
        <h1 className="text-2xl font-bold text-gray-900">Управление валютами</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className="admin-btn admin-btn-primary"
        >
          Добавить валюту
        </button>
      </div>

      {/* Currencies Table */}
      <div className="data-table">
        <div className="p-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            Валюты ({currencies.length})
          </h3>
        </div>
        <table>
          <thead>
            <tr>
              <th>Код</th>
              <th>Название (RU)</th>
              <th>Название (UA)</th>
              <th>Символ</th>
              <th>Статус</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            {currencies.map((currency) => (
              <tr key={currency.id}>
                <td className="font-mono font-bold">{currency.code}</td>
                <td>{currency.name_ru}</td>
                <td>{currency.name_ua}</td>
                <td className="text-xl">{currency.symbol}</td>
                <td>
                  <span className={`admin-badge ${
                    currency.is_active ? 'admin-badge-success' : 'admin-badge-danger'
                  }`}>
                    {currency.is_active ? 'Активна' : 'Неактивна'}
                  </span>
                </td>
                <td>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => openEditModal(currency)}
                      className="admin-btn admin-btn-outline text-xs"
                    >
                      Редактировать
                    </button>
                    <button
                      onClick={() => handleDelete(currency.id)}
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
        
        {currencies.length === 0 && (
          <div className="p-8 text-center text-gray-500">
            <div className="text-4xl mb-2">💰</div>
            <p>Валюты не найдены</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="mt-2 admin-btn admin-btn-primary"
            >
              Добавить первую валюту
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
                <h3 className="text-xl font-semibold">Добавить валюту</h3>
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
                <label className="admin-form-label">Код валюты *</label>
                <input
                  type="text"
                  required
                  maxLength="3"
                  value={formData.code}
                  onChange={(e) => setFormData({...formData, code: e.target.value.toUpperCase()})}
                  className="admin-form-input"
                  placeholder="USD, EUR, RUB"
                />
              </div>
              
              <div>
                <label className="admin-form-label">Название (Русский) *</label>
                <input
                  type="text"
                  required
                  value={formData.name_ru}
                  onChange={(e) => setFormData({...formData, name_ru: e.target.value})}
                  className="admin-form-input"
                  placeholder="Доллар США"
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
                  placeholder="Долар США"
                />
              </div>
              
              <div>
                <label className="admin-form-label">Символ *</label>
                <input
                  type="text"
                  required
                  maxLength="3"
                  value={formData.symbol}
                  onChange={(e) => setFormData({...formData, symbol: e.target.value})}
                  className="admin-form-input"
                  placeholder="$, €, ₽"
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
                  Активная валюта
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
      {showEditModal && selectedCurrency && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full">
            <div className="p-6 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <h3 className="text-xl font-semibold">Редактировать валюту</h3>
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
                <label className="admin-form-label">Код валюты *</label>
                <input
                  type="text"
                  required
                  maxLength="3"
                  value={formData.code}
                  onChange={(e) => setFormData({...formData, code: e.target.value.toUpperCase()})}
                  className="admin-form-input"
                />
              </div>
              
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
              
              <div>
                <label className="admin-form-label">Символ *</label>
                <input
                  type="text"
                  required
                  maxLength="3"
                  value={formData.symbol}
                  onChange={(e) => setFormData({...formData, symbol: e.target.value})}
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
                  Активная валюта
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

export default CurrenciesPage;