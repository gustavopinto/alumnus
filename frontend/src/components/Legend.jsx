import React from 'react';

const ITEMS = [
  { label: 'Professor', color: '#7C3AED', status: 'professor' },
  { label: 'Doutorado', color: '#10B981', status: 'doutorado' },
  { label: 'Mestrado', color: '#F59E0B', status: 'mestrado' },
  { label: 'Graduação', color: '#3B82F6', status: 'graduacao' },
];

function IconGraph() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="w-4 h-4">
      <circle cx="5" cy="12" r="2" /><circle cx="19" cy="5" r="2" /><circle cx="19" cy="19" r="2" />
      <line x1="7" y1="12" x2="17" y2="6" /><line x1="7" y1="12" x2="17" y2="18" />
    </svg>
  );
}

function IconGrid() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="w-4 h-4">
      <rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" />
      <rect x="3" y="14" width="7" height="7" /><rect x="14" y="14" width="7" height="7" />
    </svg>
  );
}

export default function Legend({ hiddenStatuses, onToggleStatus, viewMode, onToggleView }) {
  return (
    <div className="absolute top-4 right-4 bg-white rounded-lg shadow-md px-4 py-3 z-10 border border-gray-100 max-w-[11rem]">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-1 bg-gray-100 rounded-md p-0.5">
          <button
            onClick={() => onToggleView('graph')}
            title="Modo grafo"
            className={`p-1 rounded transition-all ${viewMode === 'graph' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-400 hover:text-gray-600'}`}
          >
            <IconGraph />
          </button>
          <button
            onClick={() => onToggleView('box')}
            title="Modo caixas"
            className={`p-1 rounded transition-all ${viewMode === 'box' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-400 hover:text-gray-600'}`}
          >
            <IconGrid />
          </button>
        </div>
      </div>
      <ul className="space-y-1">
        {ITEMS.map((item) => {
          const hidden = hiddenStatuses.has(item.status);
          return (
            <li key={item.status}>
              <button
                type="button"
                onClick={() => onToggleStatus(item.status)}
                title={hidden ? `Mostrar ${item.label}` : `Ocultar ${item.label}`}
                className={`w-full flex items-center gap-2 text-sm text-left rounded-md px-1.5 py-1 -mx-1.5 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 ${
                  hidden
                    ? 'text-gray-400 opacity-60 line-through'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
              >
                <span
                  className={`w-3 h-3 rounded-full shrink-0 ring-2 ring-offset-1 ${hidden ? 'ring-gray-200' : 'ring-transparent'}`}
                  style={{ backgroundColor: item.color }}
                />
                <span className="flex-1">{item.label}</span>
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
