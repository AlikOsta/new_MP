import React, { useState, useEffect } from 'react';
import PostCard from './PostCard';
import * as apiService from '../services/api';

const FavoritesPage = ({ favorites, currencies, cities, onViewDetails, onRemoveFromFavorites }) => {
  const [favoritePosts, setFavoritePosts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadFavoritePosts();
  }, [favorites]);

  const loadFavoritePosts = async () => {
    if (favorites.length === 0) {
      setFavoritePosts([]);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      // Загружаем все объявления и фильтруем избранные
      const allPosts = await apiService.getPosts({});
      const filteredPosts = allPosts.filter(post => favorites.includes(post.id));
      setFavoritePosts(filteredPosts);
    } catch (error) {
      console.error('Error loading favorite posts:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Избранное</h1>
      
      {favoritePosts.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">❤️</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Пока пусто</h3>
          <p className="text-gray-500">Добавляйте объявления в избранное, чтобы не потерять</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3">
          {favoritePosts.map(post => (
            <PostCard 
              key={post.id}
              post={post}
              onAddToFavorites={onRemoveFromFavorites}
              onViewDetails={onViewDetails}
              currencies={currencies}
              cities={cities}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default FavoritesPage;