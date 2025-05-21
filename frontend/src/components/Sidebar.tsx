import React from 'react';
import { NavLink } from 'react-router-dom';
import './Sidebar.css';

const Sidebar: React.FC = () => {
  return (
    <nav className="sidebar">
      <ul className="nav-list">
        <li>
          <NavLink to="/" className={({ isActive }) => isActive ? 'active' : ''}>
            Головна
          </NavLink>
        </li>
        {/* Тимчасово приховано
        <li>
          <NavLink to="/microservices" className={({ isActive }) => isActive ? 'active' : ''}>
            Мікросервіси
          </NavLink>
        </li>
        */}
        <li>
          <NavLink to="/grouping" className={({ isActive }) => isActive ? 'active' : ''}>
            Групування
          </NavLink>
        </li>
        {/* Тимчасово приховано
        <li>
          <NavLink to="/stability" className={({ isActive }) => isActive ? 'active' : ''}>
            Стабільність
          </NavLink>
        </li>
        */}
      </ul>
    </nav>
  );
};

export default Sidebar; 