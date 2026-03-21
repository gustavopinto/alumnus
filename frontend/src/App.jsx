import React, { useState, useEffect, useCallback } from 'react';
import { Routes, Route } from 'react-router-dom';
import GraphView from './components/GraphView';
import Sidebar from './components/Sidebar';
import Legend from './components/Legend';
import ProtectedRoute from './components/ProtectedRoute';
import ResearcherPage from './pages/StudentPage';
import RemindersPage from './pages/RemindersPage';
import BoardPage from './pages/BoardPage';
import ManualPage from './pages/ManualPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import { getGraph, getResearchers } from './api';
import Footer from './components/Footer';
import { removeToken, getTokenPayload } from './auth';

function shortName(fullName) {
  const parts = (fullName || '').trim().split(/\s+/);
  if (parts.length <= 1) return fullName;
  return `${parts[0]} ${parts[parts.length - 1]}`;
}

function GraphPage() {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [researchers, setResearchers] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(() => localStorage.getItem('sidebarOpen') !== 'false');

  const loadData = useCallback(async () => {
    const [graphData, researchersData] = await Promise.all([
      getGraph(),
      getResearchers(),
    ]);
    setNodes((graphData.nodes || []).map(n => ({
      ...n,
      data: { ...n.data, name: shortName(n.data.name), researcherId: n.id },
    })));
    setEdges(graphData.edges || []);
    setResearchers(researchersData || []);
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  return (
    <div className="h-screen flex">
      {sidebarOpen && (
        <aside className="w-80 border-r bg-gray-100 flex flex-col shrink-0">
          <div className="p-4 border-b bg-white flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-blue-700">Alumnus</h1>
              <p className="text-xs text-gray-500">Rede de pesquisa</p>
            </div>
            <button onClick={() => { removeToken(); window.location.href = '/login'; }}
              className="text-xs text-gray-400 hover:text-red-500">
              Sair
            </button>
          </div>
          <Sidebar researchers={researchers} onRefresh={loadData} role={getTokenPayload()?.role} />
          <Footer />
        </aside>
      )}
      <main className="flex-1 h-full relative">
        <button
          onClick={() => setSidebarOpen((o) => { const next = !o; localStorage.setItem('sidebarOpen', next); return next; })}
          className="absolute top-4 left-4 z-10 bg-white border rounded-lg p-1.5 shadow-md hover:bg-gray-50"
          title={sidebarOpen ? 'Esconder menu' : 'Mostrar menu'}
        >
          {sidebarOpen ? (
            <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7M18 19l-7-7 7-7" />
            </svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M6 5l7 7-7 7" />
            </svg>
          )}
        </button>
        <GraphView initialNodes={nodes} initialEdges={edges} />
        <Legend />
      </main>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login"    element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/" element={
        <ProtectedRoute professorOnly>
          <GraphPage />
        </ProtectedRoute>
      } />
      <Route path="/profile/:slug" element={
        <ProtectedRoute>
          <ResearcherPage />
        </ProtectedRoute>
      } />
      <Route path="/reminders" element={
        <ProtectedRoute professorOnly>
          <RemindersPage />
        </ProtectedRoute>
      } />
      <Route path="/board" element={
        <ProtectedRoute>
          <BoardPage />
        </ProtectedRoute>
      } />
      <Route path="/manual" element={
        <ProtectedRoute>
          <ManualPage />
        </ProtectedRoute>
      } />
    </Routes>
  );
}
