import React from 'react';

const CategoryTabs = ({ activeTab, onTabChange }) => {
  const tabs = [
    { id: 'job', label: 'Работа', icon: '💼' },
    { id: 'service', label: 'Услуги', icon: '🛠️' }
  ];

  return (
    <div className="flex bg-gray-100 rounded-lg overflow-hidden">
      {tabs.map(tab => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          className={`flex-1 py-3 px-4 text-center font-medium transition-colors ${
            activeTab === tab.id
              ? 'bg-blue-600 text-white'
              : 'bg-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          <span className="mr-2">{tab.icon}</span>
          {tab.label}
        </button>
      ))}
    </div>
  );
};

export default CategoryTabs;