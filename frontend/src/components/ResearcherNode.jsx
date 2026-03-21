import React from 'react';
import { Handle, Position } from '@xyflow/react';

export default function ResearcherNode({ data }) {
  function handleClick(e) {
    e.stopPropagation();
    window.location.href = `/app/profile/${data.slug}`;
  }

  return (
    <div className="flex flex-col items-center cursor-grab" style={{ width: '96px' }}>
      <Handle type="target" position={Position.Top} isConnectable={false} className="!bg-gray-300 !w-2 !h-2" />

      <div
        onClick={handleClick}
        className="w-16 h-16 rounded-full shadow-lg cursor-pointer group overflow-hidden flex items-center justify-center border-3 bg-white"
        style={{ borderColor: data.color || '#6B7280', borderWidth: '3px' }}
      >
        {data.photoUrl ? (
          <img
            src={data.photoUrl}
            alt={data.name}
            className="w-full h-full object-cover group-hover:opacity-80 transition-opacity"
          />
        ) : (
          <div
            className="w-full h-full flex items-center justify-center text-white text-xl font-bold group-hover:opacity-80 transition-opacity"
            style={{ backgroundColor: data.color || '#6B7280' }}
          >
            {data.name?.charAt(0)?.toUpperCase()}
          </div>
        )}
      </div>

      <p
        onClick={handleClick}
        className="mt-1.5 text-xs font-semibold text-gray-800 text-center cursor-pointer hover:text-blue-600 transition-colors leading-tight w-24"
      >
        {data.name}
      </p>

      <Handle type="source" position={Position.Bottom} isConnectable={false} className="!bg-gray-300 !w-2 !h-2" />
    </div>
  );
}
