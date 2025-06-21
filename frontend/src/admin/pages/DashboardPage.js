import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

const DashboardPage = () => {
  const [stats, setStats] = useState({
    users: { total: 0, new_7d: 0, new_30d: 0 },
    posts: { total: 0, active: 0, new_7d: 0, new_30d: 0 }
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('admin_token');
      
      const [userStatsRes, postStatsRes] = await Promise.all([
        fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/stats/users`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/stats/posts`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);

      const userStats = await userStatsRes.json();
      const postStats = await postStatsRes.json();

      setStats({
        users: userStats,
        posts: postStats
      });
    } catch (err) {
      setError('Ошибка загрузки данных');
      console.error('Dashboard data loading error:', err);
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
          onClick={loadDashboardData}
          className="mt-2 admin-btn admin-btn-primary"
        >
          Попробовать снова
        </button>
      </div>
    );
  }

  // Sample chart data
  const userGrowthData = stats.users.daily_users || [
    { date: '2024-01-01', count: 5 },
    { date: '2024-01-02', count: 8 },
    { date: '2024-01-03', count: 12 },
    { date: '2024-01-04', count: 15 },
    { date: '2024-01-05', count: 20 },
    { date: '2024-01-06', count: 18 },
    { date: '2024-01-07', count: 25 }
  ];

  const postTypesData = [
    { name: 'Работа', value: stats.posts.posts_by_type?.job || 0 },
    { name: 'Услуги', value: stats.posts.posts_by_type?.service || 0 }
  ];

  return (
    <div className="space-y-6">
      {/* Welcome Message */}
      <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg p-6 text-white">
        <h1 className="text-2xl font-bold mb-2">Добро пожаловать в админ панель!</h1>
        <p className="text-blue-100">Управляйте платформой Telegram Marketplace</p>
      </div>

      {/* Stats Grid */}
      <div className="dashboard-grid">
        {/* Total Users */}
        <div className="stat-card">
          <div className="stat-card-icon bg-blue-100">
            <span className="text-blue-600">👥</span>
          </div>
          <div className="stat-card-value text-blue-600">
            {(stats.users.total || 0).toLocaleString()}
          </div>
          <div className="stat-card-label">Всего пользователей</div>
          <div className="stat-card-change positive">
            +{stats.users.new_7d || 0} за неделю
          </div>
        </div>

        {/* Active Posts */}
        <div className="stat-card">
          <div className="stat-card-icon bg-green-100">
            <span className="text-green-600">📝</span>
          </div>
          <div className="stat-card-value text-green-600">
            {(stats.posts.active || 0).toLocaleString()}
          </div>
          <div className="stat-card-label">Активных объявлений</div>
          <div className="stat-card-change positive">
            +{stats.posts.new_7d || 0} за неделю
          </div>
        </div>

        {/* Total Posts */}
        <div className="stat-card">
          <div className="stat-card-icon bg-purple-100">
            <span className="text-purple-600">📊</span>
          </div>
          <div className="stat-card-value text-purple-600">
            {(stats.posts.total || 0).toLocaleString()}
          </div>
          <div className="stat-card-label">Всего объявлений</div>
          <div className="stat-card-change positive">
            +{stats.posts.new_30d || 0} за месяц
          </div>
        </div>

        {/* New Users 30d */}
        <div className="stat-card">
          <div className="stat-card-icon bg-orange-100">
            <span className="text-orange-600">🆕</span>
          </div>
          <div className="stat-card-value text-orange-600">
            {(stats.users.new_30d || 0).toLocaleString()}
          </div>
          <div className="stat-card-label">Новых пользователей за месяц</div>
          <div className="stat-card-change positive">
            Рост активности
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* User Growth Chart */}
        <div className="chart-container">
          <h3 className="chart-title">Рост пользователей (последние 7 дней)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={userGrowthData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="date" 
                tickFormatter={(value) => new Date(value).toLocaleDateString('ru-RU', { month: 'short', day: 'numeric' })}
              />
              <YAxis />
              <Tooltip 
                labelFormatter={(value) => new Date(value).toLocaleDateString('ru-RU')}
                formatter={(value) => [`${value} пользователей`, 'Новые регистрации']}
              />
              <Line 
                type="monotone" 
                dataKey="count" 
                stroke="#3b82f6" 
                strokeWidth={2}
                dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Post Types Chart */}
        <div className="chart-container">
          <h3 className="chart-title">Объявления по типам</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={postTypesData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip formatter={(value) => [`${value} объявлений`, 'Количество']} />
              <Bar dataKey="value" fill="#10b981" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Быстрые действия</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <button className="admin-btn admin-btn-primary flex flex-col items-center p-4">
            <span className="text-2xl mb-2">👥</span>
            <span>Пользователи</span>
          </button>
          <button className="admin-btn admin-btn-secondary flex flex-col items-center p-4">
            <span className="text-2xl mb-2">📝</span>
            <span>Объявления</span>
          </button>
          <button className="admin-btn admin-btn-success flex flex-col items-center p-4">
            <span className="text-2xl mb-2">📊</span>
            <span>Статистика</span>
          </button>
          <button className="admin-btn admin-btn-outline flex flex-col items-center p-4">
            <span className="text-2xl mb-2">⚙️</span>
            <span>Настройки</span>
          </button>
        </div>
      </div>

      {/* Popular Posts */}
      {stats.posts.popular_posts && stats.posts.popular_posts.length > 0 && (
        <div className="data-table">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Популярные объявления</h3>
          </div>
          <table>
            <thead>
              <tr>
                <th>Название</th>
                <th>Просмотры</th>
                <th>Избранное</th>
                <th>Автор</th>
              </tr>
            </thead>
            <tbody>
              {stats.posts.popular_posts.slice(0, 5).map((post) => (
                <tr key={post.id}>
                  <td className="font-medium">{post.title}</td>
                  <td>
                    <span className="admin-badge admin-badge-info">
                      {post.views_count} просмотров
                    </span>
                  </td>
                  <td>
                    <span className="admin-badge admin-badge-success">
                      {post.favorites_count} ❤️
                    </span>
                  </td>
                  <td className="text-gray-500">{post.author_id}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default DashboardPage;