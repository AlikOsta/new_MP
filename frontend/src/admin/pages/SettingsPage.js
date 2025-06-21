import React, { useState, useEffect } from 'react';

const SettingsPage = () => {
  const [settings, setSettings] = useState({
    app_name: '',
    app_description: '',
    show_view_counts: true,
    free_posts_per_week: 1,
    moderation_enabled: true,
    telegram_bot_token: '',
    mistral_api_key: ''
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [activeTab, setActiveTab] = useState('general');

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('admin_token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/settings`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setSettings(data);
    } catch (err) {
      setError('Ошибка загрузки настроек');
      console.error('Settings loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      setError(null);
      
      const token = localStorage.getItem('admin_token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/settings`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(settings)
      });

      if (response.ok) {
        setSuccess(true);
        setTimeout(() => setSuccess(false), 3000);
      } else {
        setError('Ошибка сохранения настроек');
      }
    } catch (err) {
      setError('Ошибка сохранения настроек');
      console.error('Settings saving error:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleInputChange = (key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  if (loading) {
    return (
      <div className="admin-loading">
        <div className="admin-spinner"></div>
      </div>
    );
  }

  const tabs = [
    { id: 'general', name: 'Основные', icon: '⚙️' },
    { id: 'features', name: 'Функции', icon: '🔧' },
    { id: 'integrations', name: 'Интеграции', icon: '🔗' }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Настройки системы</h1>
        <div className="flex space-x-2">
          {success && (
            <div className="bg-green-100 text-green-800 px-3 py-1 rounded text-sm">
              Настройки сохранены
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        <form onSubmit={handleSave} className="p-6">
          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
              {error}
            </div>
          )}

          {/* General Settings Tab */}
          {activeTab === 'general' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Общие настройки</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="admin-form-label">Название приложения</label>
                    <input
                      type="text"
                      value={settings.app_name}
                      onChange={(e) => handleInputChange('app_name', e.target.value)}
                      className="admin-form-input"
                      placeholder="Telegram Marketplace"
                    />
                  </div>
                  
                  <div>
                    <label className="admin-form-label">Описание приложения</label>
                    <input
                      type="text"
                      value={settings.app_description}
                      onChange={(e) => handleInputChange('app_description', e.target.value)}
                      className="admin-form-input"
                      placeholder="Платформа частных объявлений"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Features Tab */}
          {activeTab === 'features' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Настройки функций</h3>
                
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                    <div>
                      <h4 className="font-medium text-gray-900">Отображение просмотров</h4>
                      <p className="text-sm text-gray-500">Показывать количество просмотров объявлений</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={settings.show_view_counts}
                        onChange={(e) => handleInputChange('show_view_counts', e.target.checked)}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                  
                  <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                    <div>
                      <h4 className="font-medium text-gray-900">Модерация объявлений</h4>
                      <p className="text-sm text-gray-500">Включить модерацию новых объявлений</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={settings.moderation_enabled}
                        onChange={(e) => handleInputChange('moderation_enabled', e.target.checked)}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                  
                  <div className="p-4 border border-gray-200 rounded-lg">
                    <h4 className="font-medium text-gray-900 mb-2">Бесплатные объявления</h4>
                    <p className="text-sm text-gray-500 mb-3">Количество бесплатных объявлений в неделю</p>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={settings.free_posts_per_week}
                      onChange={(e) => handleInputChange('free_posts_per_week', parseInt(e.target.value))}
                      className="admin-form-input w-32"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Integrations Tab */}
          {activeTab === 'integrations' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Интеграции</h3>
                
                <div className="space-y-6">
                  <div className="p-4 border border-gray-200 rounded-lg">
                    <h4 className="font-medium text-gray-900 mb-2">Telegram Bot</h4>
                    <p className="text-sm text-gray-500 mb-3">Токен для интеграции с Telegram Bot API</p>
                    <input
                      type="password"
                      value={settings.telegram_bot_token}
                      onChange={(e) => handleInputChange('telegram_bot_token', e.target.value)}
                      className="admin-form-input"
                      placeholder="1234567890:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
                    />
                  </div>
                  
                  <div className="p-4 border border-gray-200 rounded-lg">
                    <h4 className="font-medium text-gray-900 mb-2">Mistral AI</h4>
                    <p className="text-sm text-gray-500 mb-3">API ключ для интеграции с Mistral AI</p>
                    <input
                      type="password"
                      value={settings.mistral_api_key}
                      onChange={(e) => handleInputChange('mistral_api_key', e.target.value)}
                      className="admin-form-input"
                      placeholder="xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Save Button */}
          <div className="border-t border-gray-200 pt-6">
            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={loadSettings}
                className="admin-btn admin-btn-outline"
                disabled={saving}
              >
                Сбросить
              </button>
              <button
                type="submit"
                className="admin-btn admin-btn-primary"
                disabled={saving}
              >
                {saving ? (
                  <div className="flex items-center">
                    <div className="admin-spinner mr-2 w-4 h-4"></div>
                    Сохранение...
                  </div>
                ) : (
                  'Сохранить настройки'
                )}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default SettingsPage;