import React from 'react';

const ITEMS = [
  { label: 'Professor', color: '#7C3AED' },
  { label: 'Doutorado', color: '#10B981' },
  { label: 'Mestrado', color: '#F59E0B' },
  { label: 'Graduação', color: '#3B82F6' },
];

export default function Legend() {
  return (
    <div className="absolute top-4 right-4 bg-white rounded-lg shadow-md px-4 py-3 z-10">
      <p className="text-xs font-bold text-gray-500 uppercase mb-2">Nível</p>
      <ul className="space-y-1.5">
        {ITEMS.map((item) => (
          <li key={item.label} className="flex items-center gap-2 text-sm text-gray-700">
            <span className="w-3 h-3 rounded-full inline-block" style={{ backgroundColor: item.color }} />
            {item.label}
          </li>
        ))}
      </ul>
    </div>
  );
}
