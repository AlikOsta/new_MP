import React, { useState, useEffect } from 'react';
import './App.css';

// Components
import Header from './components/Header';
import CategoryTabs from './components/CategoryTabs';
import SearchBar from './components/SearchBar';
import PostCard from './components/PostCard';
import CreatePostModal from './components/CreatePostModal';
import ProfileModal from './components/ProfileModal';
import TariffsModal from './components/TariffsModal';

// Services
import * as apiService from './services/api';

function App() {
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
  
  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [showTariffsModal, setShowTariffsModal] = useState(false);
  
  // User data (would come from Telegram WebApp)
  const [currentUser, setCurrentUser] = useState({
    id: 'demo-user',
    telegram_id: 123456789,
    first_name: 'Alex',
    username: 'alex',
    language: 'ru'
  });

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    loadPosts();
  }, [activeTab, searchQuery, selectedCategory, selectedCity]);

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
    }
  };

  const handleAddToFavorites = async (postId) => {
    try {
      await apiService.addToFavorites(currentUser.id, postId);
      // Update UI feedback
    } catch (err) {
      console.error('Error adding to favorites:', err);
    }
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
    <div className="min-h-screen bg-gray-50">
      <Header 
        user={currentUser}
        onProfileClick={() => setShowProfileModal(true)}
      />
      
      <main className="container mx-auto px-4 py-6 max-w-md">
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
        />
        
        <div className="space-y-4 mt-6">
          {posts.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500">Объявления не найдены</p>
            </div>
          ) : (
            posts.map(post => (
              <PostCard 
                key={post.id}
                post={post}
                onAddToFavorites={handleAddToFavorites}
                currencies={currencies}
                cities={cities}
              />
            ))
          )}
        </div>
      </main>
      
      {/* Floating Action Button */}
      <button
        onClick={() => setShowCreateModal(true)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-700 flex items-center justify-center text-2xl z-50"
      >
        +
      </button>
      
      {/* Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200">
        <div className="container mx-auto max-w-md px-4">
          <div className="flex justify-around py-3">
            <button className="flex flex-col items-center text-xs text-blue-600">
              <span className="text-xl mb-1">🏠</span>
              Главная
            </button>
            <button 
              className="flex flex-col items-center text-xs text-gray-500"
              onClick={() => {/* Navigate to search */}}
            >
              <span className="text-xl mb-1">🔍</span>
              Поиск
            </button>
            <button 
              className="flex flex-col items-center text-xs text-gray-500"
              onClick={() => setShowCreateModal(true)}
            >
              <span className="text-xl mb-1">➕</span>
              Создать
            </button>
            <button 
              className="flex flex-col items-center text-xs text-gray-500"
              onClick={() => {/* Navigate to favorites */}}
            >
              <span className="text-xl mb-1">❤️</span>
              Избранное
            </button>
            <button 
              className="flex flex-col items-center text-xs text-gray-500"
              onClick={() => setShowProfileModal(true)}
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
          onShowTariffs={() => {
            setShowCreateModal(false);
            setShowTariffsModal(true);
          }}
        />
      )}
      
      {showProfileModal && (
        <ProfileModal
          isOpen={showProfileModal}
          onClose={() => setShowProfileModal(false)}
          user={currentUser}
          cities={cities}
        />
      )}
      
      {showTariffsModal && (
        <TariffsModal
          isOpen={showTariffsModal}
          onClose={() => setShowTariffsModal(false)}
          packages={packages}
          currencies={currencies}
          onSelectPackage={(packageId) => {
            console.log('Selected package:', packageId);
            setShowTariffsModal(false);
          }}
        />
      )}
    </div>
  );
}

export default App;