import React, { useState } from 'react';

const PostCard = ({ post, onAddToFavorites, currencies, cities }) => {
  const [isFavorite, setIsFavorite] = useState(false);

  const getCurrencySymbol = (currencyId) => {
    const currency = currencies.find(c => c.id === currencyId);
    return currency?.symbol || '₽';
  };

  const getCityName = (cityId) => {
    const city = cities.find(c => c.id === cityId);
    return city?.name_ru || 'Неизвестно';
  };

  const handleFavoriteClick = async () => {
    try {
      await onAddToFavorites(post.id);
      setIsFavorite(!isFavorite);
    } catch (error) {
      console.error('Error toggling favorite:', error);
    }
  };

  const formatPrice = (price) => {
    if (!price) return 'Договорная';
    return new Intl.NumberFormat('ru-RU').format(price);
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* Image */}
      <div className="relative">
        {post.image_url ? (
          <img 
            src={post.image_url} 
            alt={post.title}
            className="w-full h-48 object-cover"
          />
        ) : (
          <div className="w-full h-48 bg-gray-200 flex items-center justify-center">
            <span className="text-4xl text-gray-400">📷</span>
          </div>
        )}
        
        {/* Favorite button */}
        <button
          onClick={handleFavoriteClick}
          className="absolute top-3 right-3 w-8 h-8 bg-white bg-opacity-90 rounded-full flex items-center justify-center shadow"
        >
          <span className={isFavorite ? 'text-red-500' : 'text-gray-400'}>
            {isFavorite ? '❤️' : '🤍'}
          </span>
        </button>

        {/* Premium badge */}
        {post.is_premium && (
          <div className="absolute top-3 left-3 bg-yellow-500 text-white px-2 py-1 rounded text-xs font-semibold">
            Premium
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-4">
        <h3 className="font-semibold text-lg text-gray-900 mb-2 line-clamp-2">
          {post.title}
        </h3>
        
        <p className="text-gray-600 text-sm mb-3 line-clamp-3">
          {post.description}
        </p>

        {/* Price */}
        <div className="flex items-center justify-between mb-3">
          <div className="text-2xl font-bold text-blue-600">
            {formatPrice(post.price)} {getCurrencySymbol(post.currency_id)}
          </div>
          
          {/* Job specific info */}
          {post.post_type === 'job' && post.experience && (
            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
              {getExperienceLabel(post.experience)}
            </span>
          )}
        </div>

        {/* Location and views */}
        <div className="flex items-center justify-between text-sm text-gray-500">
          <div className="flex items-center">
            <span className="mr-1">📍</span>
            {getCityName(post.city_id)}
          </div>
          
          <div className="flex items-center space-x-3">
            <span className="flex items-center">
              <span className="mr-1">👁️</span>
              {post.views_count || 0}
            </span>
            
            <span>
              {new Date(post.created_at).toLocaleDateString('ru-RU')}
            </span>
          </div>
        </div>

        {/* Additional job info */}
        {post.post_type === 'job' && (
          <div className="mt-3 flex flex-wrap gap-2">
            {post.schedule && (
              <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                {getScheduleLabel(post.schedule)}
              </span>
            )}
            {post.work_format && (
              <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                {getWorkFormatLabel(post.work_format)}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// Helper functions
const getExperienceLabel = (experience) => {
  const labels = {
    'no_experience': 'Без опыта',
    'up_to_1_year': 'До 1 года',
    'from_1_to_3_years': '1-3 года',
    'from_3_to_6_years': '3-6 лет',
    'more_than_6_years': '6+ лет'
  };
  return labels[experience] || experience;
};

const getScheduleLabel = (schedule) => {
  const labels = {
    'full_time': 'Полный день',
    'part_time': 'Частичная занятость',
    'project': 'Проектная работа',
    'freelance': 'Фриланс'
  };
  return labels[schedule] || schedule;
};

const getWorkFormatLabel = (format) => {
  const labels = {
    'office': 'Офис',
    'remote': 'Удаленно',
    'hybrid': 'Гибрид'
  };
  return labels[format] || format;
};

export default PostCard;