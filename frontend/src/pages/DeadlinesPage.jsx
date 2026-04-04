import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getDeadlines, createDeadline, deleteDeadline, getDeadlineInterests, toggleDeadlineInterest, extractDeadlineFromUrl } from '../api';
import { getTokenPayload, isDashboardRole } from '../auth';
import { daysUntil, slugify } from '../deadlines';
import { modKey, isModEnter } from '../platform';
import { useAppLayout } from '../components/AppLayout';
import Toast from '../components/Toast';
import { keys } from '../queryKeys';
import { useConfirm } from '../components/ConfirmModal';

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
    return <img src={photoUrl} alt={name} title={name} className={`${sizeClass} rounded-full object-cover border-2 border-white ring-1 ring-gray-200`} />;
  }
  return (
    <span title={name} className={`${sizeClass} rounded-full bg-blue-100 text-blue-700 text-xs font-bold border-2 border-white ring-1 ring-gray-200 flex items-center justify-center shrink-0`}>
      {initials}
    </span>
  );
}

export default function DeadlinesPage() {
  const { currentInstitution } = useAppLayout();
  const instId = currentInstitution !== undefined ? (currentInstitution?.id ?? null) : undefined;
  const queryClient = useQueryClient();
  const payload = getTokenPayload();
  const myUserId = payload?.sub != null ? Number(payload.sub) : null;
  const canManage = isDashboardRole(payload?.role);
  const { confirm, modal: confirmModal } = useConfirm();

  const { data: deadlines = [] } = useQuery({
    queryKey: keys.deadlines(instId),
    queryFn: () => getDeadlines(instId),
    enabled: instId !== undefined,
  });

  const { data: interests = [] } = useQuery({
    queryKey: [...keys.deadlines(instId), 'interests'],
    queryFn: () => getDeadlineInterests(instId),
    enabled: instId !== undefined,
  });

  const invalidateDeadlines = () => {
    queryClient.invalidateQueries({ queryKey: keys.deadlines(instId) });
  };

  const toggleMutation = useMutation({
    mutationFn: (deadlineId) => toggleDeadlineInterest(deadlineId),
    onSuccess: invalidateDeadlines,
  });

  const deleteMutation = useMutation({
    mutationFn: (deadlineId) => deleteDeadline(deadlineId),
    onSuccess: () => { invalidateDeadlines(); setToast('Deadline removido'); },
  });

  const createMutation = useMutation({
    mutationFn: (data) => createDeadline({ ...data, institution_id: instId }),
    onSuccess: () => { invalidateDeadlines(); setToast('Deadline adicionado'); },
  });

  const [showPast, setShowPast] = useState(false);
  const [extractOpen, setExtractOpen] = useState(false);
  const [extractUrl, setExtractUrl] = useState('');
  const [extracting, setExtracting] = useState(false);
  const [extracted, setExtracted] = useState(null);
  const [extractError, setExtractError] = useState('');
  const [saving, setSaving] = useState({});
  const [toast, setToast] = useState('');
  const [addOpen, setAddOpen] = useState(false);
  const [addLabel, setAddLabel] = useState('');
  const [addUrl, setAddUrl] = useState('');
  const [addDate, setAddDate] = useState(() => new Date().toISOString().split('T')[0]);
  const [addError, setAddError] = useState('');

  const isValidUrl = (() => {
    try { const u = new URL(extractUrl.trim()); return ['http:', 'https:'].includes(u.protocol); }
    catch { return false; }
  })();

  async function handleToggle(deadlineId) {
    try { await toggleMutation.mutateAsync(deadlineId); }
    catch (e) { console.error(e); }
  }

  async function handleDelete(deadlineId) {
    if (!await confirm({ title: 'Remover este deadline?', confirmLabel: 'Remover' })) return;
    await deleteMutation.mutateAsync(deadlineId);
  }

  async function handleAddManual(e) {
    e.preventDefault();
    if (!addLabel.trim() || !addUrl.trim() || !addDate) return;
    setAddError('');
    try {
      await createMutation.mutateAsync({ label: addLabel.trim(), url: addUrl.trim(), date: addDate });
      setAddLabel(''); setAddUrl(''); setAddDate(new Date().toISOString().split('T')[0]); setAddOpen(false);
    } catch { setAddError('Erro ao adicionar deadline'); }
  }

  async function handleSaveExtracted(d, idx) {
    setSaving(s => ({ ...s, [idx]: true }));
    try {
      await createMutation.mutateAsync({ label: d.label, url: d.url, date: d.date });
      setExtracted(prev => prev.filter((_, i) => i !== idx));
    } catch (e) { console.error(e); }
    finally { setSaving(s => ({ ...s, [idx]: false })); }
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

  const upcoming = deadlines.filter(d => daysUntil(d.date) >= 0).sort((a, b) => new Date(a.date) - new Date(b.date));
  const past = deadlines.filter(d => daysUntil(d.date) < 0).sort((a, b) => new Date(b.date) - new Date(a.date));

  function renderCard(d) {
    const days = daysUntil(d.date);
    const isPast = days < 0;
    const urgent = !isPast && days <= 14;
    const myInterest = interests.some(i => i.deadline_id === d.id && myUserId != null && Number(i.user_id) === myUserId);
    const interested = interests.filter(i => i.deadline_id === d.id);
    return (
      <div key={d.id} className={`relative bg-white rounded-xl border shadow-sm p-4 flex flex-col gap-3 transition-opacity ${isPast ? 'opacity-60' : ''}`}>
        {interested.length > 0 && (
          <div className="absolute top-3 right-3 flex -space-x-2">
            {interested.slice(0, 5).map(i => {
              const slug = profileSlugForInterest(i);
              const pic = i.user_photo_thumb_url || i.user_photo_url;
              return slug ? (
                <Link key={i.user_id} to={`/app/profile/${slug}`} className="inline-block ring-2 ring-white rounded-full" title={`Perfil de ${i.user_name}`}>
                  <Avatar name={i.user_name} photoUrl={pic} size={7} />
                </Link>
              ) : <Avatar key={i.user_id} name={i.user_name} photoUrl={pic} size={7} />;
            })}
            {interested.length > 5 && (
              <span className="w-7 h-7 rounded-full bg-gray-200 text-gray-600 text-xs font-bold border-2 border-white flex items-center justify-center">+{interested.length - 5}</span>
            )}
          </div>
        )}

        <div className="pr-20">
          <a href={d.url} target="_blank" rel="noreferrer" className="text-base font-semibold text-blue-700 hover:underline">{d.label}</a>
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
                  {slug ? <Link to={`/app/profile/${slug}`} className="font-medium text-blue-600 hover:underline">{i.user_name}</Link>
                        : <span className="font-medium text-gray-700">{i.user_name}</span>}
                </span>
              );
            })}
          </div>
        )}

        <div className="flex items-center gap-2">
          {!isPast && (
            <button
              type="button"
              disabled={toggleMutation.isPending}
              onClick={() => handleToggle(d.id)}
              className={`inline-flex items-center gap-2 text-xs px-3 py-1.5 rounded-lg border font-medium transition-colors disabled:opacity-50 ${
                myInterest ? 'bg-green-50 border-green-300 text-green-700 hover:bg-red-50 hover:border-red-300 hover:text-red-600'
                           : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-blue-50 hover:border-blue-300 hover:text-blue-700'
              }`}
            >
              <span>{myInterest ? '✓ Quero mandar' : 'Quero mandar'}</span>
            </button>
          )}
          {canManage && (
            <button type="button" onClick={() => handleDelete(d.id)} title="Remover" className="text-gray-300 hover:text-red-500 transition-colors ml-auto shrink-0">
              <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-full bg-gray-50">
      {confirmModal}
      <Toast message={toast} onClose={() => setToast('')} />
      <div className="max-w-3xl mx-auto p-6 space-y-8">

        {/* Adicionar deadline manualmente */}
        <section className="bg-white rounded-xl border shadow-sm overflow-hidden">
          <button
            type="button"
            onClick={() => { setAddOpen(o => !o); setAddError(''); }}
            className="w-full flex items-center justify-between px-5 py-3 text-left hover:bg-gray-50 transition-colors"
          >
            <span className="text-sm font-semibold text-gray-700">Adicionar deadline</span>
            <svg xmlns="http://www.w3.org/2000/svg" className={`w-4 h-4 text-gray-400 transition-transform ${addOpen ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          {addOpen && (
            <form onSubmit={handleAddManual} className="px-5 pb-5 pt-3 border-t space-y-3">
              <input
                required
                placeholder="Nome do deadline (ex: ICSE 2026)"
                value={addLabel}
                onChange={e => setAddLabel(e.target.value)}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
              />
              <input
                required
                type="url"
                placeholder="URL (ex: https://conf.example.org)"
                value={addUrl}
                onChange={e => setAddUrl(e.target.value)}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
              />
              <input
                required
                type="date"
                value={addDate}
                onChange={e => setAddDate(e.target.value)}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
              />
              {addError && <p className="text-xs text-red-500">{addError}</p>}
              <div className="flex gap-2">
                <button type="submit" disabled={createMutation.isPending} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50">
                  {createMutation.isPending ? 'Adicionando…' : 'Adicionar'}
                </button>
                <button type="button" onClick={() => setAddOpen(false)} className="bg-gray-200 px-4 py-2 rounded-lg text-sm hover:bg-gray-300">Cancelar</button>
              </div>
            </form>
          )}
        </section>

        {/* Extrair deadline por URL */}
        {canManage && (
          <section className="bg-white rounded-xl border shadow-sm overflow-hidden">
            <button
              type="button"
              onClick={() => { setExtractOpen(o => !o); setExtracted(null); setExtractError(''); }}
              className="w-full flex items-center justify-between px-5 py-3 text-left hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-gray-700">Extrair deadline de uma URL</span>
                <span className="text-[10px] font-semibold uppercase tracking-wide text-amber-600 bg-amber-50 border border-amber-200 rounded px-1.5 py-0.5">experimental</span>
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
                      {extractError && <p className="text-xs text-red-500">{extractError}</p>}
                    </div>
                    <button type="submit" disabled={extracting || !isValidUrl} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40 shrink-0 self-start">
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
                    Processando…
                  </div>
                )}

                {extracted && extracted.length > 0 && (
                  <div className="space-y-2">
                    {extracted.map((d, i) => (
                      <div key={i} className="flex flex-wrap items-center gap-3 rounded-lg border bg-gray-50 px-4 py-3 text-sm">
                        <span className="font-semibold text-gray-800">{d.label}</span>
                        <span className="text-gray-400">·</span>
                        <span className="text-blue-700 font-medium">{new Date(d.date + 'T00:00:00').toLocaleDateString('pt-BR')}</span>
                        <a href={d.url} target="_blank" rel="noreferrer" className="ml-auto text-xs text-blue-500 hover:underline truncate max-w-[14rem]">{d.url}</a>
                        <button
                          type="button"
                          disabled={saving[i]}
                          onClick={() => handleSaveExtracted(d, i)}
                          className="text-xs bg-blue-600 text-white rounded px-2 py-1 hover:bg-blue-700 disabled:opacity-50 shrink-0"
                        >
                          {saving[i] ? 'Salvando…' : 'Adicionar'}
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </section>
        )}

        {/* Próximos */}
        <section className="space-y-3">
          {upcoming.length === 0 ? (
            <p className="text-sm text-gray-400 italic">Nenhum deadline próximo.</p>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2">{upcoming.map(renderCard)}</div>
          )}
        </section>

        {/* Passados */}
        <section>
          <button type="button" onClick={() => setShowPast(o => !o)} className="flex items-center gap-1.5 text-sm text-gray-400 hover:text-gray-600 mb-3">
            <svg xmlns="http://www.w3.org/2000/svg" className={`w-4 h-4 transition-transform ${showPast ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
            {past.length} deadline{past.length !== 1 ? 's' : ''} passado{past.length !== 1 ? 's' : ''}
          </button>
          {showPast && <div className="grid gap-3 sm:grid-cols-2">{past.map(renderCard)}</div>}
        </section>
      </div>
    </div>
  );
}
