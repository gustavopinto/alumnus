import React, { useState } from 'react';
import { useNavigate, useSearchParams, Link, Navigate } from 'react-router-dom';
import { saveToken, getToken } from '../auth';
import { formatApiDetail, readResponseJson } from '../apiErrors';
import { modKey, isModEnter } from '../platform';
import {
  INSTITUTIONAL_EMAIL_ERROR_PT,
  REGISTER_PROFESSOR_ONLY_HINT_PT,
  isPublicEmailDomain,
} from '../institutionalEmail';

function slugify(nome) {
  return (nome || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .toLowerCase().trim().replace(/[^a-z0-9\s-]/g, '').replace(/\s+/g, '-');
}

const LOGO = (
  <Link to="/" className="flex items-center gap-2 mb-6">
    <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center shrink-0">
      <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5}
          d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    </div>
    <span className="text-2xl font-bold text-blue-700">Alumnus</span>
  </Link>
);

function LoginForm({ onSuccess }) {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      const data = await readResponseJson(res, 'login');
      if (data._invalidJson) {
        setError(res.ok ? 'Resposta inválida do servidor.' : `Erro ${res.status}. Tente novamente.`);
        return;
      }
      if (!res.ok) {
        setError(formatApiDetail(data) || 'Erro ao fazer login');
        return;
      }
      if (!data.access_token) {
        setError('Resposta inesperada do servidor.');
        return;
      }
      saveToken(data.access_token);
      let payload;
      try {
        payload = JSON.parse(atob(data.access_token.split('.')[1]));
      } catch {
        setError('Sessão inválida recebida do servidor.');
        return;
      }
      if (payload.role === 'researcher') {
        if (!payload.researcher_id) {
          navigate('/app/manual', { replace: true });
        } else {
          const stuRes = await fetch(`/api/researchers/${payload.researcher_id}`, {
            headers: { Authorization: `Bearer ${data.access_token}` },
          });
          const stu = await readResponseJson(stuRes, 'login.profile');
          if (!stuRes.ok || stu._invalidJson) {
            setError('Login ok, mas não foi possível carregar seu perfil.');
            return;
          }
          navigate(`/app/profile/${slugify(stu.nome)}`, { replace: true });
        }
      } else {
        navigate('/app', { replace: true });
      }
    } catch (err) {
      const offline = err instanceof TypeError || err?.message?.includes('fetch');
      setError(offline ? 'Não foi possível conectar ao servidor.' : 'Falha inesperada. Tente novamente.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      {error && <p className="text-sm text-red-600 mb-4">{error}</p>}
      <form onSubmit={handleSubmit} className="space-y-4">
        <input type="email" required placeholder="Email"
          className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          value={form.email} onChange={set('email')} />
        <input type="password" required placeholder="Senha"
          className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          value={form.password} onChange={set('password')}
          onKeyDown={e => isModEnter(e) && handleSubmit(e)} />
        <button type="submit" disabled={loading}
          className="w-full bg-blue-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
          {loading ? 'Entrando...' : <><span>Entrar</span> <span className="opacity-50 text-xs ml-1">{modKey}+Enter</span></>}
        </button>
      </form>
    </>
  );
}

function RegisterForm({ inviteEmail }) {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: inviteEmail, password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError('');
    if (!inviteEmail && isPublicEmailDomain(form.email)) {
      setError(INSTITUTIONAL_EMAIL_ERROR_PT);
      setLoading(false);
      return;
    }
    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      const data = await readResponseJson(res, 'register');
      if (data._invalidJson) {
        setError(`Erro ${res.status}. Tente novamente.`);
        return;
      }
      if (!res.ok) {
        setError(formatApiDetail(data) || 'Erro ao cadastrar');
        return;
      }
      if (inviteEmail) {
        const loginRes = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: form.email, password: form.password }),
        });
        const loginData = await readResponseJson(loginRes, 'auto-login');
        if (loginRes.ok && loginData.access_token) {
          saveToken(loginData.access_token);
          let payload;
          try { payload = JSON.parse(atob(loginData.access_token.split('.')[1])); } catch { payload = {}; }
          if (payload.researcher_id) {
            const stuRes = await fetch(`/api/researchers/${payload.researcher_id}`, {
              headers: { Authorization: `Bearer ${loginData.access_token}` },
            });
            if (stuRes.ok) {
              const stu = await stuRes.json();
              navigate(`/app/profile/${slugify(stu.nome)}`, { replace: true });
              return;
            }
          }
          navigate('/app', { replace: true });
          return;
        }
      }
      navigate('/entrar', { replace: true });
    } catch (err) {
      const offline = err instanceof TypeError || err?.message?.includes('fetch');
      setError(offline ? 'Não foi possível conectar ao servidor.' : 'Falha inesperada. Tente novamente.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      {inviteEmail ? (
        <p className="text-xs text-blue-600 bg-blue-50 border border-blue-100 rounded-lg px-3 py-2 mb-4">
          Você foi convidado para ativar sua conta. Defina uma senha para continuar.
        </p>
      ) : (
        <p className="text-xs text-gray-600 mb-3 leading-relaxed">{REGISTER_PROFESSOR_ONLY_HINT_PT}</p>
      )}
      {error && <p className="text-sm text-red-600 mb-4">{error}</p>}
      <form onSubmit={handleSubmit} className="space-y-4">
        <input type="email" required placeholder="E-mail institucional (universidade)"
          className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 ${inviteEmail ? 'bg-gray-50 text-gray-500 cursor-not-allowed' : ''}`}
          value={form.email} onChange={set('email')} readOnly={!!inviteEmail} />
        <input type="password" required placeholder="Senha (mín. 8 caracteres)"
          className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          value={form.password} onChange={set('password')}
          onKeyDown={e => isModEnter(e) && handleSubmit(e)} />
        <button type="submit" disabled={loading}
          className="w-full bg-blue-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
          {loading ? 'Cadastrando...' : <><span>Criar conta</span> <span className="opacity-50 text-xs ml-1">{modKey}+Enter</span></>}
        </button>
      </form>
    </>
  );
}

export default function AuthPage() {
  if (getToken()) return <Navigate to="/app" replace />;
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';
  const inviteEmail = token ? (() => { try { return atob(token); } catch { return ''; } })() : '';
  const defaultTab = (searchParams.get('tab') === 'cadastro' || inviteEmail) ? 'cadastro' : 'entrar';
  const [tab, setTab] = useState(defaultTab);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="bg-white rounded-xl shadow-sm border p-8 w-full max-w-sm">
        {LOGO}

        {/* Toggle */}
        <div className="flex rounded-lg border border-gray-200 p-1 mb-6 bg-gray-50">
          <button
            type="button"
            onClick={() => setTab('entrar')}
            className={`flex-1 py-1.5 text-sm font-medium rounded-md transition-colors ${
              tab === 'entrar'
                ? 'bg-white text-blue-700 shadow-sm border border-gray-200'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Entrar
          </button>
          <button
            type="button"
            onClick={() => setTab('cadastro')}
            className={`flex-1 py-1.5 text-sm font-medium rounded-md transition-colors ${
              tab === 'cadastro'
                ? 'bg-white text-blue-700 shadow-sm border border-gray-200'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Cadastrar
          </button>
        </div>

        {tab === 'entrar' ? (
          <LoginForm />
        ) : (
          <RegisterForm inviteEmail={inviteEmail} />
        )}
      </div>
    </div>
  );
}
