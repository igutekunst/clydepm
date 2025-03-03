import { useCallback, useEffect, useState } from 'react';
import ReactFlow, {
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  NodeTypes,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { getDependencyGraph } from '@/api/client';
import type { DependencyNode as ApiNode } from '@/api/client';

interface DependencyGraphProps {
  onNodeClick: (node: ApiNode) => void;
}

// Custom node component
const CustomNode = ({ data }: { data: ApiNode }) => (
  <div
    className={`dependency-node ${data.is_dev_dep ? 'dev-dep' : ''} ${
      data.has_warnings ? 'has-warnings' : ''
    }`}
  >
    <div className="title">{data.name}</div>
    <div className="version">{data.version}</div>
    {data.has_warnings && <div className="warning-indicator">⚠️</div>}
  </div>
);

const nodeTypes: NodeTypes = {
  dependency: CustomNode,
};

export const DependencyGraph: React.FC<DependencyGraphProps> = ({ onNodeClick }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchGraph = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getDependencyGraph();

      // Convert API nodes to ReactFlow nodes
      const flowNodes = data.nodes.map((node) => ({
        id: node.id,
        type: 'dependency',
        position: node.position,
        data: node,
      }));

      // Convert API edges to ReactFlow edges
      const flowEdges = data.edges.map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        animated: edge.is_circular,
        style: {
          stroke: edge.is_circular ? '#ff0000' : '#000000',
        },
      }));

      setNodes(flowNodes);
      setEdges(flowEdges);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dependency graph');
    } finally {
      setLoading(false);
    }
  }, [setNodes, setEdges]);

  useEffect(() => {
    fetchGraph();
  }, [fetchGraph]);

  if (loading) {
    return <div>Loading dependency graph...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={(_, node) => onNodeClick(node.data)}
        nodeTypes={nodeTypes}
        fitView
      >
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  );
}; 