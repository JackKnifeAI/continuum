/**
 * Sidebar Entry Point
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import { Sidebar } from './Sidebar';
import '../styles/sidebar.css';

const root = document.getElementById('root');
if (root) {
  ReactDOM.createRoot(root).render(
    <React.StrictMode>
      <Sidebar />
    </React.StrictMode>
  );
}
