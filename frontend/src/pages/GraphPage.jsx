import React, { useMemo, useState, useCallback } from 'react';
import GraphView from '../components/GraphView';
import BoxView from '../components/BoxView';
import Legend from '../components/Legend';
import { useAppLayout } from '../components/AppLayout';

export default function GraphPage() {
  const { graphNodes, graphEdges, researchers } = useAppLayout();
  const [hiddenStatuses, setHiddenStatuses] = useState(() => new Set());
  const [viewMode, setViewMode] = useState('graph');

  const toggleStatus = useCallback((status) => {
    setHiddenStatuses((prev) => {
      const next = new Set(prev);
      if (next.has(status)) next.delete(status);
      else next.add(status);
      return next;
    });
  }, []);

  const visibleNodes = useMemo(
    () => graphNodes.filter((n) => !hiddenStatuses.has(n.data?.status)),
    [graphNodes, hiddenStatuses],
  );

  const visibleIds = useMemo(() => new Set(visibleNodes.map((n) => n.id)), [visibleNodes]);

  const visibleEdges = useMemo(
    () => graphEdges.filter((e) => visibleIds.has(e.source) && visibleIds.has(e.target)),
    [graphEdges, visibleIds],
  );

  return (
    <div className="h-full min-h-[400px] relative bg-gray-50">
      {viewMode === 'graph' ? (
        <GraphView initialNodes={visibleNodes} initialEdges={visibleEdges} />
      ) : (
        <BoxView researchers={researchers} hiddenStatuses={hiddenStatuses} />
      )}
      <Legend hiddenStatuses={hiddenStatuses} onToggleStatus={toggleStatus} viewMode={viewMode} onToggleView={setViewMode} researchers={researchers} />
    </div>
  );
}
