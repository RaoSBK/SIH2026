import { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';

// Mock data based on SIH Demonstration Story
const elements = [
  { data: { id: 'a', label: 'Person A', type: 'person' } },
  { data: { id: 'b', label: 'Person B', type: 'person' } },
  { data: { id: 'c', label: 'Person C', type: 'person' } },
  { data: { id: 'bank', label: 'Bank Account Y', type: 'account' } },
  { data: { id: 'phone', label: 'Phone X', type: 'phone' } },
  { data: { id: 'ab', source: 'a', target: 'b', label: 'CALLS' } },
  { data: { id: 'bc', source: 'b', target: 'c', label: 'TRANSFERRED' } },
  { data: { id: 'cbank', source: 'c', target: 'bank', label: 'OWNS' } },
  { data: { id: 'aphone', source: 'a', target: 'phone', label: 'USES' } }
];

export default function GraphView() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        {
          selector: 'node',
          style: {
            'label': 'data(label)',
            'text-valign': 'bottom',
            'text-halign': 'center',
            'text-margin-y': 5,
            'background-color': '#3b82f6',
            'color': '#1f2937',
            'font-family': 'Inter, sans-serif',
            'font-size': 12,
            'font-weight': 500,
          }
        },
        {
          selector: 'node[type="account"]',
          style: { 'background-color': '#10b981', 'shape': 'round-rectangle' }
        },
        {
          selector: 'node[type="phone"]',
          style: { 'background-color': '#8b5cf6', 'shape': 'diamond' }
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': '#cbd5e1',
            'target-arrow-color': '#cbd5e1',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(label)',
            'font-size': 10,
            'color': '#64748b',
            'text-rotation': 'autorotate',
            'text-margin-y': -10
          }
        }
      ],
      layout: {
        name: 'cose',
        padding: 50,
        animate: true,
        animationDuration: 500,
        animationEasing: 'ease-out-quint'
      }
    });

    return () => {
      cy.destroy();
    };
  }, []);

  return (
    <div className="h-[calc(100vh-8rem)] w-full glass-panel dark:glass-panel-dark rounded-2xl border border-gray-200/50 dark:border-gray-800/50 shadow-sm overflow-hidden flex flex-col">
      <div className="p-4 border-b border-gray-200/50 dark:border-gray-800/50 flex justify-between items-center bg-white/20 dark:bg-black/20">
        <h3 className="font-semibold">Knowledge Graph Investigation</h3>
        <div className="flex gap-2">
          <button className="px-3 py-1.5 text-xs font-medium bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
            Run Centrality
          </button>
          <button className="px-3 py-1.5 text-xs font-medium bg-blue-600 text-white rounded-lg shadow-sm hover:bg-blue-700 transition-colors">
            Find Communities
          </button>
        </div>
      </div>
      <div className="flex-1 relative">
        <div ref={containerRef} className="absolute inset-0" />
      </div>
    </div>
  );
}
