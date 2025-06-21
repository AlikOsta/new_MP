import React, { useState, useEffect } from 'react';

const CategoriesPage = () => {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/categories/super-rubrics`);
      const data = await response.json();
      setCategories(data);
    } catch (err) {
      setError('Ошибка загрузки категорий');
      console.error('Categories loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    alert('Создание категорий будет добавлено в следующем обновлении');
  };

  const handleEdit = (category) => {
    alert(`Редактирование категории "${category.name_ru}" будет добавлено в следующем обновлении`);
  };

  const handleDelete = (category) => {
    alert(`Удаление категории "${category.name_ru}" будет добавлено в следующем обновлении`);
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
          onClick={handleCreate}
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
                      onClick={() => handleEdit(category)}
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
              onClick={handleCreate}
              className="mt-2 admin-btn admin-btn-primary"
            >
              Добавить первую категорию
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default CategoriesPage;