import React from 'react';
import { Handle, Position } from '@xyflow/react';

export default function StudentNode({ data }) {
  function handleClick(e) {
    e.stopPropagation();
    window.location.href = `/profile/${data.slug}`;
  }

  return (
    <div
      className="rounded-xl shadow-lg bg-white border-2 p-3 w-44 text-center cursor-grab"
      style={{ borderColor: data.color || '#6B7280' }}
    >
      <Handle type="target" position={Position.Top} isConnectable={false} className="!bg-gray-300 !w-2 !h-2" />
      <div onClick={handleClick} className="cursor-pointer group">
        {data.photoUrl ? (
          <img
            src={data.photoUrl}
            alt={data.name}
            className="w-14 h-14 rounded-full mx-auto mb-2 object-cover border-2 group-hover:opacity-80 transition-opacity"
            style={{ borderColor: data.color }}
          />
        ) : (
          <div
            className="w-14 h-14 rounded-full mx-auto mb-2 flex items-center justify-center text-white text-xl font-bold group-hover:opacity-80 transition-opacity"
            style={{ backgroundColor: data.color || '#6B7280' }}
          >
            {data.name?.charAt(0)?.toUpperCase()}
          </div>
        )}
        <p className="font-semibold text-sm text-gray-800 truncate group-hover:text-blue-600 transition-colors">
          {data.name}
        </p>
      </div>
      <Handle type="source" position={Position.Bottom} isConnectable={false} className="!bg-gray-300 !w-2 !h-2" />
    </div>
  );
}
