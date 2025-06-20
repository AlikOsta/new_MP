import React, { useState, useEffect } from 'react';

const PostCard = ({ post, onAddToFavorites, onViewDetails, currencies, cities, isFavorite }) => {
  const [localIsFavorite, setLocalIsFavorite] = useState(isFavorite);

  useEffect(() => {
    setLocalIsFavorite(isFavorite);
  }, [isFavorite]);

  const getCurrencySymbol = (currencyId) => {
    const currency = currencies.find(c => c.id === currencyId);
    return currency?.symbol || '₽';
  };

  const getCityName = (cityId) => {
    const city = cities.find(c => c.id === cityId);
    return city?.name_ru || 'Неизвестно';
  };

  const handleFavoriteClick = async (e) => {
    e.stopPropagation();
    try {
      await onAddToFavorites(post.id);
      setLocalIsFavorite(!localIsFavorite);
    } catch (error) {
      console.error('Error toggling favorite:', error);
    }
  };

  const formatPrice = (price) => {
    if (!price) return 'Договорная';
    return new Intl.NumberFormat('ru-RU').format(price);
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) return 'Сегодня';
    if (diffDays === 2) return 'Вчера';
    if (diffDays <= 7) return `${diffDays} дн. назад`;
    return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
  };

  return (
    <div 
      className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden cursor-pointer hover:shadow-md transition-shadow"
      onClick={() => onViewDetails(post)}
    >
      {/* Image */}
      <div className="relative">
        {post.image_url ? (
          <img 
            src={post.image_url} 
            alt={post.title}
            className="w-full h-24 object-cover"
          />
        ) : (
          <div className="w-full h-24 bg-gray-200 flex items-center justify-center">
            <span className="text-2xl text-gray-400">📷</span>
          </div>
        )}
        
        {/* Favorite button */}
        <button
          onClick={handleFavoriteClick}
          className="absolute top-2 right-2 w-6 h-6 bg-white bg-opacity-90 rounded-full flex items-center justify-center shadow"
        >
          <span className={`text-xs ${localIsFavorite ? 'text-red-500' : 'text-gray-400'}`}>
            {localIsFavorite ? '❤️' : '🤍'}
          </span>
        </button>

        {/* Premium badge */}
        {post.is_premium && (
          <div className="absolute top-2 left-2 bg-yellow-500 text-white px-1 py-0.5 rounded text-xs font-semibold">
            Premium
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-3">
        <h3 className="font-medium text-sm text-gray-900 mb-2 line-clamp-2 leading-tight">
          {post.title}
        </h3>
        
        {/* Price */}
        <div className="text-lg font-bold text-blue-600 mb-2">
          {formatPrice(post.price)} {getCurrencySymbol(post.currency_id)}
        </div>

        {/* Location and info */}
        <div className="flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center">
            <span className="mr-1">📍</span>
            <span className="truncate">{getCityName(post.city_id)}</span>
          </div>
          
          <div className="flex items-center space-x-2">
            <span className="flex items-center">
              <span className="mr-1">👁️</span>
              {post.views_count || 0}
            </span>
          </div>
        </div>
        
        {/* Date */}
        <div className="text-xs text-gray-400 mt-1">
          {formatDate(post.created_at)}
        </div>
      </div>
    </div>
  );
};

export default PostCard;