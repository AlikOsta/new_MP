import React, { useState, useEffect } from 'react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, PieChart, Pie, Cell, AreaChart, Area 
} from 'recharts';

const StatisticsPage = () => {
  const [userStats, setUserStats] = useState(null);
  const [postStats, setPostStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeRange, setTimeRange] = useState('7d');

  useEffect(() => {
    loadStatistics();
  }, [timeRange]);

  const loadStatistics = async () => {
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

      const userStatsData = await userStatsRes.json();
      const postStatsData = await postStatsRes.json();

      setUserStats(userStatsData);
      setPostStats(postStatsData);
    } catch (err) {
      setError('Ошибка загрузки статистики');
      console.error('Statistics loading error:', err);
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
          onClick={loadStatistics}
          className="mt-2 admin-btn admin-btn-primary"
        >
          Попробовать снова
        </button>
      </div>
    );
  }

  // Use only real data for charts
  const userGrowthData = userStats?.daily_users || [];

  const postTypesData = postStats?.posts_by_type ? [
    { name: 'Работа', value: postStats.posts_by_type.job || 0, color: '#3b82f6' },
    { name: 'Услуги', value: postStats.posts_by_type.service || 0, color: '#10b981' }
  ] : [];

  const postStatusData = [
    { status: 'Активные', count: postStats?.active_posts || 0 },
    { status: 'Всего', count: postStats?.total_posts || 0 }
  ];

  return (
    <div className="space-y-6">
      {/* Header with Time Range Selector */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-2xl font-bold text-gray-900">Детальная статистика</h1>
          <div className="flex space-x-2">
            {['7d', '30d', '90d'].map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={`px-3 py-1 rounded text-sm font-medium ${
                  timeRange === range
                    ? 'bg-blue-100 text-blue-700 border border-blue-300'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {range === '7d' ? '7 дней' : range === '30d' ? '30 дней' : '90 дней'}
              </button>
            ))}
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">
              {userStats?.total_users || 0}
            </div>
            <div className="text-sm text-blue-800">Всего пользователей</div>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">
              {postStats?.total_posts || 0}
            </div>
            <div className="text-sm text-green-800">Всего объявлений</div>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">
              {postStats?.active_posts || 0}
            </div>
            <div className="text-sm text-purple-800">Активных объявлений</div>
          </div>
          <div className="text-center p-4 bg-orange-50 rounded-lg">
            <div className="text-2xl font-bold text-orange-600">
              {((postStats?.active_posts / postStats?.total_posts) * 100 || 0).toFixed(1)}%
            </div>
            <div className="text-sm text-orange-800">Активность</div>
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* User Growth Chart */}
        <div className="chart-container">
          <h3 className="chart-title">Рост пользователей</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={userGrowthData}>
              <defs>
                <linearGradient id="colorUsers" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.1}/>
                </linearGradient>
                <linearGradient id="colorActive" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0.1}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="date" 
                tickFormatter={(value) => new Date(value).toLocaleDateString('ru-RU', { month: 'short', day: 'numeric' })}
              />
              <YAxis />
              <Tooltip 
                labelFormatter={(value) => new Date(value).toLocaleDateString('ru-RU')}
              />
              <Area 
                type="monotone" 
                dataKey="users" 
                stackId="1"
                stroke="#3b82f6" 
                fillOpacity={1} 
                fill="url(#colorUsers)" 
                name="Всего пользователей"
              />
              <Area 
                type="monotone" 
                dataKey="active" 
                stackId="2"
                stroke="#10b981" 
                fillOpacity={1} 
                fill="url(#colorActive)" 
                name="Активные пользователи"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Post Types Distribution */}
        <div className="chart-container">
          <h3 className="chart-title">Распределение по типам объявлений</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={postTypesData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {postTypesData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => [`${value} объявлений`, 'Количество']} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Post Status Chart */}
        <div className="chart-container">
          <h3 className="chart-title">Статусы объявлений</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={postStatusData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="status" />
              <YAxis />
              <Tooltip formatter={(value) => [`${value} объявлений`, 'Количество']} />
              <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Activity Heatmap Placeholder */}
        <div className="chart-container">
          <h3 className="chart-title">Активность по времени</h3>
          <div className="h-300 flex items-center justify-center bg-gray-50 rounded">
            <div className="text-center text-gray-500">
              <div className="text-4xl mb-2">📊</div>
              <p>Тепловая карта активности</p>
              <p className="text-sm">В разработке</p>
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Posts */}
        {postStats?.popular_posts && (
          <div className="data-table">
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Топ объявления</h3>
            </div>
            <table>
              <thead>
                <tr>
                  <th>Название</th>
                  <th>Просмотры</th>
                  <th>Избранное</th>
                </tr>
              </thead>
              <tbody>
                {postStats.popular_posts.slice(0, 5).map((post) => (
                  <tr key={post.id}>
                    <td className="font-medium">{post.title}</td>
                    <td>
                      <span className="admin-badge admin-badge-info">
                        {post.views_count}
                      </span>
                    </td>
                    <td>
                      <span className="admin-badge admin-badge-success">
                        {post.favorites_count}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Recent Activity */}
        <div className="data-table">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Последняя активность</h3>
          </div>
          <table>
            <thead>
              <tr>
                <th>Действие</th>
                <th>Время</th>
                <th>Статус</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Новое объявление создано</td>
                <td>5 мин назад</td>
                <td><span className="admin-badge admin-badge-success">Создано</span></td>
              </tr>
              <tr>
                <td>Пользователь зарегистрирован</td>
                <td>12 мин назад</td>
                <td><span className="admin-badge admin-badge-info">Активен</span></td>
              </tr>
              <tr>
                <td>Объявление отправлено на модерацию</td>
                <td>23 мин назад</td>
                <td><span className="admin-badge admin-badge-warning">Модерация</span></td>
              </tr>
              <tr>
                <td>Платеж обработан</td>
                <td>1 час назад</td>
                <td><span className="admin-badge admin-badge-success">Успешно</span></td>
              </tr>
              <tr>
                <td>Объявление заблокировано</td>
                <td>2 часа назад</td>
                <td><span className="admin-badge admin-badge-danger">Заблокировано</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default StatisticsPage;