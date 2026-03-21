import React, { useState } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { formatApiDetail, readResponseJson } from '../apiErrors';
import { modKey, isModEnter } from '../platform';
import {
  INSTITUTIONAL_EMAIL_ERROR_PT,
  REGISTER_PROFESSOR_ONLY_HINT_PT,
  isPublicEmailDomain,
} from '../institutionalEmail';

export default function RegisterPage() {
  const navigate  = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';
  const inviteEmail = token ? (() => { try { return atob(token); } catch { return ''; } })() : '';
  const [form, setForm] = useState({ email: inviteEmail, password: '' });
  const [error,   setError]   = useState('');
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
        setError(
          formatApiDetail(data) ||
            `Não foi possível processar a resposta (${res.status}). Tente novamente.`,
        );
        return;
      }
      if (!res.ok) {
        console.error('[register] Falha na API', { status: res.status, body: data });
        setError(formatApiDetail(data) || 'Erro ao cadastrar');
        return;
      }
      navigate('/login');
    } catch (err) {
      console.error('[register] Erro inesperado', err);
      const offline =
        err instanceof TypeError ||
        (typeof err?.message === 'string' && err.message.includes('fetch'));
      setError(
        offline
          ? 'Não foi possível conectar ao servidor. Verifique sua internet.'
          : 'Falha inesperada. Tente novamente.',
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="bg-white rounded-xl shadow-sm border p-8 w-full max-w-sm">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center shrink-0">
            <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5}
                d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-blue-700">Alumnus</h1>
        </div>
        <p className="text-sm text-gray-500 mb-1">Criar conta</p>
        <p className="text-xs text-gray-600 mb-3 leading-relaxed">{REGISTER_PROFESSOR_ONLY_HINT_PT}</p>
        {inviteEmail && (
          <p className="text-xs text-blue-600 bg-blue-50 border border-blue-100 rounded-lg px-3 py-2 mb-4">
            Você foi convidado para ativar sua conta. Defina uma senha para continuar.
          </p>
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
            {loading ? 'Cadastrando...' : <><span>Criar conta</span> <span className="opacity-50 text-xs">{modKey}+Enter</span></>}
          </button>
        </form>

        <p className="text-xs text-gray-500 mt-4 text-center">
          Já tem conta?{' '}
          <Link to="/login" className="text-blue-600 hover:underline">Entrar</Link>
        </p>
      </div>
    </div>
  );
}
