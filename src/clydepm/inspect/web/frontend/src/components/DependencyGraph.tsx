import React, { useEffect, useRef, useState, useCallback } from 'react';
import ReactFlow, {
    Node,
    Edge,
    Background,
    Controls,
    NodeProps,
    Handle,
    Position,
    useReactFlow,
    ReactFlowProvider,
    applyNodeChanges,
    applyEdgeChanges,
    NodeChange,
    EdgeChange
} from 'reactflow';
import 'reactflow/dist/style.css';
import { DependencyGraph as DependencyGraphType, GraphSettings } from '../types';
import { fetchDependencyGraph, fetchGraphSettings } from '../api/client';
import type { DependencyNode } from '../types';

interface DependencyGraphProps {
    onNodeClick: (node: DependencyNode) => void;
}

const PackageNode: React.FC<NodeProps> = ({ data }) => (
    <div className={`package-node ${data.is_dev_dep ? 'dev-dep' : ''} ${data.has_warnings ? 'has-warnings' : ''}`}>
        <Handle type="target" position={Position.Top} />
        <div className="package-header">
            <span className="package-name">{data.name}</span>
            <span className="package-version">{data.version}</span>
        </div>
        {data.has_warnings && (
            <div className="warning-indicator">⚠️</div>
        )}
        <Handle type="source" position={Position.Bottom} />
    </div>
);

const nodeTypes = {
    package: PackageNode,
};

const Flow: React.FC<DependencyGraphProps> = ({ onNodeClick }) => {
    const [nodes, setNodes] = useState<Node[]>([]);
    const [edges, setEdges] = useState<Edge[]>([]);
    const [settings, setSettings] = useState<GraphSettings | null>(null);
    const flowWrapper = useRef<HTMLDivElement>(null);
    const { fitView } = useReactFlow();

    const onNodesChange = useCallback((changes: NodeChange[]) => {
        setNodes((nds) => applyNodeChanges(changes, nds));
    }, []);

    const onEdgesChange = useCallback((changes: EdgeChange[]) => {
        setEdges((eds) => applyEdgeChanges(changes, eds));
    }, []);

    useEffect(() => {
        const loadGraphData = async () => {
            try {
                const [graphData, graphSettings] = await Promise.all([
                    fetchDependencyGraph(),
                    fetchGraphSettings(),
                ]);

                // Transform nodes with draggable positions
                const flowNodes = graphData.nodes.map((node) => ({
                    id: node.id,
                    type: 'package',
                    position: {
                        x: node.position.x * 200,  // Space out nodes more
                        y: node.position.y * 200
                    },
                    draggable: true,  // Enable dragging
                    data: {
                        ...node,
                    },
                }));

                // Transform edges
                const flowEdges = graphData.edges.map((edge) => ({
                    id: edge.id,
                    source: edge.source,
                    target: edge.target,
                    type: edge.is_circular ? 'smoothstep' : 'default',
                    animated: edge.is_circular,
                    style: {
                        stroke: edge.is_circular ? '#ff0000' : '#888',
                        strokeWidth: 2,
                    },
                }));

                setNodes(flowNodes);
                setEdges(flowEdges);
                setSettings(graphSettings);

            } catch (error) {
                console.error('Failed to load graph data:', error);
            }
        };

        loadGraphData();
    }, []);

    useEffect(() => {
        if (settings && nodes.length > 0) {
            setTimeout(() => {
                fitView({
                    padding: 0.2,
                    minZoom: settings.zoom.min,
                    maxZoom: settings.zoom.max,
                });
            }, 100);
        }
    }, [settings, nodes, fitView]);

    if (!settings) return <div>Loading...</div>;

    return (
        <div ref={flowWrapper} style={{ width: '100%', height: '100%' }}>
            <ReactFlow
                nodes={nodes}
                edges={edges}
                nodeTypes={nodeTypes}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onNodeClick={(_, node) => onNodeClick(node.data)}
                fitView
                minZoom={settings.zoom.min}
                maxZoom={settings.zoom.max}
                defaultViewport={{
                    x: 0,
                    y: 0,
                    zoom: settings.zoom.initial
                }}
                attributionPosition="bottom-left"
            >
                <Background />
                <Controls />
            </ReactFlow>
        </div>
    );
};

export const DependencyGraph: React.FC<DependencyGraphProps> = (props) => {
    return (
        <ReactFlowProvider>
            <Flow {...props} />
        </ReactFlowProvider>
    );
}; 