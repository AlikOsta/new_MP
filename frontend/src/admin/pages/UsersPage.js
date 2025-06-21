import React, { useState, useEffect } from 'react';

const UsersPage = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedUser, setSelectedUser] = useState(null);
  const [showUserModal, setShowUserModal] = useState(false);

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      setLoading(true);
      
      // For now, we don't have a users API endpoint, so show empty state
      // In the future, this would be: const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/users`);
      setUsers([]);
    } catch (err) {
      setError('Ошибка загрузки пользователей');
      console.error('Users loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredUsers = users.filter(user => {
    const matchesSearch = !searchTerm || 
      user.first_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.last_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.username.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = filterStatus === 'all' || 
      (filterStatus === 'active' && user.is_active) ||
      (filterStatus === 'inactive' && !user.is_active);
    
    return matchesSearch && matchesStatus;
  });

  const handleUserClick = (user) => {
    setSelectedUser(user);
    setShowUserModal(true);
  };

  const handleUserStatusToggle = async (userId) => {
    try {
      // Mock API call
      setUsers(users.map(user => 
        user.id === userId 
          ? { ...user, is_active: !user.is_active }
          : user
      ));
    } catch (err) {
      console.error('Error toggling user status:', err);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('ru-RU', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
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
          onClick={loadUsers}
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
        <h1 className="text-2xl font-bold text-gray-900">Управление пользователями</h1>
        <div className="text-sm text-gray-500">
          Всего: {users.length} пользователей
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="admin-form-label">Поиск</label>
            <input
              type="text"
              placeholder="Имя, фамилия или username"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="admin-form-input"
            />
          </div>
          <div>
            <label className="admin-form-label">Статус</label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="admin-form-select"
            >
              <option value="all">Все пользователи</option>
              <option value="active">Активные</option>
              <option value="inactive">Неактивные</option>
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={() => {
                setSearchTerm('');
                setFilterStatus('all');
              }}
              className="admin-btn admin-btn-outline w-full"
            >
              Сбросить фильтры
            </button>
          </div>
        </div>
      </div>

      {/* Users Table */}
      <div className="data-table">
        <div className="p-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            Пользователи ({filteredUsers.length})
          </h3>
        </div>
        <table>
          <thead>
            <tr>
              <th>Пользователь</th>
              <th>Telegram ID</th>
              <th>Объявления</th>
              <th>Статус</th>
              <th>Регистрация</th>
              <th>Последняя активность</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            {filteredUsers.map((user) => (
              <tr key={user.id}>
                <td>
                  <div 
                    className="flex items-center space-x-3 cursor-pointer hover:text-blue-600"
                    onClick={() => handleUserClick(user)}
                  >
                    <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                      <span className="text-blue-600 text-sm font-medium">
                        {user.first_name.charAt(0)}
                      </span>
                    </div>
                    <div>
                      <div className="font-medium">
                        {user.first_name} {user.last_name}
                      </div>
                      <div className="text-sm text-gray-500">
                        @{user.username}
                      </div>
                    </div>
                  </div>
                </td>
                <td className="font-mono text-sm">{user.telegram_id}</td>
                <td>
                  <span className="admin-badge admin-badge-info">
                    {user.posts_count}
                  </span>
                </td>
                <td>
                  <span className={`admin-badge ${
                    user.is_active ? 'admin-badge-success' : 'admin-badge-danger'
                  }`}>
                    {user.is_active ? 'Активен' : 'Неактивен'}
                  </span>
                </td>
                <td className="text-sm text-gray-500">
                  {formatDate(user.created_at)}
                </td>
                <td className="text-sm text-gray-500">
                  {formatDate(user.last_activity)}
                </td>
                <td>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleUserStatusToggle(user.id)}
                      className={`admin-btn text-xs ${
                        user.is_active ? 'admin-btn-danger' : 'admin-btn-success'
                      }`}
                    >
                      {user.is_active ? 'Заблокировать' : 'Активировать'}
                    </button>
                    <button
                      onClick={() => handleUserClick(user)}
                      className="admin-btn admin-btn-outline text-xs"
                    >
                      Детали
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {filteredUsers.length === 0 && (
          <div className="p-8 text-center text-gray-500">
            <div className="text-4xl mb-2">👥</div>
            <p>Пользователи не найдены</p>
            {searchTerm && (
              <button
                onClick={() => setSearchTerm('')}
                className="mt-2 admin-btn admin-btn-outline"
              >
                Сбросить поиск
              </button>
            )}
          </div>
        )}
      </div>

      {/* User Details Modal */}
      {showUserModal && selectedUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-screen overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <h3 className="text-xl font-semibold">Детали пользователя</h3>
                <button
                  onClick={() => setShowUserModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
            </div>
            
            <div className="p-6 space-y-6">
              {/* User Info */}
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Основная информация</h4>
                  <div className="space-y-2 text-sm">
                    <div><strong>Имя:</strong> {selectedUser.first_name}</div>
                    <div><strong>Фамилия:</strong> {selectedUser.last_name}</div>
                    <div><strong>Username:</strong> @{selectedUser.username}</div>
                    <div><strong>Telegram ID:</strong> {selectedUser.telegram_id}</div>
                    <div><strong>Язык:</strong> {selectedUser.language.toUpperCase()}</div>
                    <div><strong>Тема:</strong> {selectedUser.theme}</div>
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Активность</h4>
                  <div className="space-y-2 text-sm">
                    <div><strong>Статус:</strong> 
                      <span className={`ml-2 admin-badge ${
                        selectedUser.is_active ? 'admin-badge-success' : 'admin-badge-danger'
                      }`}>
                        {selectedUser.is_active ? 'Активен' : 'Неактивен'}
                      </span>
                    </div>
                    <div><strong>Объявлений:</strong> {selectedUser.posts_count}</div>
                    <div><strong>Регистрация:</strong> {formatDate(selectedUser.created_at)}</div>
                    <div><strong>Последняя активность:</strong> {formatDate(selectedUser.last_activity)}</div>
                  </div>
                </div>
              </div>
              
              {/* Actions */}
              <div className="border-t pt-4">
                <h4 className="font-medium text-gray-900 mb-3">Действия</h4>
                <div className="flex space-x-3">
                  <button
                    onClick={() => handleUserStatusToggle(selectedUser.id)}
                    className={`admin-btn ${
                      selectedUser.is_active ? 'admin-btn-danger' : 'admin-btn-success'
                    }`}
                  >
                    {selectedUser.is_active ? 'Заблокировать пользователя' : 'Активировать пользователя'}
                  </button>
                  <button className="admin-btn admin-btn-outline">
                    Просмотреть объявления
                  </button>
                  <button className="admin-btn admin-btn-secondary">
                    Отправить сообщение
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UsersPage;