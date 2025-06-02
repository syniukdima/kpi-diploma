import React, { useEffect } from 'react';
import './Sidebar.css';

interface SidebarProps {
  onPageChange: (page: 'home' | 'grouping' | 'saved-groupings' | 'help' | 'normalization' | 'autonormalization' | 'raw-metrics') => void;
  currentPage: 'home' | 'grouping' | 'saved-groupings' | 'help' | 'normalization' | 'autonormalization' | 'raw-metrics';
  isMobileMenuOpen: boolean;
  setIsMobileMenuOpen: (open: boolean) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ onPageChange, currentPage, isMobileMenuOpen, setIsMobileMenuOpen }) => {
  // Закриваємо меню при зміні розміру екрану
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth > 768) {
        setIsMobileMenuOpen(false);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [setIsMobileMenuOpen]);

  const handlePageChange = (page: 'home' | 'grouping' | 'saved-groupings' | 'help' | 'normalization' | 'autonormalization' | 'raw-metrics') => {
    onPageChange(page);
    setIsMobileMenuOpen(false); // Закриваємо меню після вибору сторінки
  };

  return (
    <>
      {/* Overlay для закриття меню */}
      <div 
        className={`mobile-overlay ${isMobileMenuOpen ? 'active' : ''}`}
        onClick={() => setIsMobileMenuOpen(false)}
      />

      {/* Сайдбар */}
      <nav className={`sidebar ${isMobileMenuOpen ? 'mobile-open' : ''}`}>
        <ul className="nav-list">
          <li>
            <a 
              href="#" 
              className={currentPage === 'home' ? 'active' : ''} 
              onClick={(e) => {
                e.preventDefault();
                handlePageChange('home');
              }}
            >
              Головна
            </a>
          </li>
          <li>
            <a 
              href="#" 
              className={currentPage === 'normalization' ? 'active' : ''} 
              onClick={(e) => {
                e.preventDefault();
                handlePageChange('normalization');
              }}
            >
              Нормалізація
            </a>
          </li>
          <li>
            <a 
              href="#" 
              className={currentPage === 'autonormalization' ? 'active' : ''}
              onClick={(e) => {
                e.preventDefault();
                handlePageChange('autonormalization');
              }}
            >
              Автонормалізація
            </a>
          </li>
          <li>
            <a 
              href="#" 
              className={currentPage === 'raw-metrics' ? 'active' : ''}
              onClick={(e) => {
                e.preventDefault();
                handlePageChange('raw-metrics');
              }}
            >
              Сирі метрики
            </a>
          </li>
          <li>
            <a 
              href="#" 
              className={currentPage === 'grouping' ? 'active' : ''} 
              onClick={(e) => {
                e.preventDefault();
                handlePageChange('grouping');
              }}
            >
              Групування
            </a>
          </li>
          <li>
            <a 
              href="#" 
              className={currentPage === 'saved-groupings' ? 'active' : ''} 
              onClick={(e) => {
                e.preventDefault();
                handlePageChange('saved-groupings');
              }}
            >
              Збережені групування
            </a>
          </li>
          <li>
            <a 
              href="#" 
              className={currentPage === 'help' ? 'active' : ''} 
              onClick={(e) => {
                e.preventDefault();
                handlePageChange('help');
              }}
            >
              Довідка
            </a>
          </li>
        </ul>
      </nav>
    </>
  );
};

export default Sidebar; 