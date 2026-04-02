import React, { useState, useEffect, useRef } from 'react';
import { getReadings, createReading, updateReadingStatus, deleteReading, summarizeReading } from '../api';
import Toast from './Toast';

const COLUMNS = [
  { key: 'quero_ler', label: 'Quero ler',  color: '#6B7280', bg: '#F9FAFB', border: '#E5E7EB' },
  { key: 'lendo',     label: 'Lendo',       color: '#2563EB', bg: '#EFF6FF', border: '#BFDBFE' },
  { key: 'lido',      label: 'Lido',        color: '#059669', bg: '#ECFDF5', border: '#A7F3D0' },
];

const STATUS_ORDER = ['quero_ler', 'lendo', 'lido'];
const STATUS_LABEL = { quero_ler: 'Quero ler', lendo: 'Lendo', lido: 'Lido' };
const STATUS_STYLE = {
  quero_ler: { color: '#6B7280', bg: '#F9FAFB', border: '#E5E7EB' },
  lendo:     { color: '#2563EB', bg: '#EFF6FF', border: '#BFDBFE' },
  lido:      { color: '#059669', bg: '#ECFDF5', border: '#A7F3D0' },
};

function fmtDate(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

function HistoryBadge({ history }) {
  const [open, setOpen] = useState(false);
  if (!history || history.length <= 1) return null;
  return (
    <div className="relative inline-block">
      <button
        onClick={() => setOpen(o => !o)}
        className="text-[10px] text-gray-400 hover:text-gray-600 underline leading-none"
      >
        histórico
      </button>
      {open && (
        <div
          className="absolute z-50 bottom-5 left-0 bg-white border border-gray-200 rounded shadow-lg p-2 min-w-[180px] text-[11px] text-gray-600"
          onMouseLeave={() => setOpen(false)}
        >
          {[...history].reverse().map(h => (
            <div key={h.id} className="flex justify-between gap-3 py-0.5 border-b border-gray-100 last:border-0">
              <span className="font-medium">{STATUS_LABEL[h.status] ?? h.status}</span>
              <span className="text-gray-400">{fmtDate(h.changed_at)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ReadingCard({ reading, canEdit, onStatusChange, onDelete, onSummarize, summarizing, onViewSummary }) {
  const idx = STATUS_ORDER.indexOf(reading.status);
  const prevStatus = idx > 0 ? STATUS_ORDER[idx - 1] : null;
  const nextStatus = idx < STATUS_ORDER.length - 1 ? STATUS_ORDER[idx + 1] : null;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-3 text-sm shadow-sm flex flex-col gap-1.5">
      <a
        href={reading.url}
        target="_blank"
        rel="noopener noreferrer"
        className="font-medium text-blue-700 hover:underline line-clamp-2 leading-snug"
        title={reading.url}
      >
        {reading.title || reading.url}
      </a>

      {!reading.title && (
        <span className="text-[10px] text-gray-400 italic">Carregando título…</span>
      )}

      <div className="flex items-center gap-2 flex-wrap mt-0.5">
        {canEdit && prevStatus && (() => {
          const s = STATUS_STYLE[prevStatus];
          return (
            <button
              onClick={() => onStatusChange(reading.id, prevStatus)}
              style={{ color: s.color, background: s.bg, borderColor: s.border }}
              className="text-[11px] px-2 py-0.5 rounded border leading-none hover:opacity-80"
            >
              ← {STATUS_LABEL[prevStatus]}
            </button>
          );
        })()}
        {canEdit && nextStatus && (() => {
          const s = STATUS_STYLE[nextStatus];
          return (
            <button
              onClick={() => onStatusChange(reading.id, nextStatus)}
              style={{ color: s.color, background: s.bg, borderColor: s.border }}
              className="text-[11px] px-2 py-0.5 rounded border leading-none hover:opacity-80"
            >
              → {STATUS_LABEL[nextStatus]}
            </button>
          );
        })()}
        {canEdit && (
          <button
            onClick={() => onDelete(reading)}
            className="text-[11px] text-gray-400 hover:text-red-500 leading-none ml-auto"
            title="Remover"
          >
            ✕
          </button>
        )}
      </div>

      <div className="flex items-center gap-2 flex-wrap">
        {reading.summary ? (
          <button
            onClick={() => onViewSummary(reading)}
            className="text-[11px] text-purple-600 hover:text-purple-800 underline leading-none"
          >
            Ler resumo
          </button>
        ) : canEdit && (
          <button
            onClick={() => onSummarize(reading.id)}
            disabled={summarizing === reading.id}
            className="text-[11px] text-purple-600 hover:text-purple-800 underline disabled:opacity-50 leading-none"
          >
            {summarizing === reading.id ? 'Resumindo…' : 'Resumir'}
          </button>
        )}
        <HistoryBadge history={reading.status_history} />
        <span className="text-[10px] text-gray-400 ml-auto">{fmtDate(reading.created_at)}</span>
      </div>
    </div>
  );
}

export default function ReadingList({ userId, canEdit }) {
  const [open, setOpen]               = useState(false);
  const [readings, setReadings]       = useState([]);
  const [urlInput, setUrlInput]       = useState('');
  const [adding, setAdding]           = useState(false);
  const [summarizing, setSummarizing] = useState(null);
  const [toast, setToast]             = useState(null);
  const [pendingDelete, setPendingDelete] = useState(null);
  const [summaryReading, setSummaryReading] = useState(null);
  const loaded                        = useRef(false);
  const pollRef                       = useRef({});

  // Reset cache when user changes
  useEffect(() => {
    loaded.current = false;
    setReadings([]);
    setUrlInput('');
    Object.values(pollRef.current).forEach(clearInterval);
    pollRef.current = {};
  }, [userId]);

  // Lazy load on first open
  useEffect(() => {
    if (open && !loaded.current && userId) {
      loaded.current = true;
      load();
    }
  }, [open]);

  // Cleanup polls on unmount
  useEffect(() => {
    return () => Object.values(pollRef.current).forEach(clearInterval);
  }, []);

  async function load() {
    const data = await getReadings(userId);
    if (data) setReadings(data);
    // start polling for any readings without title yet
    data?.forEach(r => {
      if (!r.title) startPolling(r.id);
    });
  }

  function startPolling(readingId) {
    if (pollRef.current[readingId]) return;
    let attempts = 0;
    pollRef.current[readingId] = setInterval(async () => {
      attempts++;
      const data = await getReadings(userId);
      if (!data) return;
      const found = data.find(r => r.id === readingId);
      if (found?.title || attempts >= 10) {
        clearInterval(pollRef.current[readingId]);
        delete pollRef.current[readingId];
        setReadings(data);
      }
    }, 3000);
  }

  async function handleAdd(e) {
    e.preventDefault();
    const url = urlInput.trim();
    if (!url) return;
    setAdding(true);
    const res = await createReading(userId, url);
    setAdding(false);
    if (res?.id) {
      setReadings(prev => [res, ...prev]);
      setUrlInput('');
      setToast({ message: 'Leitura adicionada', type: 'success' });
      if (!res.title) startPolling(res.id);
    } else {
      const msg = res?.detail ?? 'Erro ao adicionar leitura';
      setToast({ message: typeof msg === 'string' ? msg : 'Erro ao adicionar leitura', type: 'error' });
    }
  }

  async function handleStatusChange(readingId, newStatus) {
    const res = await updateReadingStatus(userId, readingId, newStatus);
    if (res?.id) {
      setReadings(prev => prev.map(r => r.id === readingId ? res : r));
      setToast({ message: `Status atualizado: ${STATUS_LABEL[newStatus]}`, type: 'success' });
    }
  }

  async function handleDelete(readingId) {
    await deleteReading(userId, readingId);
    setReadings(prev => prev.filter(r => r.id !== readingId));
    setPendingDelete(null);
    setToast({ message: 'Leitura removida', type: 'success' });
  }

  async function handleSummarize(readingId) {
    setSummarizing(readingId);
    await summarizeReading(userId, readingId);
    setSummarizing(null);
    setToast({ message: 'Resumo sendo gerado, aguarde…', type: 'success' });
    // poll until summary arrives
    let attempts = 0;
    const iv = setInterval(async () => {
      attempts++;
      const data = await getReadings(userId);
      if (!data) return;
      const found = data.find(r => r.id === readingId);
      if (found?.summary || attempts >= 15) {
        clearInterval(iv);
        setReadings(data);
        if (found?.summary) setToast({ message: 'Resumo disponível!', type: 'success' });
      }
    }, 3000);
  }

  const byStatus = (status) => readings.filter(r => r.status === status);

  return (
    <section className="bg-white rounded-xl border shadow-sm overflow-hidden">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}

      {/* Header */}
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-6 py-4 hover:bg-gray-50 transition-colors"
      >
        <h2 className="text-lg font-bold text-gray-800">📚 Leituras</h2>
        <svg
          className={`w-4 h-4 text-gray-500 transition-transform ${open ? 'rotate-180' : ''}`}
          fill="none" stroke="currentColor" viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div className="px-6 pb-6 space-y-4">
          {/* Add form */}
          {canEdit && (
            <form onSubmit={handleAdd} className="flex gap-2">
              <input
                type="url"
                value={urlInput}
                onChange={e => setUrlInput(e.target.value)}
                placeholder="https://arxiv.org/abs/..."
                className="flex-1 border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
                required
              />
              <button
                type="submit"
                disabled={adding}
                className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded disabled:opacity-50"
              >
                {adding ? '…' : 'Adicionar'}
              </button>
            </form>
          )}

          {/* Columns */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {COLUMNS.map(col => (
              <div key={col.key}>
                <div
                  className="text-xs font-semibold px-2 py-1 rounded-t border-b mb-2"
                  style={{ color: col.color, background: col.bg, borderColor: col.border }}
                >
                  {col.label}
                  <span className="ml-1 font-normal text-gray-400">({byStatus(col.key).length})</span>
                </div>
                <div className="space-y-2 max-h-80 overflow-y-auto pr-0.5">
                  {byStatus(col.key).map(reading => (
                    <ReadingCard
                      key={reading.id}
                      reading={reading}
                      canEdit={canEdit}
                      onStatusChange={handleStatusChange}
                      onDelete={setPendingDelete}
                      onSummarize={handleSummarize}
                      summarizing={summarizing}
                      onViewSummary={setSummaryReading}
                    />
                  ))}
                  {byStatus(col.key).length === 0 && (
                    <p className="text-xs text-gray-400 italic px-1">Nenhuma leitura aqui.</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Confirmação de remoção */}
      {pendingDelete && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 max-w-sm w-full mx-4">
            <p className="text-gray-800 font-medium mb-1">Remover leitura?</p>
            <p className="text-sm text-gray-500 mb-5 line-clamp-2">
              {pendingDelete.title || pendingDelete.url}
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setPendingDelete(null)}
                className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
              >
                Cancelar
              </button>
              <button
                onClick={() => handleDelete(pendingDelete.id)}
                className="px-4 py-2 text-sm bg-red-600 hover:bg-red-700 text-white rounded-lg"
              >
                Remover
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Popup de resumo */}
      {summaryReading && (
        <div
          className="fixed inset-0 bg-black/40 flex items-center justify-center z-50"
          onClick={() => setSummaryReading(null)}
        >
          <div
            className="bg-white rounded-xl shadow-xl p-6 max-w-lg w-full mx-4 max-h-[80vh] overflow-y-auto"
            onClick={e => e.stopPropagation()}
          >
            <div className="flex items-start justify-between mb-4 gap-3">
              <h3 className="text-base font-semibold text-gray-800 leading-snug">
                {summaryReading.title || summaryReading.url}
              </h3>
              <button
                onClick={() => setSummaryReading(null)}
                className="text-gray-400 hover:text-gray-600 shrink-0 text-lg leading-none"
              >
                ✕
              </button>
            </div>
            <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-line">
              {summaryReading.summary}
            </p>
          </div>
        </div>
      )}
    </section>
  );
}
