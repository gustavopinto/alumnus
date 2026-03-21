import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { getDeadlineInterests, toggleDeadlineInterest } from '../api';
import { getTokenPayload } from '../auth';
import { DEADLINES, daysUntil, slugify } from '../deadlines';

/** Slug do perfil: API ou derivado do nome (alinhado ao grafo / perfil). */
function profileSlugForInterest(i) {
  const fromApi = i.profile_slug && String(i.profile_slug).trim();
  if (fromApi) return fromApi;
  if (i.user_name) return slugify(i.user_name);
  return '';
}

function Avatar({ name, photoUrl, size = 7 }) {
  const initials = (name || '?').split(' ').filter(Boolean).slice(0, 2).map(p => p[0].toUpperCase()).join('');
  const sizeClass = `w-${size} h-${size}`;
  if (photoUrl) {
    return (
      <img
        src={photoUrl}
        alt={name}
        title={name}
        className={`${sizeClass} rounded-full object-cover border-2 border-white ring-1 ring-gray-200`}
      />
    );
  }
  return (
    <span
      title={name}
      className={`${sizeClass} rounded-full bg-blue-100 text-blue-700 text-xs font-bold border-2 border-white ring-1 ring-gray-200 flex items-center justify-center shrink-0`}
    >
      {initials}
    </span>
  );
}

export default function DeadlinesPage() {
  const [interests, setInterests] = useState([]);
  const [showPast, setShowPast] = useState(false);
  const [loading, setLoading] = useState(false);
  const payload = getTokenPayload();
  const myUserId = payload?.sub != null ? Number(payload.sub) : null;

  const load = useCallback(async () => {
    const data = await getDeadlineInterests();
    setInterests(data || []);
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleToggle(key) {
    if (loading) return;
    setLoading(true);
    try {
      await toggleDeadlineInterest(key);
    } catch (e) {
      console.error(e);
    } finally {
      await load();
      setLoading(false);
    }
  }

  const upcoming = DEADLINES.filter(d => daysUntil(d.date) >= 0).sort((a, b) => new Date(a.date) - new Date(b.date));
  const past = DEADLINES.filter(d => daysUntil(d.date) < 0).sort((a, b) => new Date(b.date) - new Date(a.date));

  function renderCard(d) {
    const days = daysUntil(d.date);
    const isPast = days < 0;
    const urgent = !isPast && days <= 14;
    const myInterest = interests.some(
      (i) => i.deadline_key === d.label && myUserId != null && Number(i.user_id) === myUserId,
    );
    const interested = interests.filter(i => i.deadline_key === d.label);

    return (
      <div
        key={d.label}
        className={`relative bg-white rounded-xl border shadow-sm p-4 flex flex-col gap-3 transition-opacity ${isPast ? 'opacity-60' : ''}`}
      >
        {/* Avatares dos interessados */}
        {interested.length > 0 && (
          <div className="absolute top-3 right-3 flex -space-x-2">
            {interested.slice(0, 5).map(i => {
              const slug = profileSlugForInterest(i);
              return slug ? (
                <Link
                  key={i.user_id}
                  to={`/profile/${slug}`}
                  className="inline-block ring-2 ring-white rounded-full"
                  title={`Perfil de ${i.user_name}`}
                >
                  <Avatar name={i.user_name} photoUrl={i.user_photo_url} size={7} />
                </Link>
              ) : (
                <Avatar key={i.user_id} name={i.user_name} photoUrl={i.user_photo_url} size={7} />
              );
            })}
            {interested.length > 5 && (
              <span className="w-7 h-7 rounded-full bg-gray-200 text-gray-600 text-xs font-bold border-2 border-white flex items-center justify-center">
                +{interested.length - 5}
              </span>
            )}
          </div>
        )}

        {/* Nome + link */}
        <div className="pr-20">
          <a
            href={d.url}
            target="_blank"
            rel="noreferrer"
            className="text-base font-semibold text-blue-700 hover:underline"
          >
            {d.label}
          </a>
          <p className={`text-sm mt-0.5 ${isPast ? 'text-gray-400' : urgent ? 'text-orange-500 font-semibold' : 'text-gray-500'}`}>
            {isPast
              ? `Encerrado · ${new Date(d.date + 'T00:00:00').toLocaleDateString('pt-BR')}`
              : days === 0
                ? `Hoje! · ${new Date(d.date + 'T00:00:00').toLocaleDateString('pt-BR')}`
                : `${days} dia${days !== 1 ? 's' : ''} · ${new Date(d.date + 'T00:00:00').toLocaleDateString('pt-BR')}`}
          </p>
        </div>

        {interested.length > 0 && (
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs">
            <span className="text-gray-400 shrink-0">Quem vai mandar:</span>
            {interested.map((i, idx) => {
              const slug = profileSlugForInterest(i);
              return (
                <span key={i.user_id} className="inline-flex items-center gap-1">
                  {idx > 0 && <span className="text-gray-300">·</span>}
                  {slug ? (
                    <Link to={`/profile/${slug}`} className="font-medium text-blue-600 hover:underline">
                      {i.user_name}
                    </Link>
                  ) : (
                    <span className="font-medium text-gray-700">{i.user_name}</span>
                  )}
                </span>
              );
            })}
          </div>
        )}

        {/* Botão de interesse */}
        {!isPast && (
          <button
            type="button"
            disabled={loading}
            onClick={() => handleToggle(d.label)}
            className={`self-start text-xs px-3 py-1.5 rounded-lg border font-medium transition-colors disabled:opacity-50 ${
              myInterest
                ? 'bg-green-50 border-green-300 text-green-700 hover:bg-red-50 hover:border-red-300 hover:text-red-600'
                : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-blue-50 hover:border-blue-300 hover:text-blue-700'
            }`}
          >
            {myInterest ? '✓ Quero mandar' : 'Quero mandar'}
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-8">
      <h1 className="text-2xl font-bold text-gray-800">Deadlines</h1>

      {/* Próximos */}
      <section className="space-y-3">
        {upcoming.length === 0 ? (
          <p className="text-sm text-gray-400 italic">Nenhum deadline próximo.</p>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {upcoming.map(renderCard)}
          </div>
        )}
      </section>

      {/* Passados */}
      <section>
        <button
          type="button"
          onClick={() => setShowPast(o => !o)}
          className="flex items-center gap-1.5 text-sm text-gray-400 hover:text-gray-600 mb-3"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className={`w-4 h-4 transition-transform ${showPast ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
          {past.length} deadline{past.length !== 1 ? 's' : ''} encerrado{past.length !== 1 ? 's' : ''}
        </button>
        {showPast && (
          <div className="grid gap-3 sm:grid-cols-2">
            {past.map(renderCard)}
          </div>
        )}
      </section>
    </div>
  );
}
