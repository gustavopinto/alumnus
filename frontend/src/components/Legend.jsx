import React from 'react';

const ITEMS = [
  { label: 'Professor', color: '#7C3AED', status: 'professor' },
  { label: 'Doutorado', color: '#10B981', status: 'doutorado' },
  { label: 'Mestrado', color: '#F59E0B', status: 'mestrado' },
  { label: 'Graduação', color: '#3B82F6', status: 'graduacao' },
];

export default function Legend({ hiddenStatuses, onToggleStatus }) {
  return (
    <div className="absolute top-4 right-4 bg-white rounded-lg shadow-md px-4 py-3 z-10 border border-gray-100 max-w-[11rem]">
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
