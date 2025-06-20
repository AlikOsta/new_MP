import React, { useState, useEffect } from 'react';
import * as apiService from '../services/api';

const ProfilePage = ({ user, cities, onUpdateUser }) => {
  const [activeTab, setActiveTab] = useState('published');
  const [userPosts, setUserPosts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showEditProfile, setShowEditProfile] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  const [editForm, setEditForm] = useState({
    first_name: user.first_name || '',
    last_name: user.last_name || '',
    phone: user.phone || '',
    city_id: user.city_id || '',
    photo_url: user.photo_url || ''
  });

  const [settings, setSettings] = useState({
    language: user.language || 'ru',
    theme: user.theme || 'light'
  });

  useEffect(() => {
    loadUserPosts();
  }, [activeTab, user.id]);

  const loadUserPosts = async () => {
    setLoading(true);
    try {
      // Загружаем все посты пользователя
      const allPosts = await apiService.getPosts({ author_id: user.id });
      
      // Фильтруем по статусам
      let filteredPosts = [];
      switch (activeTab) {
        case 'published':
          filteredPosts = allPosts.filter(post => post.status === 3); // Active
          break;
        case 'moderation':
          filteredPosts = allPosts.filter(post => post.status === 2); // Moderation
          break;
        case 'archive':
          filteredPosts = allPosts.filter(post => post.status === 5); // Archived
          break;
        case 'blocked':
          filteredPosts = allPosts.filter(post => post.status === 4); // Blocked
          break;
        default:
          filteredPosts = allPosts;
      }
      
      setUserPosts(filteredPosts);
    } catch (error) {
      console.error('Error loading user posts:', error);
      setUserPosts([]);
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'published', label: 'Опубликовано', count: userPosts.filter(p => p.status === 3).length },
    { id: 'moderation', label: 'На модерации', count: userPosts.filter(p => p.status === 2).length },
    { id: 'archive', label: 'Архив', count: userPosts.filter(p => p.status === 5).length },
    { id: 'blocked', label: 'Заблокированные', count: userPosts.filter(p => p.status === 4).length }
  ];

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    try {
      await apiService.updateUser(user.id, editForm);
      onUpdateUser({ ...user, ...editForm });
      setShowEditProfile(false);
      alert('Профиль обновлен');
    } catch (error) {
      console.error('Error updating profile:', error);
      alert('Ошибка при обновлении профиля');
    }
  };

  const handleSettingsSubmit = async (e) => {
    e.preventDefault();
    try {
      await apiService.updateUser(user.id, settings);
      onUpdateUser({ ...user, ...settings });
      setShowSettings(false);
      
      // Применяем тему
      document.documentElement.setAttribute('data-theme', settings.theme);
      
      alert('Настройки сохранены');
    } catch (error) {
      console.error('Error updating settings:', error);
      alert('Ошибка при сохранении настроек');
    }
  };

  const getCityName = (cityId) => {
    const city = cities.find(c => c.id === cityId);
    return city?.name_ru || 'Не указан';
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('ru-RU');
  };

  const getStatusBadge = (status) => {
    const badges = {
      1: { label: 'Черновик', color: 'bg-gray-100 text-gray-800' },
      2: { label: 'На модерации', color: 'bg-yellow-100 text-yellow-800' },
      3: { label: 'Опубликовано', color: 'bg-green-100 text-green-800' },
      4: { label: 'Заблокировано', color: 'bg-red-100 text-red-800' },
      5: { label: 'В архиве', color: 'bg-gray-100 text-gray-800' }
    };
    
    const badge = badges[status] || badges[1];
    return (
      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${badge.color}`}>
        {badge.label}
      </span>
    );
  };

  if (showEditProfile) {
    return (
      <div className="max-w-md mx-auto">
        <div className="flex items-center mb-6">
          <button 
            onClick={() => setShowEditProfile(false)}
            className="mr-4 text-blue-600"
          >
            ← Назад
          </button>
          <h1 className="text-2xl font-bold">Редактировать профиль</h1>
        </div>

        <form onSubmit={handleEditSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Имя *
            </label>
            <input
              type="text"
              value={editForm.first_name}
              onChange={(e) => setEditForm(prev => ({ ...prev, first_name: e.target.value }))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Фамилия
            </label>
            <input
              type="text"
              value={editForm.last_name}
              onChange={(e) => setEditForm(prev => ({ ...prev, last_name: e.target.value }))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Телефон
            </label>
            <input
              type="tel"
              value={editForm.phone}
              onChange={(e) => setEditForm(prev => ({ ...prev, phone: e.target.value }))}
              placeholder="+7 (999) 123-45-67"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Город
            </label>
            <select
              value={editForm.city_id}
              onChange={(e) => setEditForm(prev => ({ ...prev, city_id: e.target.value }))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Выберите город</option>
              {cities.map(city => (
                <option key={city.id} value={city.id}>
                  {city.name_ru}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Фото профиля
            </label>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-4">
              {editForm.photo_url ? (
                <div className="relative">
                  <img src={editForm.photo_url} alt="Profile" className="w-20 h-20 object-cover rounded-full mx-auto" />
                  <button
                    type="button"
                    onClick={() => setEditForm(prev => ({ ...prev, photo_url: '' }))}
                    className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm"
                  >
                    ✕
                  </button>
                </div>
              ) : (
                <div className="text-center">
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => {
                      const file = e.target.files[0];
                      if (file) {
                        const url = URL.createObjectURL(file);
                        setEditForm(prev => ({ ...prev, photo_url: url }));
                      }
                    }}
                    className="hidden"
                    id="photo-upload"
                  />
                  <label htmlFor="photo-upload" className="cursor-pointer">
                    <div className="text-4xl mb-2">👤</div>
                    <div className="text-sm text-gray-600">
                      <p>Нажмите для выбора фото</p>
                    </div>
                  </label>
                </div>
              )}
            </div>
          </div>

          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={() => setShowEditProfile(false)}
              className="flex-1 py-3 px-4 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              Отмена
            </button>
            <button
              type="submit"
              className="flex-1 py-3 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Сохранить
            </button>
          </div>
        </form>
      </div>
    );
  }

  if (showSettings) {
    return (
      <div className="max-w-md mx-auto">
        <div className="flex items-center mb-6">
          <button 
            onClick={() => setShowSettings(false)}
            className="mr-4 text-blue-600"
          >
            ← Назад
          </button>
          <h1 className="text-2xl font-bold">Настройки</h1>
        </div>

        <form onSubmit={handleSettingsSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Язык
            </label>
            <div className="space-y-2">
              <label className="flex items-center">
                <input
                  type="radio"
                  name="language"
                  value="ru"
                  checked={settings.language === 'ru'}
                  onChange={(e) => setSettings(prev => ({ ...prev, language: e.target.value }))}
                  className="mr-3"
                />
                Русский
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="language"
                  value="ua"
                  checked={settings.language === 'ua'}
                  onChange={(e) => setSettings(prev => ({ ...prev, language: e.target.value }))}
                  className="mr-3"
                />
                Українська
              </label>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Цветовая схема
            </label>
            <div className="space-y-2">
              <label className="flex items-center">
                <input
                  type="radio"
                  name="theme"
                  value="light"
                  checked={settings.theme === 'light'}
                  onChange={(e) => setSettings(prev => ({ ...prev, theme: e.target.value }))}
                  className="mr-3"
                />
                ☀️ Светлая
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="theme"
                  value="dark"
                  checked={settings.theme === 'dark'}
                  onChange={(e) => setSettings(prev => ({ ...prev, theme: e.target.value }))}
                  className="mr-3"
                />
                🌙 Темная
              </label>
            </div>
          </div>

          <div className="pt-4 border-t">
            <button
              type="button"
              onClick={() => window.open('https://t.me/support', '_blank')}
              className="w-full py-3 px-4 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center justify-center"
            >
              📞 Связаться с поддержкой
            </button>
          </div>

          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={() => setShowSettings(false)}
              className="flex-1 py-3 px-4 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              Отмена
            </button>
            <button
              type="submit"
              className="flex-1 py-3 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Сохранить
            </button>
          </div>
        </form>
      </div>
    );
  }

  return (
    <div>
      {/* User Info Header */}
      <div className="text-center mb-6">
        <div className="w-20 h-20 bg-orange-100 rounded-full mx-auto mb-4 flex items-center justify-center overflow-hidden">
          {editForm.photo_url ? (
            <img src={editForm.photo_url} alt="Profile" className="w-full h-full object-cover" />
          ) : (
            <span className="text-2xl">👤</span>
          )}
        </div>
        <h3 className="text-xl font-semibold text-gray-900">
          {user.first_name} {user.last_name || ''}
        </h3>
        <p className="text-gray-600">@{user.username}</p>
        <p className="text-sm text-gray-500 mt-1">{getCityName(user.city_id)}</p>
        
        <div className="flex space-x-3 mt-4">
          <button
            onClick={() => setShowEditProfile(true)}
            className="flex-1 py-2 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Редактировать
          </button>
          <button
            onClick={() => setShowSettings(true)}
            className="flex-1 py-2 px-4 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
          >
            Настройки
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b mb-4">
        <div className="flex overflow-x-auto">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-shrink-0 px-4 py-3 text-sm font-medium border-b-2 whitespace-nowrap ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.label}
              {tab.count > 0 && (
                <span className="ml-1 bg-gray-200 text-gray-600 px-2 py-0.5 rounded-full text-xs">
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Posts Content */}
      <div>
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : userPosts.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">Нет объявлений</p>
          </div>
        ) : (
          <div className="space-y-3">
            {userPosts.map(post => (
              <div key={post.id} className="bg-white border border-gray-200 rounded-lg p-4">
                <div className="flex items-start space-x-3">
                  <div className="w-16 h-16 bg-gray-100 rounded-lg flex items-center justify-center flex-shrink-0">
                    {post.image_url ? (
                      <img src={post.image_url} alt={post.title} className="w-full h-full object-cover rounded-lg" />
                    ) : (
                      <span className="text-lg">📋</span>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between">
                      <h4 className="text-sm font-medium text-gray-900 truncate">
                        {post.title}
                      </h4>
                      {getStatusBadge(post.status)}
                    </div>
                    
                    <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                      {post.description}
                    </p>
                    
                    <div className="flex items-center justify-between text-xs text-gray-500 mt-2">
                      <span>
                        {post.price ? `${post.price} ₽` : 'Договорная'}
                      </span>
                      <div className="flex items-center space-x-3">
                        <span>👁️ {post.views_count || 0}</span>
                        <span>{formatDate(post.created_at)}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ProfilePage;