import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

const AdminSidebar = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const menuItems = [
    {
      path: '/admin/dashboard',
      name: 'Дашборд',
      icon: '📊',
      description: 'Главная панель'
    },
    {
      path: '/admin/statistics',
      name: 'Статистика',
      icon: '📈',
      description: 'Аналитика и графики'
    },
    {
      path: '/admin/users',
      name: 'Пользователи',
      icon: '👥',
      description: 'Управление пользователями'
    },
    {
      path: '/admin/posts',
      name: 'Объявления',
      icon: '📝',
      description: 'Управление объявлениями'
    },
    {
      path: '/admin/categories',
      name: 'Категории',
      icon: '📂',
      description: 'Управление категориями'
    },
    {
      path: '/admin/cities',
      name: 'Города',
      icon: '🏙️',
      description: 'Управление городами'
    },
    {
      path: '/admin/currencies',
      name: 'Валюты',
      icon: '💰',
      description: 'Управление валютами'
    },
    {
      path: '/admin/packages',
      name: 'Тарифы',
      icon: '💎',
      description: 'Управление тарифами'
    },
    {
      path: '/admin/settings',
      name: 'Настройки',
      icon: '⚙️',
      description: 'Настройки системы'
    }
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <div className="w-64 bg-white shadow-lg h-screen flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
            <span className="text-white text-xl">⚡</span>
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">Admin Panel</h1>
            <p className="text-xs text-gray-500">Telegram Marketplace</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4">
        <div className="space-y-1 px-3">
          {menuItems.map((item) => (
            <button
              key={item.path}
              onClick={() => navigate(item.path)}
              className={`w-full flex items-center px-3 py-3 text-left rounded-lg transition-all duration-200 group ${
                isActive(item.path)
                  ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-700'
                  : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
              }`}
            >
              <span className="text-xl mr-3 flex-shrink-0">{item.icon}</span>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium truncate">{item.name}</div>
                <div className="text-xs text-gray-500 truncate">{item.description}</div>
              </div>
              {isActive(item.path) && (
                <div className="w-2 h-2 bg-blue-600 rounded-full flex-shrink-0"></div>
              )}
            </button>
          ))}
        </div>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200">
        <div className="text-xs text-gray-500 text-center">
          <p>Version 1.0.0</p>
          <p>© 2024 Telegram Marketplace</p>
        </div>
      </div>
    </div>
  );
};

export default AdminSidebar;