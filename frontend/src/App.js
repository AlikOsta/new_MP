import React, { useState, useEffect } from 'react';
import './App.css';

// Components
import Header from './components/Header';
import CategoryTabs from './components/CategoryTabs';
import SearchBar from './components/SearchBar';
import PostCard from './components/PostCard';
import CreatePostModal from './components/CreatePostModal';
import ProfilePage from './components/ProfileModal';
import TariffsModal from './components/TariffsModal';
import PostDetails from './components/PostDetails';
import FavoritesPage from './components/FavoritesPage';

// Admin Panel
import AdminApp from './admin/AdminApp';

// Services
import * as apiService from './services/api';

function App() {
  // Check if this is admin route
  if (window.location.pathname.startsWith('/admin')) {
    return <AdminApp />;
  }
  const [posts, setPosts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [cities, setCities] = useState([]);
  const [currencies, setCurrencies] = useState([]);
  const [packages, setPackages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Current state
  const [activeTab, setActiveTab] = useState('job');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedCity, setSelectedCity] = useState('');
  const [filters, setFilters] = useState({});
  
  // Pages and modals
  const [currentPage, setCurrentPage] = useState('home'); // home, favorites, tariffs, profile
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedPost, setSelectedPost] = useState(null);
  const [favorites, setFavorites] = useState([]);
  
  // User data - simulate Telegram WebApp user
  const [currentUser, setCurrentUser] = useState(null);
  const [isAuthenticating, setIsAuthenticating] = useState(true);

  // Simulate Telegram WebApp authentication
  useEffect(() => {
    // Simulate checking Telegram WebApp InitData
    const initTelegramAuth = () => {
      setIsAuthenticating(true);
      
      // For demo purposes, simulate user from localStorage or create demo user
      const savedUser = localStorage.getItem('telegram_user');
      if (savedUser) {
        try {
          setCurrentUser(JSON.parse(savedUser));
        } catch (err) {
          console.error('Error parsing saved user:', err);
        }
      } else {
        // Create demo user for testing
        const demoUser = {
          id: '6855dc265afe51e45102bc68',
          telegram_id: 123456789,
          first_name: 'Alex',
          last_name: 'Smith',
          username: 'alex',
          language: 'ru',
          theme: 'light'
        };
        setCurrentUser(demoUser);
        localStorage.setItem('telegram_user', JSON.stringify(demoUser));
      }
      
      setIsAuthenticating(false);
    };

    // Simulate async auth check
    setTimeout(initTelegramAuth, 500);
  }, []);

  const handleTelegramAuth = () => {
    // In real app, this would trigger Telegram WebApp authorization
    alert('В реальном Telegram Mini App здесь будет авторизация через Telegram');
    
    // For demo, create a user
    const user = {
      id: '6855dc265afe51e45102bc68',
      telegram_id: Math.floor(Math.random() * 1000000000),
      first_name: 'User',
      last_name: 'Demo',
      username: 'demo_user',
      language: 'ru',
      theme: 'light'
    };
    
    setCurrentUser(user);
    localStorage.setItem('telegram_user', JSON.stringify(user));
  };

  const handleLogout = () => {
    setCurrentUser(null);
    localStorage.removeItem('telegram_user');
    setCurrentPage('home');
  };

  const requireAuth = (action) => {
    if (!currentUser) {
      if (window.confirm('Для этого действия необходимо авторизоваться через Telegram. Войти?')) {
        handleTelegramAuth();
      }
      return false;
    }
    return true;
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    if (currentPage === 'home') {
      loadPosts();
    }
  }, [activeTab, searchQuery, selectedCategory, selectedCity, filters, currentPage]);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      const [categoriesData, citiesData, currenciesData, packagesData] = await Promise.all([
        apiService.getCategories(),
        apiService.getCities(),
        apiService.getCurrencies(),
        apiService.getPackages()
      ]);
      
      setCategories(categoriesData);
      setCities(citiesData);
      setCurrencies(currenciesData);
      setPackages(packagesData);
    } catch (err) {
      setError('Ошибка загрузки данных');
      console.error('Error loading initial data:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadPosts = async () => {
    try {
      const filters = {
        post_type: activeTab,
        search: searchQuery || undefined,
        super_rubric_id: selectedCategory || undefined,
        city_id: selectedCity || undefined
      };
      
      const postsData = await apiService.getPosts(filters);
      setPosts(postsData);
    } catch (err) {
      console.error('Error loading posts:', err);
    }
  };

  const handleCreatePost = async (postData) => {
    if (!requireAuth('create post')) return;
    
    try {
      if (activeTab === 'job') {
        await apiService.createJobPost(postData, currentUser.id);
      } else {
        await apiService.createServicePost(postData, currentUser.id);
      }
      
      setShowCreateModal(false);
      loadPosts();
    } catch (err) {
      console.error('Error creating post:', err);
      alert('Ошибка при создании объявления');
    }
  };

  const handleSearch = (query) => {
    setSearchQuery(query);
  };

  const handleFilterChange = (type, value) => {
    if (type === 'category') {
      setSelectedCategory(value);
    } else if (type === 'city') {
      setSelectedCity(value);
    } else {
      setFilters(prev => ({
        ...prev,
        [type]: value
      }));
    }
  };

  const handleAddToFavorites = async (postId) => {
    if (!requireAuth('add to favorites')) return;
    
    try {
      if (favorites.includes(postId)) {
        await apiService.removeFromFavorites(currentUser.id, postId);
        setFavorites(favorites.filter(id => id !== postId));
      } else {
        await apiService.addToFavorites(currentUser.id, postId);
        setFavorites([...favorites, postId]);
      }
    } catch (err) {
      console.error('Error toggling favorites:', err);
    }
  };

  // Загружаем избранное при старте приложения
  const loadUserFavorites = async () => {
    try {
      const userFavorites = await apiService.getUserFavorites(currentUser.id);
      const favoriteIds = userFavorites.map(post => post.id);
      setFavorites(favoriteIds);
    } catch (err) {
      console.error('Error loading user favorites:', err);
    }
  };

  // Загружаем избранное при инициализации
  useEffect(() => {
    if (currentUser.id) {
      loadUserFavorites();
    }
  }, [currentUser.id]);

  // Применяем тему при загрузке
  useEffect(() => {
    // Загружаем тему из localStorage или используем тему пользователя
    const savedTheme = localStorage.getItem('theme') || currentUser.theme || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    // Обновляем пользователя если тема отличается
    if (savedTheme !== currentUser.theme) {
      setCurrentUser(prev => ({ ...prev, theme: savedTheme }));
    }
  }, []);

  const handleViewDetails = (post) => {
    setSelectedPost(post);
  };

  const handleCloseDetails = () => {
    setSelectedPost(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Загрузка...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600">{error}</p>
          <button 
            onClick={loadInitialData}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Попробовать снова
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-16">
      <main className="container mx-auto px-4 py-6 max-w-md">
        {currentPage === 'home' && (
          <>
            <CategoryTabs 
              activeTab={activeTab}
              onTabChange={setActiveTab}
            />
            
            <SearchBar 
              onSearch={handleSearch}
              categories={categories}
              cities={cities}
              selectedCategory={selectedCategory}
              selectedCity={selectedCity}
              onFilterChange={handleFilterChange}
              activeTab={activeTab}
              onApplyFilters={(filters) => {
                // Применяем все фильтры одновременно
                Object.keys(filters).forEach(key => {
                  if (filters[key] !== '') {
                    handleFilterChange(key, filters[key]);
                  }
                });
              }}
              onResetFilters={() => {
                // Сбрасываем все фильтры
                setSelectedCategory('');
                setSelectedCity('');
                setFilters({});
              }}
            />
            
            <div className="grid grid-cols-2 gap-3 mt-6">
              {posts.length === 0 ? (
                <div className="col-span-2 text-center py-12">
                  <p className="text-gray-500">Объявления не найдены</p>
                </div>
              ) : (
                posts.map(post => (
                  <PostCard 
                    key={post.id}
                    post={post}
                    onAddToFavorites={handleAddToFavorites}
                    onViewDetails={handleViewDetails}
                    currencies={currencies}
                    cities={cities}
                    isFavorite={favorites.includes(post.id)}
                  />
                ))
              )}
            </div>
          </>
        )}
        
        {currentPage === 'favorites' && (
          <FavoritesPage
            favorites={favorites}
            currencies={currencies}
            cities={cities}
            onViewDetails={handleViewDetails}
            onRemoveFromFavorites={handleAddToFavorites}
            currentUser={currentUser}
          />
        )}
        
        {currentPage === 'tariffs' && (
          <TariffsModal
            isOpen={true}
            onClose={() => setCurrentPage('home')}
            packages={packages}
            currencies={currencies}
            onSelectPackage={(packageId) => {
              console.log('Selected package:', packageId);
              setCurrentPage('home');
            }}
          />
        )}
        
        {currentPage === 'profile' && (
          <ProfilePage
            user={currentUser}
            cities={cities}
            onUpdateUser={setCurrentUser}
          />
        )}
      </main>
      
      {/* Модальные окна удалены круглую кнопку */}
      
      {/* Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200">
        <div className="container mx-auto max-w-md px-4">
          <div className="flex justify-around py-3">
            <button 
              className={`flex flex-col items-center text-xs ${currentPage === 'home' ? 'text-blue-600' : 'text-gray-500'}`}
              onClick={() => setCurrentPage('home')}
            >
              <span className="text-xl mb-1">🏠</span>
              Домой
            </button>
            <button 
              className={`flex flex-col items-center text-xs ${currentPage === 'favorites' ? 'text-blue-600' : 'text-gray-500'}`}
              onClick={() => setCurrentPage('favorites')}
            >
              <span className="text-xl mb-1">❤️</span>
              Избранное
            </button>
            <button 
              className="flex flex-col items-center text-xs text-gray-500"
              onClick={() => setShowCreateModal(true)}
            >
              <span className="text-xl mb-1">➕</span>
              Создать
            </button>
            <button 
              className={`flex flex-col items-center text-xs ${currentPage === 'tariffs' ? 'text-blue-600' : 'text-gray-500'}`}
              onClick={() => setCurrentPage('tariffs')}
            >
              <span className="text-xl mb-1">💎</span>
              Тарифы
            </button>
            <button 
              className={`flex flex-col items-center text-xs ${currentPage === 'profile' ? 'text-blue-600' : 'text-gray-500'}`}
              onClick={() => setCurrentPage('profile')}
            >
              <span className="text-xl mb-1">👤</span>
              Профиль
            </button>
          </div>
        </div>
      </nav>
      
      {/* Modals */}
      {showCreateModal && (
        <CreatePostModal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          onSubmit={handleCreatePost}
          postType={activeTab}
          categories={categories}
          cities={cities}
          currencies={currencies}
          packages={packages}
          currentUser={currentUser}
          onShowTariffs={() => {
            setShowCreateModal(false);
            setCurrentPage('tariffs');
          }}
        />
      )}
      
      {selectedPost && (
        <PostDetails
          post={selectedPost}
          onClose={handleCloseDetails}
          currencies={currencies}
          cities={cities}
          onAddToFavorites={handleAddToFavorites}
          isFavorite={favorites.includes(selectedPost.id)}
          currentUser={currentUser}
        />
      )}
    </div>
  );
}

export default App;