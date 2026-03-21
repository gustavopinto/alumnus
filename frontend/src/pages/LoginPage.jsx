import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { saveToken } from '../auth';
import { formatApiDetail, readResponseJson } from '../apiErrors';
import { modKey, isModEnter } from '../platform';

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
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      const data = await readResponseJson(res, 'login');

      if (data._invalidJson) {
        setError(
          res.ok
            ? 'Resposta inválida do servidor.'
            : `Não foi possível processar a resposta (${res.status}). Tente novamente.`,
        );
        return;
      }

      if (!res.ok) {
        const msg = formatApiDetail(data) || 'Erro ao fazer login';
        console.error('[login] Falha na API', { status: res.status, body: data });
        setError(msg);
        return;
      }

      if (!data.access_token) {
        console.error('[login] Resposta sem access_token', data);
        setError('Resposta inesperada do servidor.');
        return;
      }

      saveToken(data.access_token);
      let payload;
      try {
        payload = JSON.parse(atob(data.access_token.split('.')[1]));
      } catch (err) {
        console.error('[login] Token JWT ilegível', err);
        setError('Sessão inválida recebida do servidor.');
        return;
      }

      if (payload.role === 'student') {
        if (!payload.researcher_id) {
          navigate('/manual', { replace: true });
        } else {
          const stuRes = await fetch(`/api/researchers/${payload.researcher_id}`, {
            headers: { Authorization: `Bearer ${data.access_token}` },
          });
          const stu = await readResponseJson(stuRes, 'login.profile');
          if (stu._invalidJson) {
            console.error('[login] Perfil: JSON inválido', stuRes.status);
            setError('Login ok, mas a resposta do perfil veio inválida. Tente de novo.');
            return;
          }
          if (!stuRes.ok) {
            const msg = formatApiDetail(stu) || 'Não foi possível carregar seu perfil.';
            console.error('[login] Falha ao buscar pesquisador', { status: stuRes.status, body: stu });
            setError(msg);
            return;
          }
          if (!stu.nome) {
            console.error('[login] Perfil sem nome', stu);
            setError('Perfil incompleto. Contate o suporte.');
            return;
          }
          navigate(`/profile/${slugify(stu.nome)}`, { replace: true });
        }
      } else {
        navigate('/', { replace: true });
      }
    } catch (err) {
      console.error('[login] Erro inesperado', err);
      const offline =
        err instanceof TypeError ||
        (typeof err?.message === 'string' && err.message.includes('fetch'));
      setError(
        offline
          ? 'Não foi possível conectar ao servidor. Verifique sua internet e tente de novo.'
          : 'Falha inesperada. Tente novamente.',
      );
    } finally {
      setLoading(false);
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
            value={form.password} onChange={set('password')}
            onKeyDown={e => isModEnter(e) && handleSubmit(e)} />
          <button type="submit" disabled={loading}
            className="w-full bg-blue-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
            {loading ? 'Entrando...' : <><span>Entrar</span> <span className="opacity-50 text-xs">{modKey}+Enter</span></>}
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
