import React from 'react';
import { Routes, Route } from 'react-router-dom';
import AppLayout from './components/AppLayout';
import ProtectedRoute from './components/ProtectedRoute';
import GraphPage from './pages/GraphPage';
import ResearcherPage from './pages/StudentPage';
import RemindersPage from './pages/RemindersPage';
import BoardPage from './pages/BoardPage';
import ManualPage from './pages/ManualPage';
import DeadlinesPage from './pages/DeadlinesPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/" element={<AppLayout />}>
        <Route
          index
          element={
            <ProtectedRoute>
              <GraphPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="manual"
          element={
            <ProtectedRoute>
              <ManualPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="profile/:slug"
          element={
            <ProtectedRoute>
              <ResearcherPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="reminders"
          element={
            <ProtectedRoute>
              <RemindersPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="board"
          element={
            <ProtectedRoute>
              <BoardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="deadlines"
          element={
            <ProtectedRoute>
              <DeadlinesPage />
            </ProtectedRoute>
          }
        />
      </Route>
    </Routes>
  );
}
