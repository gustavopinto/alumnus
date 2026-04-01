import React from 'react';
import { Handle, Position } from '@xyflow/react';

export default function ResearcherNode({ data }) {
  const pending = data.registered === false;

  function handleClick(e) {
    e.stopPropagation();
    window.location.href = `/app/profile/${data.slug}`;
  }

  const nodeColor = pending ? '#9CA3AF' : (data.color || '#6B7280');

  return (
    <div className={`flex flex-col items-center cursor-grab${pending ? ' opacity-50' : ''}`} style={{ width: '96px' }}>
      <Handle type="target" position={Position.Top} isConnectable={false} className="!bg-gray-300 !w-2 !h-2" />

      <div
        onClick={handleClick}
        className="w-16 h-16 rounded-full shadow-lg cursor-pointer group overflow-hidden flex items-center justify-center border-3 bg-white"
        style={{ borderColor: nodeColor, borderWidth: '3px' }}
      >
        {data.photoUrl ? (
          <img
            src={data.photoUrl}
            alt={data.name}
            className={`w-full h-full object-cover group-hover:opacity-80 transition-opacity${pending ? ' grayscale' : ''}`}
          />
        ) : (
          <div
            className="w-full h-full flex items-center justify-center text-white text-xl font-bold group-hover:opacity-80 transition-opacity"
            style={{ backgroundColor: nodeColor }}
          >
            {data.name?.charAt(0)?.toUpperCase()}
          </div>
        )}
      </div>

      <p
        onClick={handleClick}
        className="mt-1.5 text-xs font-semibold text-center cursor-pointer hover:text-blue-600 transition-colors leading-tight w-24 text-gray-800"
      >
        {data.name}
      </p>

      <Handle type="source" position={Position.Bottom} isConnectable={false} className="!bg-gray-300 !w-2 !h-2" />
    </div>
  );
}
