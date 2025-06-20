import React, { useState, useEffect } from 'react';

const ProfileModal = ({ isOpen, onClose, user, cities }) => {
  const [activeTab, setActiveTab] = useState('published');
  const [userPosts, setUserPosts] = useState([]);
  const [loading, setLoading] = useState(false);

  // Mock user posts data
  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      // Simulate API call
      setTimeout(() => {
        setUserPosts([
          {
            id: '1',
            title: "I'm looking for a designer",
            status: 'active',
            views: 1000,
            created_at: new Date().toISOString()
          },
          {
            id: '2',
            title: "I'm looking for a manager",
            status: 'active',
            views: 1000,
            created_at: new Date().toISOString()
          },
          {
            id: '3',
            title: "I'm looking for a developer",
            status: 'moderation',
            views: 0,
            created_at: new Date().toISOString()
          }
        ]);
        setLoading(false);
      }, 1000);
    }
  }, [isOpen]);

  const tabs = [
    { id: 'published', label: 'Published', count: userPosts.filter(p => p.status === 'active').length },
    { id: 'moderation', label: 'Moderation', count: userPosts.filter(p => p.status === 'moderation').length },
    { id: 'archive', label: 'Archive', count: 0 },
    { id: 'blocked', label: 'Blocked', count: 0 }
  ];

  const getFilteredPosts = () => {
    return userPosts.filter(post => {
      switch (activeTab) {
        case 'published':
          return post.status === 'active';
        case 'moderation':
          return post.status === 'moderation';
        case 'archive':
          return post.status === 'archived';
        case 'blocked':
          return post.status === 'blocked';
        default:
          return true;
      }
    });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg w-full max-w-md max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-white border-b px-6 py-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Profile</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-xl"
            >
              ←
            </button>
          </div>
        </div>

        {/* User Info */}
        <div className="p-6 text-center border-b">
          <div className="w-20 h-20 bg-orange-100 rounded-full mx-auto mb-4 flex items-center justify-center">
            <span className="text-2xl">👤</span>
          </div>
          <h3 className="text-xl font-semibold text-gray-900">{user.first_name}</h3>
          <p className="text-gray-600">@{user.username}</p>
          <p className="text-sm text-gray-500 mt-1">Joined in 2022</p>
        </div>

        {/* Tabs */}
        <div className="border-b">
          <div className="flex overflow-x-auto">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-shrink-0 px-4 py-3 text-sm font-medium border-b-2 ${
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

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <div className="p-4 space-y-3">
              {getFilteredPosts().length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-gray-500">Нет объявлений</p>
                </div>
              ) : (
                getFilteredPosts().map(post => (
                  <div key={post.id} className="bg-white border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start space-x-3">
                      <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
                        <span className="text-lg">🌿</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="text-sm font-medium text-gray-900 truncate">
                          {post.title}
                        </h4>
                        <div className="flex items-center text-xs text-gray-500 mt-1 space-x-3">
                          <span>{post.views} • {post.views}</span>
                          <span>
                            {new Date(post.created_at).toLocaleDateString('ru-RU')}
                          </span>
                        </div>
                        
                        {post.status === 'moderation' && (
                          <div className="mt-2">
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                              На модерации
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        {/* Bottom Navigation */}
        <div className="border-t bg-gray-50 p-4">
          <div className="flex justify-around">
            <button className="flex flex-col items-center text-xs text-blue-600">
              <span className="text-lg mb-1">🏠</span>
              Главная
            </button>
            <button className="flex flex-col items-center text-xs text-gray-500">
              <span className="text-lg mb-1">❤️</span>
              Избранное
            </button>
            <button className="flex flex-col items-center text-xs text-gray-500">
              <span className="text-lg mb-1">➕</span>
              Создать
            </button>
            <button className="flex flex-col items-center text-xs text-gray-500">
              <span className="text-lg mb-1">💼</span>
              Мои объявления
            </button>
            <button className="flex flex-col items-center text-xs text-gray-500">
              <span className="text-lg mb-1">👤</span>
              Профиль
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfileModal;