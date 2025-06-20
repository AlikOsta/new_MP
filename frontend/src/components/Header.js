import React from 'react';

const Header = ({ user, onProfileClick }) => {
  return (
    <header className="bg-white shadow-sm border-b">
      <div className="container mx-auto px-4 py-3 max-w-md">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center">
              <span className="text-white font-bold text-sm">🏪</span>
            </div>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">Marketplace</h1>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <select className="text-sm border border-gray-300 rounded px-2 py-1 bg-white">
              <option value="ru">RU</option>
              <option value="ua">UA</option>
            </select>
            
            <button
              onClick={onProfileClick}
              className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center"
            >
              <span className="text-sm">👤</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;