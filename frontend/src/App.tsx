import React, { useState } from 'react';
import './App.css';

// Імпорт компонентів сторінок
import Header from './components/Header.tsx';
import Sidebar from './components/Sidebar.tsx';
import GroupingView from './pages/GroupingView.tsx';
import HelpPage from './pages/HelpPage.tsx';
import SavedGroupingsPage from './pages/SavedGroupingsPage.tsx';
import NormalizationPage from './pages/NormalizationPage.tsx';
import HomePage from './pages/HomePage.tsx';
import AutoNormalization from './components/AutoNormalization.tsx';

const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<'home' | 'grouping' | 'saved-groupings' | 'help' | 'normalization' | 'autonormalization'>('home');
  
  const handlePageChange = (page: 'home' | 'grouping' | 'saved-groupings' | 'help' | 'normalization' | 'autonormalization') => {
    setCurrentPage(page);
  };

  const goToHome = () => {
    setCurrentPage('home');
  };

  const renderPage = () => {
    switch (currentPage) {
      case 'home':
        return <HomePage onPageChange={handlePageChange} />;
      case 'grouping':
        return <GroupingView />;
      case 'saved-groupings':
        return <SavedGroupingsPage />;
      case 'help':
        return <HelpPage />;
      case 'normalization':
        return <NormalizationPage />;
      case 'autonormalization':
        return <AutoNormalization />;
      default:
        return <HomePage onPageChange={handlePageChange} />;
    }
  };

  return (
    <div className="app">
      <Header onHomeClick={goToHome} />
      <div className="main-container">
        {currentPage !== 'home' && (
          <Sidebar onPageChange={handlePageChange} currentPage={currentPage} />
        )}
        <main className={currentPage === 'home' ? "content full-width" : "content"}>
          {renderPage()}
        </main>
      </div>
    </div>
  );
};

export default App; 