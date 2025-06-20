import React, { useState } from 'react';

const SearchBar = ({ 
  onSearch, 
  categories, 
  cities, 
  selectedCategory, 
  selectedCity, 
  onFilterChange 
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  const handleSearch = (e) => {
    e.preventDefault();
    onSearch(searchQuery);
  };

  const handleSearchInput = (e) => {
    const value = e.target.value;
    setSearchQuery(value);
    onSearch(value);
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
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Категория
            </label>
            <select
              value={selectedCategory}
              onChange={(e) => onFilterChange('category', e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Все категории</option>
              {categories.map(category => (
                <option key={category.id} value={category.id}>
                  {category.name_ru}
                </option>
              ))}
            </select>
          </div>

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
        </div>
      )}
    </div>
  );
};

export default SearchBar;