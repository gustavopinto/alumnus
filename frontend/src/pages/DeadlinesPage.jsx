import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { getDeadlineInterests, toggleDeadlineInterest, extractDeadlineFromUrl } from '../api';
import { getTokenPayload } from '../auth';
import { DEADLINES, daysUntil, slugify } from '../deadlines';
import { modKey, isModEnter } from '../platform';

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

  const [extractOpen, setExtractOpen] = useState(false);
  const [extractUrl, setExtractUrl] = useState('');
  const [extracting, setExtracting] = useState(false);
  const [extracted, setExtracted] = useState(null);  // list | null
  const [extractError, setExtractError] = useState('');

  const isValidUrl = (() => {
    try { const u = new URL(extractUrl.trim()); return ['http:', 'https:'].includes(u.protocol); }
    catch { return false; }
  })();

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

  async function handleExtract(e) {
    e.preventDefault();
    if (!isValidUrl) return;
    setExtracting(true);
    setExtracted(null);
    setExtractError('');
    try {
      const result = await extractDeadlineFromUrl(extractUrl.trim());
      if (!Array.isArray(result)) {
        setExtractError(result?.detail || 'Não foi possível acessar a URL.');
      } else if (result.length === 0) {
        setExtractError('Nenhum deadline encontrado na página.');
      } else {
        setExtracted(result);
      }
    } catch {
      setExtractError('Não foi possível acessar a URL. Verifique o endereço e tente novamente.');
    } finally {
      setExtracting(false);
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
    const myEntry =
      myUserId != null ? interested.find((i) => Number(i.user_id) === myUserId) : null;
    const myPic = myEntry ? (myEntry.user_photo_thumb_url || myEntry.user_photo_url) : null;

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
              const pic = i.user_photo_thumb_url || i.user_photo_url;
              return slug ? (
                <Link
                  key={i.user_id}
                  to={`/app/profile/${slug}`}
                  className="inline-block ring-2 ring-white rounded-full"
                  title={`Perfil de ${i.user_name}`}
                >
                  <Avatar name={i.user_name} photoUrl={pic} size={7} />
                </Link>
              ) : (
                <Avatar key={i.user_id} name={i.user_name} photoUrl={pic} size={7} />
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
                    <Link to={`/app/profile/${slug}`} className="font-medium text-blue-600 hover:underline">
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
            className={`self-start inline-flex items-center gap-2 text-xs px-3 py-1.5 rounded-lg border font-medium transition-colors disabled:opacity-50 ${
              myInterest
                ? 'bg-green-50 border-green-300 text-green-700 hover:bg-red-50 hover:border-red-300 hover:text-red-600'
                : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-blue-50 hover:border-blue-300 hover:text-blue-700'
            }`}
          >
            {myInterest && myPic && (
              <img
                src={myPic}
                alt=""
                className="w-5 h-5 rounded-full object-cover border border-green-200 shrink-0"
              />
            )}
            <span>{myInterest ? '✓ Quero mandar' : 'Quero mandar'}</span>
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="min-h-full bg-gray-50">
      <div className="max-w-3xl mx-auto p-6 space-y-8">

      {/* Extrair deadline por URL */}
      <section className="bg-white rounded-xl border shadow-sm overflow-hidden">
        <button
          type="button"
          onClick={() => { setExtractOpen(o => !o); setExtracted(null); setExtractError(''); }}
          className="w-full flex items-center justify-between px-5 py-3 text-left hover:bg-gray-50 transition-colors"
        >
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-gray-700">Extrair deadline de uma URL</span>
            <span className="text-[10px] font-semibold uppercase tracking-wide text-amber-600 bg-amber-50 border border-amber-200 rounded px-1.5 py-0.5">
              experimental
            </span>
          </div>
          <svg xmlns="http://www.w3.org/2000/svg" className={`w-4 h-4 text-gray-400 transition-transform ${extractOpen ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        {extractOpen && (
          <div className="px-5 pb-5 space-y-3 border-t">
            <form onSubmit={handleExtract} className="space-y-1.5 pt-4">
            <div className="flex gap-2">
              <div className="flex-1 flex flex-col gap-1">
                <input
                  type="text"
                  value={extractUrl}
                  onChange={e => { setExtractUrl(e.target.value); setExtractError(''); }}
                  onKeyDown={e => isModEnter(e) && isValidUrl && !extracting && handleExtract(e)}
                  placeholder="https://conf.example.org/2026"
                  className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 ${extractError ? 'border-red-400 focus:ring-red-300' : 'focus:ring-blue-400'}`}
                />
                {extractError && (
                  <p className="text-xs text-red-500">{extractError}</p>
                )}
              </div>
              <button
                type="submit"
                disabled={extracting || !isValidUrl}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40 shrink-0 self-start"
              >
                Extrair <span className="opacity-50 text-xs">{modKey}+Enter</span>
              </button>
            </div>
            </form>

            {extracting && (
              <div className="flex items-center gap-2 text-sm text-gray-500 py-1">
                <svg className="w-4 h-4 animate-spin text-blue-500 shrink-0" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Processando… o deadline aparecerá em instantes.
              </div>
            )}

            {extracted && extracted.length > 0 && (
              <div className="space-y-2">
                {extracted.map((d, i) => (
                  <div key={i} className="flex flex-wrap items-center gap-3 rounded-lg border bg-gray-50 px-4 py-3 text-sm">
                    <span className="font-semibold text-gray-800">{d.label}</span>
                    <span className="text-gray-400">·</span>
                    <span className="text-blue-700 font-medium">
                      {new Date(d.date + 'T00:00:00').toLocaleDateString('pt-BR')}
                    </span>
                    <a
                      href={d.url}
                      target="_blank"
                      rel="noreferrer"
                      className="ml-auto text-xs text-blue-500 hover:underline truncate max-w-[14rem]"
                    >
                      {d.url}
                    </a>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </section>

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
          {past.length} deadline{past.length !== 1 ? 's' : ''} passado{past.length !== 1 ? 's' : ''}
        </button>
        {showPast && (
          <div className="grid gap-3 sm:grid-cols-2">
            {past.map(renderCard)}
          </div>
        )}
      </section>
      </div>
    </div>
  );
}
