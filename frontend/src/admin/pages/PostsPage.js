import React, { useState, useEffect } from 'react';

const PostsPage = () => {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [selectedPost, setSelectedPost] = useState(null);
  const [showPostModal, setShowPostModal] = useState(false);

  useEffect(() => {
    loadPosts();
  }, []);

  const loadPosts = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/posts/`);
      const data = await response.json();
      setPosts(data);
    } catch (err) {
      setError('Ошибка загрузки объявлений');
      console.error('Posts loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredPosts = posts.filter(post => {
    const matchesSearch = !searchTerm || 
      post.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      post.description.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesType = filterType === 'all' || post.post_type === filterType;
    
    const matchesStatus = filterStatus === 'all' || 
      (filterStatus === 'active' && post.status === 3) ||  // Active
      (filterStatus === 'draft' && post.status === 1) ||   // Draft
      (filterStatus === 'moderation' && post.status === 2) || // Moderation
      (filterStatus === 'rejected' && post.status === 4) || // Rejected
      (filterStatus === 'archived' && post.status === 5);   // Archived
    
    return matchesSearch && matchesType && matchesStatus;
  });

  const handlePostClick = (post) => {
    setSelectedPost(post);
    setShowPostModal(true);
  };

  const handlePostStatusChange = async (postId, newStatus) => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/posts/${postId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus }),
      });

      if (response.ok) {
        setPosts(posts.map(post => 
          post.id === postId 
            ? { ...post, status: newStatus }
            : post
        ));
      }
    } catch (err) {
      console.error('Error updating post status:', err);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 1:
        return <span className="admin-badge admin-badge-warning">Черновик</span>;
      case 2:
        return <span className="admin-badge admin-badge-info">Модерация</span>;
      case 3:
        return <span className="admin-badge admin-badge-success">Активно</span>;
      case 4:
        return <span className="admin-badge admin-badge-danger">Отклонено</span>;
      case 5:
        return <span className="admin-badge admin-badge-secondary">Архив</span>;
      default:
        return <span className="admin-badge admin-badge-info">Неизвестно</span>;
    }
  };

  const getTypeIcon = (type) => {
    return type === 'job' ? '💼' : '🛠️';
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
          onClick={loadPosts}
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
        <h1 className="text-2xl font-bold text-gray-900">Управление объявлениями</h1>
        <div className="text-sm text-gray-500">
          Всего: {posts.length} объявлений
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="admin-form-label">Поиск</label>
            <input
              type="text"
              placeholder="Название или описание"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="admin-form-input"
            />
          </div>
          <div>
            <label className="admin-form-label">Тип</label>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="admin-form-select"
            >
              <option value="all">Все типы</option>
              <option value="job">Работа</option>
              <option value="service">Услуги</option>
            </select>
          </div>
          <div>
            <label className="admin-form-label">Статус</label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="admin-form-select"
            >
              <option value="all">Все статусы</option>
              <option value="active">Активные</option>
              <option value="moderation">На модерации</option>
              <option value="draft">Черновики</option>
              <option value="rejected">Отклоненные</option>
              <option value="archived">Архив</option>
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={() => {
                setSearchTerm('');
                setFilterType('all');
                setFilterStatus('all');
              }}
              className="admin-btn admin-btn-outline w-full"
            >
              Сбросить фильтры
            </button>
          </div>
        </div>
      </div>

      {/* Posts Table */}
      <div className="data-table">
        <div className="p-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            Объявления ({filteredPosts.length})
          </h3>
        </div>
        <table>
          <thead>
            <tr>
              <th>Объявление</th>
              <th>Тип</th>
              <th>Статус</th>
              <th>Автор</th>
              <th>Просмотры</th>
              <th>Создано</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            {filteredPosts.map((post) => (
              <tr key={post.id}>
                <td>
                  <div 
                    className="cursor-pointer hover:text-blue-600"
                    onClick={() => handlePostClick(post)}
                  >
                    <div className="font-medium">{post.title}</div>
                    <div className="text-sm text-gray-500 truncate max-w-xs">
                      {post.description}
                    </div>
                  </div>
                </td>
                <td>
                  <div className="flex items-center space-x-2">
                    <span className="text-lg">{getTypeIcon(post.post_type)}</span>
                    <span className="capitalize">
                      {post.post_type === 'job' ? 'Работа' : 'Услуги'}
                    </span>
                  </div>
                </td>
                <td>{getStatusBadge(post.status)}</td>
                <td className="text-sm text-gray-500">{post.author_id}</td>
                <td>
                  <span className="admin-badge admin-badge-info">
                    {post.views_count || 0}
                  </span>
                </td>
                <td className="text-sm text-gray-500">
                  {formatDate(post.created_at)}
                </td>
                <td>
                  <div className="flex space-x-2">
                    {post.status === 2 && (
                      <>
                        <button
                          onClick={() => handlePostStatusChange(post.id, 3)}
                          className="admin-btn admin-btn-success text-xs"
                        >
                          Одобрить
                        </button>
                        <button
                          onClick={() => handlePostStatusChange(post.id, 4)}
                          className="admin-btn admin-btn-danger text-xs"
                        >
                          Отклонить
                        </button>
                      </>
                    )}
                    {post.status === 3 && (
                      <button
                        onClick={() => handlePostStatusChange(post.id, 4)}
                        className="admin-btn admin-btn-danger text-xs"
                      >
                        Заблокировать
                      </button>
                    )}
                    <button
                      onClick={() => handlePostClick(post)}
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
        
        {filteredPosts.length === 0 && (
          <div className="p-8 text-center text-gray-500">
            <div className="text-4xl mb-2">📝</div>
            <p>Объявления не найдены</p>
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

      {/* Post Details Modal */}
      {showPostModal && selectedPost && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-screen overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <h3 className="text-xl font-semibold">Детали объявления</h3>
                <button
                  onClick={() => setShowPostModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
            </div>
            
            <div className="p-6 space-y-6">
              {/* Post Info */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Основная информация</h4>
                  <div className="space-y-3">
                    <div>
                      <label className="text-sm text-gray-500">Название</label>
                      <div className="font-medium">{selectedPost.title}</div>
                    </div>
                    <div>
                      <label className="text-sm text-gray-500">Описание</label>
                      <div className="text-sm text-gray-700">{selectedPost.description}</div>
                    </div>
                    <div>
                      <label className="text-sm text-gray-500">Тип</label>
                      <div className="flex items-center space-x-2">
                        <span>{getTypeIcon(selectedPost.post_type)}</span>
                        <span>{selectedPost.post_type === 'job' ? 'Работа' : 'Услуги'}</span>
                      </div>
                    </div>
                    {selectedPost.price && (
                      <div>
                        <label className="text-sm text-gray-500">Цена</label>
                        <div className="font-medium">
                          {selectedPost.price} {selectedPost.currency_code || 'RUB'}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Статистика</h4>
                  <div className="space-y-3">
                    <div>
                      <label className="text-sm text-gray-500">Статус</label>
                      <div>{getStatusBadge(selectedPost.status)}</div>
                    </div>
                    <div>
                      <label className="text-sm text-gray-500">Просмотры</label>
                      <div className="font-medium">{selectedPost.views_count || 0}</div>
                    </div>
                    <div>
                      <label className="text-sm text-gray-500">Автор</label>
                      <div className="text-sm">{selectedPost.author_id}</div>
                    </div>
                    <div>
                      <label className="text-sm text-gray-500">Создано</label>
                      <div className="text-sm">{formatDate(selectedPost.created_at)}</div>
                    </div>
                    <div>
                      <label className="text-sm text-gray-500">Обновлено</label>
                      <div className="text-sm">{formatDate(selectedPost.updated_at)}</div>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Actions */}
              <div className="border-t pt-4">
                <h4 className="font-medium text-gray-900 mb-3">Действия модератора</h4>
                <div className="flex space-x-3">
                  {selectedPost.status === 2 && (
                    <>
                      <button
                        onClick={() => {
                          handlePostStatusChange(selectedPost.id, 3);
                          setShowPostModal(false);
                        }}
                        className="admin-btn admin-btn-success"
                      >
                        Одобрить объявление
                      </button>
                      <button
                        onClick={() => {
                          handlePostStatusChange(selectedPost.id, 4);
                          setShowPostModal(false);
                        }}
                        className="admin-btn admin-btn-danger"
                      >
                        Отклонить объявление
                      </button>
                    </>
                  )}
                  {selectedPost.status === 3 && (
                    <button
                      onClick={() => {
                        handlePostStatusChange(selectedPost.id, 4);
                        setShowPostModal(false);
                      }}
                      className="admin-btn admin-btn-danger"
                    >
                      Заблокировать объявление
                    </button>
                  )}
                  {selectedPost.status === 4 && (
                    <button
                      onClick={() => {
                        handlePostStatusChange(selectedPost.id, 3);
                        setShowPostModal(false);
                      }}
                      className="admin-btn admin-btn-success"
                    >
                      Разблокировать объявление
                    </button>
                  )}
                  <button className="admin-btn admin-btn-outline">
                    Связаться с автором
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

export default PostsPage;