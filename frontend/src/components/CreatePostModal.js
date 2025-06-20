import React, { useState } from 'react';

const CreatePostModal = ({ 
  isOpen, 
  onClose, 
  onSubmit, 
  postType, 
  categories, 
  cities, 
  currencies,
  onShowTariffs 
}) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    price: '',
    currency_id: '',
    super_rubric_id: '',
    city_id: '',
    phone: '',
    // Job specific
    experience: '',
    schedule: '',
    work_format: ''
  });

  const [errors, setErrors] = useState({});

  React.useEffect(() => {
    if (currencies.length > 0 && !formData.currency_id) {
      const rubCurrency = currencies.find(c => c.code === 'RUB');
      if (rubCurrency) {
        setFormData(prev => ({ ...prev, currency_id: rubCurrency.id }));
      }
    }
  }, [currencies, formData.currency_id]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.title.trim()) {
      newErrors.title = 'Заголовок обязателен';
    }

    if (!formData.description.trim()) {
      newErrors.description = 'Описание обязательно';
    }

    if (!formData.super_rubric_id) {
      newErrors.super_rubric_id = 'Выберите категорию';
    }

    if (!formData.city_id) {
      newErrors.city_id = 'Выберите город';
    }

    if (!formData.currency_id) {
      newErrors.currency_id = 'Выберите валюту';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    // Convert price to number
    const submitData = {
      ...formData,
      price: formData.price ? parseFloat(formData.price) : null
    };

    onSubmit(submitData);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b px-6 py-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">
              Новое объявление - {postType === 'job' ? 'Работа' : 'Услуги'}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Заголовок *
            </label>
            <input
              type="text"
              name="title"
              value={formData.title}
              onChange={handleChange}
              placeholder="например, Website Design"
              className={`w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 ${
                errors.title ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {errors.title && (
              <p className="text-red-500 text-sm mt-1">{errors.title}</p>
            )}
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Описание *
            </label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleChange}
              placeholder="Describe your job or service..."
              rows={4}
              className={`w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 ${
                errors.description ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {errors.description && (
              <p className="text-red-500 text-sm mt-1">{errors.description}</p>
            )}
          </div>

          {/* Category and Price Row */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Категория *
              </label>
              <select
                name="super_rubric_id"
                value={formData.super_rubric_id}
                onChange={handleChange}
                className={`w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 ${
                  errors.super_rubric_id ? 'border-red-500' : 'border-gray-300'
                }`}
              >
                <option value="">Выберите</option>
                {categories.map(category => (
                  <option key={category.id} value={category.id}>
                    {category.name_ru}
                  </option>
                ))}
              </select>
              {errors.super_rubric_id && (
                <p className="text-red-500 text-sm mt-1">{errors.super_rubric_id}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Цена
              </label>
              <div className="flex">
                <input
                  type="number"
                  name="price"
                  value={formData.price}
                  onChange={handleChange}
                  placeholder="500"
                  className="flex-1 border border-r-0 rounded-l-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 border-gray-300"
                />
                <select
                  name="currency_id"
                  value={formData.currency_id}
                  onChange={handleChange}
                  className="border border-l-0 rounded-r-lg px-2 py-2 focus:ring-2 focus:ring-blue-500 border-gray-300 bg-white"
                >
                  {currencies.map(currency => (
                    <option key={currency.id} value={currency.id}>
                      {currency.symbol}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* City */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Город *
            </label>
            <select
              name="city_id"
              value={formData.city_id}
              onChange={handleChange}
              className={`w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 ${
                errors.city_id ? 'border-red-500' : 'border-gray-300'
              }`}
            >
              <option value="">Выберите город</option>
              {cities.map(city => (
                <option key={city.id} value={city.id}>
                  {city.name_ru}
                </option>
              ))}
            </select>
            {errors.city_id && (
              <p className="text-red-500 text-sm mt-1">{errors.city_id}</p>
            )}
          </div>

          {/* Phone */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Телефон
            </label>
            <input
              type="tel"
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              placeholder="+7 (999) 123-45-67"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Job-specific fields */}
          {postType === 'job' && (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Опыт
                  </label>
                  <select
                    name="experience"
                    value={formData.experience}
                    onChange={handleChange}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Не важно</option>
                    <option value="no_experience">Без опыта</option>
                    <option value="up_to_1_year">До 1 года</option>
                    <option value="from_1_to_3_years">1-3 года</option>
                    <option value="from_3_to_6_years">3-6 лет</option>
                    <option value="more_than_6_years">6+ лет</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    График
                  </label>
                  <select
                    name="schedule"
                    value={formData.schedule}
                    onChange={handleChange}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Не указано</option>
                    <option value="full_time">Полный день</option>
                    <option value="part_time">Частичная занятость</option>
                    <option value="project">Проектная работа</option>
                    <option value="freelance">Фриланс</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Формат работы
                </label>
                <select
                  name="work_format"
                  value={formData.work_format}
                  onChange={handleChange}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Не указано</option>
                  <option value="office">Офис</option>
                  <option value="remote">Удаленно</option>
                  <option value="hybrid">Гибрид</option>
                </select>
              </div>
            </>
          )}

          {/* Photo Upload */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Фото
            </label>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
              <div className="text-4xl mb-2">📷</div>
              <div className="text-sm text-gray-600">
                <p>Tap to Upload Photo</p>
                <p className="text-xs">PNG, JPG, GIF up to 10MB</p>
              </div>
            </div>
          </div>

          {/* Buttons */}
          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-3 px-4 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              Отмена
            </button>
            <button
              type="submit"
              className="flex-1 py-3 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Опубликовать
            </button>
          </div>

          {/* Tariffs link */}
          <div className="text-center pt-4">
            <button
              type="button"
              onClick={onShowTariffs}
              className="text-blue-600 text-sm hover:underline"
            >
              Посмотреть тарифы
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreatePostModal;