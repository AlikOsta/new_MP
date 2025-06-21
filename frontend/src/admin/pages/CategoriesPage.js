import React, { useState, useEffect } from 'react';

const CategoriesPage = () => {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [formData, setFormData] = useState({
    name_ru: '',
    name_ua: '',
    icon: '',
    is_active: true
  });

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('admin_token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/categories`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setCategories(data);
    } catch (err) {
      setError('Ошибка загрузки категорий');
      console.error('Categories loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('admin_token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/categories`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        setShowCreateModal(false);
        setFormData({ name_ru: '', name_ua: '', icon: '', is_active: true });
        loadCategories();
      } else {
        const error = await response.json();
        alert(error.error || 'Ошибка создания категории');
      }
    } catch (err) {
      console.error('Error creating category:', err);
      alert('Ошибка создания категории');
    }
  };

  const handleEdit = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('admin_token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/categories/${selectedCategory.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        setShowEditModal(false);
        setSelectedCategory(null);
        setFormData({ name_ru: '', name_ua: '', icon: '', is_active: true });
        loadCategories();
      } else {
        const error = await response.json();
        alert(error.error || 'Ошибка редактирования категории');
      }
    } catch (err) {
      console.error('Error updating category:', err);
      alert('Ошибка редактирования категории');
    }
  };

  const handleDelete = async (category) => {
    if (!window.confirm(`Вы уверены, что хотите удалить категорию "${category.name_ru}"?`)) {
      return;
    }

    try {
      const token = localStorage.getItem('admin_token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/categories/${category.id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        loadCategories();
      } else {
        const error = await response.json();
        alert(error.error || 'Ошибка удаления категории');
      }
    } catch (err) {
      console.error('Error deleting category:', err);
      alert('Ошибка удаления категории');
    }
  };

  const openEditModal = (category) => {
    setSelectedCategory(category);
    setFormData({
      name_ru: category.name_ru,
      name_ua: category.name_ua,
      icon: category.icon,
      is_active: category.is_active
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
          onClick={loadCategories}
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
        <h1 className="text-2xl font-bold text-gray-900">Управление категориями</h1>
        <button 
          onClick={() => setShowCreateModal(true)}
          className="admin-btn admin-btn-primary"
        >
          Добавить категорию
        </button>
      </div>

      {/* Categories Table */}
      <div className="data-table">
        <div className="p-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            Категории ({categories.length})
          </h3>
        </div>
        <table>
          <thead>
            <tr>
              <th>Иконка</th>
              <th>Название (RU)</th>
              <th>Название (UA)</th>
              <th>Статус</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            {categories.map((category) => (
              <tr key={category.id}>
                <td className="text-2xl">{category.icon}</td>
                <td className="font-medium">{category.name_ru}</td>
                <td>{category.name_ua}</td>
                <td>
                  <span className={`admin-badge ${
                    category.is_active ? 'admin-badge-success' : 'admin-badge-danger'
                  }`}>
                    {category.is_active ? 'Активна' : 'Неактивна'}
                  </span>
                </td>
                <td>
                  <div className="flex space-x-2">
                    <button 
                      onClick={() => openEditModal(category)}
                      className="admin-btn admin-btn-outline text-xs"
                    >
                      Редактировать
                    </button>
                    <button 
                      onClick={() => handleDelete(category)}
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
        
        {categories.length === 0 && (
          <div className="p-8 text-center text-gray-500">
            <div className="text-4xl mb-2">📂</div>
            <p>Категории не найдены</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="mt-2 admin-btn admin-btn-primary"
            >
              Добавить первую категорию
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
                <h3 className="text-xl font-semibold">Добавить категорию</h3>
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
                  placeholder="Работа"
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
                  placeholder="Робота"
                />
              </div>
              
              <div>
                <label className="admin-form-label">Иконка (emoji) *</label>
                <input
                  type="text"
                  required
                  maxLength="2"
                  value={formData.icon}
                  onChange={(e) => setFormData({...formData, icon: e.target.value})}
                  className="admin-form-input"
                  placeholder="💼"
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
                  Активная категория
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
      {showEditModal && selectedCategory && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full">
            <div className="p-6 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <h3 className="text-xl font-semibold">Редактировать категорию</h3>
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
              
              <div>
                <label className="admin-form-label">Иконка (emoji) *</label>
                <input
                  type="text"
                  required
                  maxLength="2"
                  value={formData.icon}
                  onChange={(e) => setFormData({...formData, icon: e.target.value})}
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
                  Активная категория
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

export default CategoriesPage;