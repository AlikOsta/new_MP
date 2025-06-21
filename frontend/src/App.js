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
  
  // User data - Telegram WebApp user
  const [currentUser, setCurrentUser] = useState(null);
  const [isAuthenticating, setIsAuthenticating] = useState(true);

  // Telegram WebApp authentication
  useEffect(() => {
    const initTelegramAuth = () => {
      setIsAuthenticating(true);
      
      // Check if running in Telegram WebApp
      if (window.Telegram?.WebApp) {
        const tg = window.Telegram.WebApp;
        tg.ready();
        
        // Get user data from Telegram WebApp
        const user = tg.initDataUnsafe?.user;
        if (user) {
          const userData = {
            id: user.id.toString(),
            telegram_id: user.id,
            first_name: user.first_name,
            last_name: user.last_name || '',
            username: user.username || '',
            language: user.language_code || 'ru',
            theme: tg.colorScheme || 'light'
          };
          setCurrentUser(userData);
        }
      }
      
      setIsAuthenticating(false);
    };

    initTelegramAuth();
  }, []);

  const handleTelegramAuth = () => {
    // This function is called when user needs to authenticate
    // In Telegram WebApp, this would typically not be needed as user is already authenticated
    alert('Пожалуйста, откройте приложение через Telegram Bot');
  };

  const handleLogout = () => {
    // In Telegram WebApp, logout would typically close the app
    if (window.Telegram?.WebApp) {
      window.Telegram.WebApp.close();
    }
  };

  const requireAuth = (action) => {
    if (!currentUser) {
      alert('Это действие доступно только в Telegram Mini App');
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
      // Проверяем можно ли создать бесплатный пост
      if (postData.package_id === 'free-package') {
        const freePostCheck = await apiService.checkFreePostAvailability(currentUser.id);
        if (!freePostCheck.can_create_free) {
          const nextDate = new Date(freePostCheck.next_free_at).toLocaleDateString('ru-RU');
          alert(`Бесплатный пост можно будет создать ${nextDate}`);
          return;
        }
      }
      
      // Если выбран платный тариф, инициируем оплату
      const selectedPackage = packages.find(pkg => pkg.id === postData.package_id);
      if (selectedPackage && selectedPackage.price > 0) {
        const paymentResult = await apiService.purchasePackage(currentUser.id, postData.package_id);
        
        // Инициируем Telegram Payment
        if (window.Telegram?.WebApp) {
          // TODO: Интегрировать с Telegram Payment API
          console.log('Payment initiated:', paymentResult);
        }
      }
      
      if (activeTab === 'job') {
        await apiService.createJobPost(postData, currentUser.id);
      } else {
        await apiService.createServicePost(postData, currentUser.id);
      }
      
      setShowCreateModal(false);
      loadPosts();
      
      if (selectedPackage && selectedPackage.price === 0) {
        alert('Объявление отправлено на модерацию!');
      } else if (selectedPackage && selectedPackage.price > 0) {
        alert('Объявление создано! После оплаты оно будет отправлено на модерацию.');
      }
    } catch (err) {
      console.error('Error creating post:', err);
      
      if (err.message && err.message.includes('Free post not available')) {
        alert('Бесплатный пост пока недоступен. Выберите платный тариф или попробуйте позже.');
      } else {
        alert('Ошибка при создании объявления');
      }
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
    if (!currentUser) return; // Только для авторизованных пользователей
    
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
    if (currentUser?.id && !isAuthenticating) {
      loadUserFavorites();
    }
  }, [currentUser?.id, isAuthenticating]);

  // Применяем тему при загрузке
  useEffect(() => {
    // Загружаем тему из localStorage или используем тему пользователя
    const savedTheme = localStorage.getItem('theme') || currentUser?.theme || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    // Обновляем пользователя если тема отличается
    if (currentUser && savedTheme !== currentUser.theme) {
      setCurrentUser(prev => ({ ...prev, theme: savedTheme }));
    }
  }, [currentUser?.theme]);

  const handleViewDetails = (post) => {
    setSelectedPost(post);
  };

  const handleShowCreateModal = () => {
    if (!requireAuth('create post')) return;
    setShowCreateModal(true);
  };

  const handleShowFavorites = () => {
    if (!requireAuth('view favorites')) return;
    setCurrentPage('favorites');
  };

  const handleShowProfile = () => {
    if (!requireAuth('view profile')) return;
    setCurrentPage('profile');
  };

  const handleCloseDetails = () => {
    setSelectedPost(null);
  };

  if (loading || isAuthenticating) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">
            {isAuthenticating ? 'Проверка авторизации...' : 'Загрузка...'}
          </p>
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
                    isUserAuthenticated={!!currentUser}
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
              onClick={handleShowFavorites}
            >
              <span className="text-xl mb-1">❤️</span>
              Избранное
              {!currentUser && <span className="text-xs text-red-500">*</span>}
            </button>
            <button 
              className="flex flex-col items-center text-xs text-gray-500"
              onClick={handleShowCreateModal}
            >
              <span className="text-xl mb-1">➕</span>
              Создать
              {!currentUser && <span className="text-xs text-red-500">*</span>}
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
              onClick={handleShowProfile}
            >
              <span className="text-xl mb-1">👤</span>
              {currentUser ? 'Профиль' : 'Войти'}
              {!currentUser && <span className="text-xs text-red-500">*</span>}
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