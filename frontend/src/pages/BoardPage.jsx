import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getBoardPosts, createBoardPost, deleteBoardPost } from '../api';
import { getTokenPayload } from '../auth';
import Toast from '../components/Toast';
import Footer from '../components/Footer';

function formatDate(iso) {
  return new Date(iso).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

export default function BoardPage() {
  const navigate = useNavigate();
  const [posts, setPosts] = useState([]);
  const [text, setText] = useState('');
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState('');

  const payload = getTokenPayload();
  const isProfessor = payload?.role === 'professor';
  const currentUserId = payload ? parseInt(payload.sub) : null;

  async function load() {
    const data = await getBoardPosts();
    setPosts(data || []);
  }

  useEffect(() => { load(); }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!text.trim()) return;
    setSaving(true);
    await createBoardPost({ text: text.trim() });
    setText('');
    setSaving(false);
    setToast('Post adicionado!');
    load();
  }

  async function handleDelete(id) {
    if (!confirm('Remover este post?')) return;
    await deleteBoardPost(id);
    load();
  }

  return (
    <div className="min-h-screen bg-amber-50">
      <Toast message={toast} onClose={() => setToast('')} />
      <header className="bg-white border-b shadow-sm px-6 py-4 flex items-center gap-4">
        <button onClick={() => navigate('/')} className="text-gray-500 hover:text-gray-800 text-sm flex items-center gap-1">
          <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Retornar
        </button>
        <div className="w-px h-6 bg-gray-200" />
        <h1 className="text-xl font-bold text-gray-900">Mural</h1>
      </header>

      <main className="max-w-5xl mx-auto py-8 px-4">
        {/* Add post form */}
        <form onSubmit={handleSubmit} className="mb-8 flex gap-3 items-start">
          <textarea
            className="flex-1 border rounded-xl px-4 py-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-yellow-400 resize-none"
            placeholder="Adicione uma nota..."
            rows={3}
            maxLength={200}
            value={text}
            onChange={e => setText(e.target.value)}
          />
          <button
            type="submit"
            disabled={saving || !text.trim()}
            className="bg-yellow-400 hover:bg-yellow-500 text-yellow-900 font-medium px-5 py-2 rounded-xl text-sm shadow-sm disabled:opacity-40 transition-colors"
          >
            + Adicionar
          </button>
        </form>

        {/* Post-its grid */}
        {posts.length === 0 && (
          <p className="text-center text-gray-400 italic mt-16">Nenhuma nota no mural ainda.</p>
        )}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
          {posts.map(post => {
            const canDelete = isProfessor || post.author_id === currentUserId;
            return (
              <div
                key={post.id}
                className="bg-yellow-200 rounded-lg shadow-md p-4 flex flex-col gap-2 relative group"
                style={{ minHeight: '140px' }}
              >
                <p className="text-sm text-gray-800 whitespace-pre-wrap flex-1 leading-relaxed">{post.text}</p>
                <div className="border-t border-yellow-300 pt-2 mt-auto">
                  <p className="text-xs text-yellow-700 font-medium truncate">{post.author_name || 'Anônimo'}</p>
                  <p className="text-xs text-yellow-600">{formatDate(post.created_at)}</p>
                </div>
                {canDelete && (
                  <button
                    onClick={() => handleDelete(post.id)}
                    className="absolute top-2 right-2 text-yellow-500 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                    title="Remover"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  </button>
                )}
              </div>
            );
          })}
        </div>
      </main>
      <Footer />
    </div>
  );
}
