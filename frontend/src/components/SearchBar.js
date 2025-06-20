import React, { useState, useEffect } from 'react';

const SearchBar = ({ 
  onSearch, 
  categories, 
  cities, 
  selectedCategory, 
  selectedCity, 
  onFilterChange,
  activeTab,
  onApplyFilters,
  onResetFilters
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [localFilters, setLocalFilters] = useState({
    sortBy: 'date',
    experience: '',
    schedule: '',
    workFormat: '',
    minSalary: '',
    maxPrice: '',
    category: selectedCategory,
    city: selectedCity
  });

  // Синхронизируем локальные фильтры с внешними
  useEffect(() => {
    setLocalFilters(prev => ({
      ...prev,
      category: selectedCategory,
      city: selectedCity
    }));
  }, [selectedCategory, selectedCity]);

  const handleSearch = (e) => {
    e.preventDefault();
    onSearch(searchQuery);
  };

  const handleSearchInput = (e) => {
    const value = e.target.value;
    setSearchQuery(value);
    onSearch(value);
  };

  const handleFilterChange = (filterType, value) => {
    setLocalFilters(prev => ({
      ...prev,
      [filterType]: value
    }));
  };

  const handleApplyFilters = () => {
    // Применяем все фильтры
    Object.keys(localFilters).forEach(key => {
      if (localFilters[key] !== '') {
        onFilterChange(key, localFilters[key]);
      }
    });
    onApplyFilters && onApplyFilters(localFilters);
    setShowFilters(false);
  };

  const handleResetFilters = () => {
    const resetFilters = {
      sortBy: 'date',
      experience: '',
      schedule: '',
      workFormat: '',
      minSalary: '',
      maxPrice: '',
      category: '',
      city: ''
    };
    setLocalFilters(resetFilters);
    onResetFilters && onResetFilters();
  };

  return (
    <div className="mt-4">
      <form onSubmit={handleSearch} className="relative">
        <input
          type="text"
          placeholder="Поиск..."
          value={searchQuery}
          onChange={handleSearchInput}
          className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <span className="text-gray-400">🔍</span>
        </div>
      </form>

      <button
        onClick={() => setShowFilters(!showFilters)}
        className="mt-3 flex items-center justify-center w-full py-2 px-4 border border-gray-300 rounded-lg bg-white hover:bg-gray-50"
      >
        <span className="mr-2">🏷️</span>
        Фильтры и сортировка
      </button>

      {showFilters && (
        <div className="mt-3 p-4 bg-white border border-gray-200 rounded-lg space-y-4">
          {/* Общие фильтры */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Город
            </label>
            <select
              value={selectedCity}
              onChange={(e) => onFilterChange('city', e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Все города</option>
              {cities.map(city => (
                <option key={city.id} value={city.id}>
                  {city.name_ru}
                </option>
              ))}
            </select>
          </div>

          {/* Сортировка */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Сортировать по
            </label>
            <select
              value={localFilters.sortBy}
              onChange={(e) => handleFilterChange('sortBy', e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
            >
              <option value="date">Дате публикации</option>
              <option value="price_asc">Цене (по возрастанию)</option>
              <option value="price_desc">Цене (по убыванию)</option>
              <option value="views">Популярности</option>
            </select>
          </div>

          {/* Фильтры для работы */}
          {activeTab === 'job' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Опыт работы
                </label>
                <select 
                  value={experience}
                  onChange={(e) => handleJobFilterChange('experience', e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Любой</option>
                  <option value="no_experience">Без опыта</option>
                  <option value="up_to_1_year">До 1 года</option>
                  <option value="from_1_to_3_years">1-3 года</option>
                  <option value="from_3_to_6_years">3-6 лет</option>
                  <option value="more_than_6_years">6+ лет</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  График работы
                </label>
                <select 
                  value={schedule}
                  onChange={(e) => handleJobFilterChange('schedule', e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Любой</option>
                  <option value="full_time">Полный день</option>
                  <option value="part_time">Частичная занятость</option>
                  <option value="project">Проектная работа</option>
                  <option value="freelance">Фриланс</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Формат работы
                </label>
                <select 
                  value={workFormat}
                  onChange={(e) => handleJobFilterChange('work_format', e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Любой</option>
                  <option value="office">Офис</option>
                  <option value="remote">Удаленно</option>
                  <option value="hybrid">Гибрид</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Зарплата от
                </label>
                <input
                  type="number"
                  placeholder="Например, 50000"
                  value={minSalary}
                  onChange={(e) => handleJobFilterChange('min_salary', e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </>
          )}

          {/* Фильтры для услуг */}
          {activeTab === 'service' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Категория услуг
                </label>
                <select
                  value={selectedCategory}
                  onChange={(e) => onFilterChange('category', e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Все категории</option>
                  {categories.filter(cat => cat.name_ru === 'Услуги').map(category => (
                    <option key={category.id} value={category.id}>
                      {category.name_ru}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Стоимость до
                </label>
                <input
                  type="number"
                  placeholder="Например, 5000"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default SearchBar;