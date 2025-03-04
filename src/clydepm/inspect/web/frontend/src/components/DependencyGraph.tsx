import React, { useEffect, useRef, useState, useCallback } from 'react';
import ReactFlow, {
    Node,
    Edge,
    Background,
    Controls,
    NodeProps,
    Handle,
    Position,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { fetchDependencyGraph, fetchGraphSettings } from '../api/client';
import type { DependencyNode, DependencyEdge, GraphSettings } from '../types';
import '../styles/DependencyGraph.css';

interface DependencyGraphProps {
    onNodeSelect: (node: DependencyNode | null) => void;
}

const CustomNode = ({ data }: NodeProps) => (
    <div className={`custom-node ${data.has_warnings ? 'has-warnings' : ''}`}>
        <Handle type="target" position={Position.Top} />
        <div className="node-content">
            <div className="node-title">{data.name}</div>
            <div className="node-version">{data.version}</div>
        </div>
        <Handle type="source" position={Position.Bottom} />
    </div>
);

export function DependencyGraph({ onNodeSelect }: DependencyGraphProps) {
    const [nodes, setNodes] = useState<Node[]>([]);
    const [edges, setEdges] = useState<Edge[]>([]);
    const [settings, setSettings] = useState<GraphSettings | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function loadGraphData() {
            try {
                const [graph, graphSettings] = await Promise.all([
                    fetchDependencyGraph(),
                    fetchGraphSettings()
                ]);

                const flowNodes: Node[] = graph.nodes.map(node => ({
                    id: node.id,
                    type: 'custom',
                    position: { x: node.position.x * 200, y: node.position.y * 100 },
                    data: { ...node }
                }));

                const flowEdges: Edge[] = graph.edges.map(edge => ({
                    id: edge.id,
                    source: edge.source,
                    target: edge.target,
                    className: edge.is_circular ? 'circular-edge' : undefined,
                }));

                setNodes(flowNodes);
                setEdges(flowEdges);
                setSettings(graphSettings);
            } catch (e) {
                setError(e instanceof Error ? e.message : 'Failed to load graph data');
            }
        }
        loadGraphData();
    }, []);

    const handleNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
        onNodeSelect(node.data);
    }, [onNodeSelect]);

    if (error) {
        return <div className="graph-error">{error}</div>;
    }

    if (!settings) {
        return <div className="graph-loading">Loading graph data...</div>;
    }

    return (
        <div className="graph-container" style={{ height: settings.layout.height }}>
            <ReactFlow
                nodes={nodes}
                edges={edges}
                nodeTypes={{ custom: CustomNode }}
                onNodeClick={handleNodeClick}
                fitView
            >
                <Background />
                <Controls />
            </ReactFlow>
        </div>
    );
} 