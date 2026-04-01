import React from 'react';
import { Link } from 'react-router-dom';

const STATUS_COLOR = {
  professor: '#7C3AED',
  postdoc:    '#06B6D4',
  doutorado:  '#10B981',
  mestrado:   '#F59E0B',
  graduacao:  '#3B82F6',
  egresso:    '#6B7280',
};

const STATUS_LABEL = {
  professor: 'Professor',
  postdoc:    'Pós-doc',
  doutorado:  'Doutorado',
  mestrado:   'Mestrado',
  graduacao:  'Graduação',
  egresso:    'Egresso',
};

function slugify(nome) {
  return (nome || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .toLowerCase().trim().replace(/[^a-z0-9\s-]/g, '').replace(/\s+/g, '-');
}

function Avatar({ researcher, color }) {
  if (researcher.photo_url) {
    return (
      <img
        src={researcher.photo_url}
        alt={researcher.nome}
        className={`w-14 h-14 rounded-full object-cover shrink-0${researcher.registered === false ? ' grayscale' : ''}`}
        style={{ border: `2px solid ${color}` }}
      />
    );
  }
  const initials = researcher.nome.trim().split(/\s+/).filter(Boolean)
    .slice(0, 2).map(p => p[0].toUpperCase()).join('');
  return (
    <div
      className="w-14 h-14 rounded-full flex items-center justify-center text-white text-lg font-bold shrink-0"
      style={{ backgroundColor: color }}
    >
      {initials}
    </div>
  );
}

function ResearcherCard({ r, color }) {
  const pending = r.registered === false;
  const cardColor = pending ? '#9CA3AF' : color;
  return (
    <Link
      to={`/app/profile/${slugify(r.nome)}`}
      className={`bg-white rounded-xl border shadow-sm p-4 flex items-start gap-3 hover:shadow-md hover:border-gray-300 transition-all group${pending ? ' opacity-50' : ''}`}
      style={{ borderLeftColor: cardColor, borderLeftWidth: 4 }}
    >
      <Avatar researcher={r} color={cardColor} />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-semibold text-gray-800 group-hover:text-blue-700 leading-snug truncate">
          {r.nome}
        </p>
        {r.email && (
          <p className="text-xs text-gray-400 truncate mt-0.5">{r.email}</p>
        )}
        {r.curso && (
          <p className="text-xs text-gray-500 truncate mt-1">{r.curso}</p>
        )}
        {r.interesses && (
          <p className="text-xs text-gray-400 mt-1 line-clamp-2 leading-snug">
            {r.interesses}
          </p>
        )}
        {r.enrollment_date && (
          <p className="text-xs text-gray-400 mt-1">
            Ingresso: {new Date(r.enrollment_date + 'T00:00:00').toLocaleDateString('pt-BR', { month: '2-digit', year: 'numeric' })}
          </p>
        )}
      </div>
    </Link>
  );
}

export default function BoxView({ researchers, hiddenStatuses }) {
  const active = researchers.filter(r => r.ativo && r.status !== 'egresso');
  const visible = active.filter(r => !hiddenStatuses.has(r.status));
  const egressos = researchers.filter(r => r.ativo && r.status === 'egresso');

  const groups = [
    { status: 'professor', items: visible.filter(r => r.status === 'professor') },
    { status: 'postdoc',    items: visible.filter(r => r.status === 'postdoc') },
    { status: 'doutorado',  items: visible.filter(r => r.status === 'doutorado') },
    { status: 'mestrado',   items: visible.filter(r => r.status === 'mestrado') },
    { status: 'graduacao',  items: visible.filter(r => r.status === 'graduacao') },
  ].filter(g => g.items.length > 0);

  return (
    <div className="p-6 space-y-8 overflow-y-auto h-full">
      {groups.map(({ status, items }) => {
        const color = STATUS_COLOR[status];
        return (
          <section key={status}>
            <div className="flex items-center gap-2 mb-3">
              <span className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">
                {STATUS_LABEL[status]}
              </h2>
              <span className="text-xs text-gray-400">({items.length})</span>
            </div>
            <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {items.map(r => <ResearcherCard key={r.id} r={r} color={color} />)}
            </div>
          </section>
        );
      })}
      {egressos.length > 0 && (
        <section>
          <div className="flex items-center gap-2 mb-3">
            <span className="w-3 h-3 rounded-full" style={{ backgroundColor: STATUS_COLOR.egresso }} />
            <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">
              {STATUS_LABEL.egresso}
            </h2>
            <span className="text-xs text-gray-400">({egressos.length})</span>
          </div>
          <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 opacity-60">
            {egressos.map(r => <ResearcherCard key={r.id} r={r} color={STATUS_COLOR.egresso} />)}
          </div>
        </section>
      )}
    </div>
  );
}
