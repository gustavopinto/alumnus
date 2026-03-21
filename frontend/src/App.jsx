import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import AppLayout from './components/AppLayout';
import ProtectedRoute from './components/ProtectedRoute';
import GraphPage from './pages/GraphPage';
import ResearcherPage from './pages/ResearcherPage';
import RemindersPage from './pages/RemindersPage';
import BoardPage from './pages/BoardPage';
import ManualPage from './pages/ManualPage';
import DeadlinesPage from './pages/DeadlinesPage';
import AdminPage from './pages/AdminPage';
import AuthPage from './pages/AuthPage';
import LandingPage from './pages/LandingPage';


export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/entrar" element={<AuthPage />} />
      <Route path="/login" element={<Navigate to="/entrar" replace />} />
      <Route path="/register" element={<Navigate to="/entrar?tab=cadastro" replace />} />
      <Route path="/app" element={<AppLayout />}>
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
        <Route
          path="admin"
          element={
            <ProtectedRoute adminOnly>
              <AdminPage />
            </ProtectedRoute>
          }
        />
      </Route>
    </Routes>
  );
}
