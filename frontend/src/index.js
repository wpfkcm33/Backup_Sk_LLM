// src/index.js
import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import UserApp from './UserApp';  // App 대신 UserApp import

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <UserApp />
  </React.StrictMode>
);