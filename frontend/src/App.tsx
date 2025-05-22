import React, { useState } from 'react';
import './App.css';

// Імпорт компонентів сторінок
import Header from './components/Header.tsx';
import Sidebar from './components/Sidebar.tsx';
import GroupingView from './pages/GroupingView.tsx';
import HelpPage from './pages/HelpPage.tsx';
import SavedGroupingsPage from './pages/SavedGroupingsPage.tsx';

const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<'grouping' | 'saved-groupings' | 'help'>('grouping');
  
  const handlePageChange = (page: 'grouping' | 'saved-groupings' | 'help') => {
    setCurrentPage(page);
  };

  const renderPage = () => {
    switch (currentPage) {
      case 'grouping':
        return <GroupingView />;
      case 'saved-groupings':
        return <SavedGroupingsPage />;
      case 'help':
        return <HelpPage />;
      default:
        return <GroupingView />;
    }
  };

  return (
    <div className="app">
      <Header />
      <div className="main-container">
        <Sidebar onPageChange={handlePageChange} currentPage={currentPage} />
        <main className="content">
          {renderPage()}
        </main>
      </div>
    </div>
  );
};

export default App; 