import React from 'react';
import './Header.css';

interface HeaderProps {
  onHomeClick: () => void;
}

const Header: React.FC<HeaderProps> = ({ onHomeClick }) => {
  return (
    <header className="header">
      <div className="logo">
        <a href="#" className="home-link" onClick={(e) => {
          e.preventDefault();
          onHomeClick();
        }}>
          <h1>Групування мікросервісів</h1>
        </a>
      </div>
    </header>
  );
};

export default Header; 