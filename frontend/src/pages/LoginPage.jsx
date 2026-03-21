import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { saveToken } from '../auth';

function slugify(nome) {
  return (nome || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .toLowerCase().trim().replace(/[^a-z0-9\s-]/g, '').replace(/\s+/g, '-');
}

export default function LoginPage() {
  const navigate = useNavigate();
  const [form, setForm]     = useState({ email: '', password: '' });
  const [error, setError]   = useState('');
  const [loading, setLoading] = useState(false);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError('');

    const res  = await fetch('/api/auth/login', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(form),
    });
    const data = await res.json();
    setLoading(false);

    if (!res.ok) { setError(data.detail || 'Erro ao fazer login'); return; }

    saveToken(data.access_token);
    const payload = JSON.parse(atob(data.access_token.split('.')[1]));

    if (payload.role === 'student') {
      const stuRes = await fetch(`/api/researchers/${payload.researcher_id}`, {
        headers: { Authorization: `Bearer ${data.access_token}` },
      });
      const stu = await stuRes.json();
      navigate(`/profile/${slugify(stu.nome)}`, { replace: true });
    } else {
      navigate('/', { replace: true });
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="bg-white rounded-xl shadow-sm border p-8 w-full max-w-sm">
        <h1 className="text-2xl font-bold text-blue-700 mb-1">Alumnus</h1>
        <p className="text-sm text-gray-500 mb-6">Entre na sua conta</p>

        {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

        <form onSubmit={handleSubmit} className="space-y-4">
          <input type="email" required placeholder="Email"
            className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
            value={form.email} onChange={set('email')} />
          <input type="password" required placeholder="Senha"
            className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
            value={form.password} onChange={set('password')} />
          <button type="submit" disabled={loading}
            className="w-full bg-blue-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
            {loading ? 'Entrando...' : 'Entrar'}
          </button>
        </form>

        <p className="text-xs text-gray-500 mt-4 text-center">
          Não tem conta?{' '}
          <Link to="/register" className="text-blue-600 hover:underline">Cadastrar</Link>
        </p>
      </div>
    </div>
  );
}
