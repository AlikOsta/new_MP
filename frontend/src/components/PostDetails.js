import React, { useEffect, useState } from 'react';
import * as apiService from '../services/api';

const PostDetails = ({ post: initialPost, onClose, currencies, cities, onAddToFavorites, isFavorite, currentUser }) => {
  const [post, setPost] = useState(initialPost);
  const [authorInfo, setAuthorInfo] = useState(null);

  useEffect(() => {
    // Загружаем детали поста и увеличиваем счетчик просмотров
    const loadPostDetails = async () => {
      try {
        const detailsData = await apiService.getPost(initialPost.id, currentUser?.id);
        setPost(detailsData);
        
        // Загружаем информацию об авторе
        if (detailsData.author_id) {
          const authorData = await apiService.getUser(detailsData.author_id);
          if (authorData && !authorData.error) {
            setAuthorInfo(authorData);
          }
        }
      } catch (error) {
        console.error('Error loading post details:', error);
        setPost(initialPost);
      }
    };

    loadPostDetails();
  }, [initialPost.id, currentUser?.id]);
  const getCurrencySymbol = (currencyId) => {
    const currency = currencies.find(c => c.id === currencyId);
    return currency?.symbol || '₽';
  };

  const getCityName = (cityId) => {
    const city = cities.find(c => c.id === cityId);
    return city?.name_ru || 'Неизвестно';
  };

  const formatPrice = (price) => {
    if (!price) return 'Договорная';
    return new Intl.NumberFormat('ru-RU').format(price);
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', { 
      day: 'numeric', 
      month: 'long', 
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

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

  const isOwnPost = currentUser && post.author_id === currentUser.id;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-end justify-center">
      <div className="bg-white rounded-t-lg w-full max-w-md max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b px-4 py-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Объявление</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl"
          >
            ✕
          </button>
        </div>

        {/* Image with favorite button */}
        <div className="relative">
          {post.image_url ? (
            <img 
              src={post.image_url} 
              alt={post.title}
              className="w-full h-64 object-cover"
            />
          ) : (
            <div className="w-full h-64 bg-gray-200 flex items-center justify-center">
              <span className="text-6xl text-gray-400">📷</span>
            </div>
          )}
          
          {/* Favorite button - only if not own post */}
          {!isOwnPost && (
            <button
              onClick={() => onAddToFavorites(post.id)}
              className="absolute top-4 right-4 w-10 h-10 bg-white bg-opacity-90 rounded-full flex items-center justify-center shadow-lg"
            >
              <span className={`text-lg ${isFavorite ? 'text-red-500' : 'text-gray-400'}`}>
                {isFavorite ? '❤️' : '🤍'}
              </span>
            </button>
          )}
        </div>

        {/* Content */}
        <div className="p-4">
          {/* Title and Price */}
          <div className="mb-4">
            <h1 className="text-xl font-bold text-gray-900 mb-2">{post.title}</h1>
            <div className="text-3xl font-bold text-blue-600">
              {formatPrice(post.price)} {getCurrencySymbol(post.currency_id)}
            </div>
          </div>

          {/* Description */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-2">Описание</h3>
            <p className="text-gray-700 leading-relaxed">{post.description}</p>
          </div>

          {/* Job specific info */}
          {post.post_type === 'job' && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-3">Требования</h3>
              <div className="space-y-2">
                {post.experience && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Опыт работы:</span>
                    <span className="font-medium">{getExperienceLabel(post.experience)}</span>
                  </div>
                )}
                {post.schedule && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">График работы:</span>
                    <span className="font-medium">{getScheduleLabel(post.schedule)}</span>
                  </div>
                )}
                {post.work_format && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Формат работы:</span>
                    <span className="font-medium">{getWorkFormatLabel(post.work_format)}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Contact info */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-3">Контакты</h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600">Город:</span>
                <span className="font-medium">{getCityName(post.city_id)}</span>
              </div>
              {post.phone && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Телефон:</span>
                  <a href={`tel:${post.phone}`} className="font-medium text-blue-600">
                    {post.phone}
                  </a>
                </div>
              )}
            </div>
          </div>

          {/* Author info */}
          {authorInfo && !authorInfo.error && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-3">Продавец</h3>
              <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center overflow-hidden">
                  {authorInfo.photo_url ? (
                    <img src={authorInfo.photo_url} alt="Author" className="w-full h-full object-cover" />
                  ) : (
                    <span className="text-lg">👤</span>
                  )}
                </div>
                <div className="flex-1">
                  <div className="font-medium">
                    {authorInfo.first_name} {authorInfo.last_name || ''}
                  </div>
                  <div className="text-sm text-gray-600">@{authorInfo.username}</div>
                  {authorInfo.city_id && (
                    <div className="text-xs text-gray-500">{getCityName(authorInfo.city_id)}</div>
                  )}
                </div>
                {!isOwnPost && (
                  <button
                    className="text-blue-600 text-sm hover:underline"
                    onClick={() => {/* Navigate to author profile */}}
                  >
                    Профиль
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Meta info */}
          <div className="border-t pt-4 mb-6">
            <div className="flex justify-between items-center text-sm text-gray-500">
              <div>
                <span>Просмотры: {post.views_count || 0}</span>
              </div>
              <div>
                <span>Опубликовано: {formatDate(post.created_at)}</span>
              </div>
            </div>
          </div>

          {/* Action buttons */}
          {!isOwnPost && (
            <div className="flex space-x-3">
              {post.phone ? (
                <>
                  <button
                    onClick={() => window.open(`https://t.me/${authorInfo?.username}`, '_blank')}
                    className="flex-1 py-3 px-4 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200"
                  >
                    💬 Написать
                  </button>
                  <button
                    onClick={() => window.open(`tel:${post.phone}`)}
                    className="flex-1 py-3 px-4 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700"
                  >
                    📞 Позвонить
                  </button>
                </>
              ) : (
                <button
                  onClick={() => window.open(`https://t.me/${authorInfo?.username}`, '_blank')}
                  className="w-full py-3 px-4 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700"
                >
                  💬 Написать
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PostDetails;