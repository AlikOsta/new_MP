import React, { useState } from 'react';

const CreatePostModal = ({ 
  isOpen, 
  onClose, 
  onSubmit, 
  postType, 
  categories, 
  cities, 
  currencies,
  packages,
  onShowTariffs,
  currentUser
}) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    price: '',
    currency_id: '',
    city_id: currentUser?.city_id || '',
    phone: currentUser?.phone || '',
    // Job specific
    experience: '',
    schedule: '',
    work_format: ''
  });

  const [selectedPackage, setSelectedPackage] = useState('');
  const [selectedImage, setSelectedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [errors, setErrors] = useState({});

  React.useEffect(() => {
    if (currencies.length > 0 && !formData.currency_id) {
      const rubCurrency = currencies.find(c => c.code === 'RUB');
      if (rubCurrency) {
        setFormData(prev => ({ ...prev, currency_id: rubCurrency.id }));
      }
    }
  }, [currencies, formData.currency_id]);
  
  // Отдельный useEffect для обновления данных пользователя
  React.useEffect(() => {
    if (currentUser) {
      setFormData(prev => ({
        ...prev,
        city_id: currentUser.city_id || '',
        phone: currentUser.phone || ''
      }));
    }
  }, [currentUser]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Проверяем размер файла (макс 5MB)
      if (file.size > 5 * 1024 * 1024) {
        alert('Файл слишком большой. Максимальный размер: 5MB');
        return;
      }

      // Проверяем тип файла
      if (!file.type.startsWith('image/')) {
        alert('Пожалуйста, выберите изображение');
        return;
      }

      setSelectedImage(file);
      
      // Создаем превью
      const reader = new FileReader();
      reader.onload = (e) => {
        setImagePreview(e.target.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const compressImage = (file, maxWidth = 800, quality = 0.8) => {
    return new Promise((resolve) => {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      const img = new Image();
      
      img.onload = () => {
        // Вычисляем новые размеры
        const ratio = Math.min(maxWidth / img.width, maxWidth / img.height);
        canvas.width = img.width * ratio;
        canvas.height = img.height * ratio;
        
        // Рисуем сжатое изображение
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        
        // Конвертируем в blob
        canvas.toBlob(resolve, 'image/jpeg', quality);
      };
      
      img.src = URL.createObjectURL(file);
    });
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.title.trim()) {
      newErrors.title = 'Заголовок обязателен';
    }

    if (!formData.description.trim()) {
      newErrors.description = 'Описание обязательно';
    }

    if (!formData.city_id) {
      newErrors.city_id = 'Выберите город';
    }

    if (!formData.currency_id) {
      newErrors.currency_id = 'Выберите валюту';
    }

    if (!selectedPackage) {
      newErrors.package = 'Выберите тариф';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    // Получаем ID категории на основе типа поста
    const category = categories.find(cat => 
      postType === 'job' ? cat.name_ru === 'Работа' : cat.name_ru === 'Услуги'
    );

    let imageUrl = null;
    if (selectedImage) {
      // Сжимаем изображение
      const compressedImage = await compressImage(selectedImage);
      // В реальном приложении здесь бы была загрузка на сервер
      // Пока что просто создаем URL
      imageUrl = URL.createObjectURL(compressedImage);
    }

    // Convert price to number
    const submitData = {
      ...formData,
      price: formData.price ? parseFloat(formData.price) : null,
      super_rubric_id: category?.id,
      image_url: imageUrl,
      package_id: selectedPackage
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
              {postType === 'job' ? 'Новая вакансия' : 'Новая услуга'}
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
              placeholder={postType === 'job' ? 'например, Frontend разработчик' : 'например, Ремонт компьютеров'}
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
              placeholder={postType === 'job' ? 'Опишите требования к кандидату...' : 'Опишите вашу услугу...'}
              rows={4}
              className={`w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 ${
                errors.description ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {errors.description && (
              <p className="text-red-500 text-sm mt-1">{errors.description}</p>
            )}
          </div>

          {/* Price and Currency Row */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {postType === 'job' ? 'Зарплата' : 'Стоимость'}
              </label>
              <input
                type="number"
                name="price"
                value={formData.price}
                onChange={handleChange}
                placeholder="50000"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Валюта
              </label>
              <select
                name="currency_id"
                value={formData.currency_id}
                onChange={handleChange}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
              >
                {currencies.map(currency => (
                  <option key={currency.id} value={currency.id}>
                    {currency.symbol} {currency.code}
                  </option>
                ))}
              </select>
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

          {/* Package Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Выберите тариф *
            </label>
            <div className="space-y-2">
              {packages.map(pkg => (
                <label key={pkg.id} className="flex items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50">
                  <input
                    type="radio"
                    name="package"
                    value={pkg.id}
                    checked={selectedPackage === pkg.id}
                    onChange={(e) => setSelectedPackage(e.target.value)}
                    className="mr-3"
                  />
                  <div className="flex-1">
                    <div className="flex justify-between items-center">
                      <span className="font-medium">{pkg.name_ru}</span>
                      <span className="text-blue-600 font-bold">
                        {pkg.price === 0 ? 'Бесплатно' : `${pkg.price} ₽`}
                      </span>
                    </div>
                    <div className="text-sm text-gray-500">
                      {pkg.features_ru[0]} • {pkg.duration_days} дней
                    </div>
                  </div>
                </label>
              ))}
            </div>
            {errors.package && (
              <p className="text-red-500 text-sm mt-1">{errors.package}</p>
            )}
          </div>

          {/* Photo Upload - only show if package supports photos */}
          {(() => {
            const selectedPkg = packages.find(pkg => pkg.id === selectedPackage);
            return selectedPkg?.has_photo ? (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Фото
                </label>
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-4">
                  {imagePreview ? (
                    <div className="relative">
                      <img src={imagePreview} alt="Preview" className="w-full h-32 object-cover rounded" />
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedImage(null);
                          setImagePreview(null);
                        }}
                        className="absolute top-2 right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm"
                      >
                        ✕
                      </button>
                    </div>
                  ) : (
                    <div className="text-center">
                      <input
                        type="file"
                        accept="image/*"
                        onChange={handleImageChange}
                        className="hidden"
                        id="image-upload"
                      />
                      <label htmlFor="image-upload" className="cursor-pointer">
                        <div className="text-4xl mb-2">📷</div>
                        <div className="text-sm text-gray-600">
                          <p>Нажмите для выбора фото</p>
                          <p className="text-xs">PNG, JPG до 5MB</p>
                        </div>
                      </label>
                    </div>
                  )}
                </div>
              </div>
            ) : null;
          })()}

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
          <div className="text-center pt-2">
            <button
              type="button"
              onClick={onShowTariffs}
              className="text-blue-600 text-sm hover:underline"
            >
              Подробнее о тарифах
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreatePostModal;