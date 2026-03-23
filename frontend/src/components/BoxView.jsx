import React from 'react';
import { Link } from 'react-router-dom';

const STATUS_COLOR = {
  professor: '#7C3AED',
  postdoc:    '#06B6D4',
  doutorado:  '#10B981',
  mestrado:   '#F59E0B',
  graduacao:  '#3B82F6',
};

const STATUS_LABEL = {
  professor: 'Professor',
  postdoc:    'Pós-doc',
  doutorado:  'Doutorado',
  mestrado:   'Mestrado',
  graduacao:  'Graduação',
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
        className="w-14 h-14 rounded-full object-cover shrink-0 ring-2"
        style={{ ringColor: color, borderColor: color, border: `2px solid ${color}` }}
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

export default function BoxView({ researchers, hiddenStatuses }) {
  const visible = researchers.filter(r => r.ativo && !hiddenStatuses.has(r.status));

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
              {items.map(r => (
                <Link
                  key={r.id}
                  to={`/app/profile/${slugify(r.nome)}`}
                  className="bg-white rounded-xl border shadow-sm p-4 flex items-start gap-3 hover:shadow-md hover:border-gray-300 transition-all group"
                  style={{ borderLeftColor: color, borderLeftWidth: 4 }}
                >
                  <Avatar researcher={r} color={color} />
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
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}
