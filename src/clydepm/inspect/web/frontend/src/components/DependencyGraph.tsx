import React, { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import ReactFlow, {
    Node,
    Edge,
    Background,
    Controls,
    NodeProps,
    Handle,
    Position,
    ReactFlowProvider,
    MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { fetchDependencyGraph, fetchGraphSettings } from '../api/client';
import type { DependencyNode, DependencyEdge, GraphSettings, DependencyWarning, BuildData } from '../types';
import '../styles/DependencyGraph.css';

interface DependencyGraphProps {
    onNodeSelect: (node: DependencyNode | null) => void;
    selectedBuild: BuildData | null;
}

const CustomNode = ({ data }: NodeProps) => (
    <div className={`custom-node ${data.has_warnings ? 'has-warnings' : ''}`}>
        <Handle type="target" position={Position.Top} />
        <div className="node-content">
            <div className="node-title">{data.package.name}</div>
            <div className="node-version">{data.version}</div>
        </div>
        <Handle type="source" position={Position.Bottom} />
    </div>
);

class ErrorBoundary extends React.Component<
    { children: React.ReactNode },
    { hasError: boolean }
> {
    constructor(props: { children: React.ReactNode }) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError() {
        return { hasError: true };
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="graph-error">
                    Something went wrong rendering the graph.
                    Please try refreshing the page.
                </div>
            );
        }

        return this.props.children;
    }
}

export function DependencyGraph({ onNodeSelect, selectedBuild }: DependencyGraphProps) {
    const [nodes, setNodes] = useState<Node[]>([]);
    const [edges, setEdges] = useState<Edge[]>([]);
    const [settings, setSettings] = useState<GraphSettings | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [warnings, setWarnings] = useState<DependencyWarning[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    // Memoize nodeTypes to prevent React Flow warning
    const nodeTypes = useMemo(() => ({ custom: CustomNode }), []);

    useEffect(() => {
        let mounted = true;

        async function loadGraphData() {
            if (!selectedBuild) return;
            
            try {
                setIsLoading(true);
                setError(null);
                setWarnings([]);

                console.log('Fetching dependency graph data...');
                const [graph, graphSettings] = await Promise.all([
                    fetchDependencyGraph().catch(e => {
                        console.error('Failed to fetch dependency graph:', e);
                        throw e;
                    }),
                    fetchGraphSettings().catch(e => {
                        console.error('Failed to fetch graph settings:', e);
                        throw e;
                    })
                ]);

                if (!mounted) return;

                console.log('Received graph data:', graph);
                console.log('Received graph settings:', graphSettings);

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
                    markerEnd: {
                        type: MarkerType.ArrowClosed,
                        width: 20,
                        height: 20,
                    },
                }));

                setNodes(flowNodes);
                setEdges(flowEdges);
                setSettings(graphSettings);
                setWarnings(graph.warnings || []);
            } catch (e) {
                if (!mounted) return;
                const errorMessage = e instanceof Error ? e.message : 'Failed to load graph data';
                console.error('Error loading graph data:', errorMessage);
                setError(errorMessage);
            } finally {
                if (mounted) {
                    setIsLoading(false);
                }
            }
        }

        loadGraphData();
        return () => { mounted = false; };
    }, [selectedBuild?.id]);

    const handleNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
        onNodeSelect(node.data);
    }, [onNodeSelect]);

    if (error) {
        return <div className="graph-error">{error}</div>;
    }

    if (isLoading || !settings) {
        return <div className="graph-loading">Loading graph data...</div>;
    }

    return (
        <div className="graph-container" style={{ height: settings.layout.height }}>
            {warnings.length > 0 && (
                <div className="graph-warnings">
                    {warnings.map((warning, index) => (
                        <div key={index} className="graph-warning">
                            <span className="warning-icon">⚠️</span>
                            <span className="warning-message">{warning.message}</span>
                        </div>
                    ))}
                </div>
            )}
            <ErrorBoundary>
                <ReactFlowProvider>
                    <ReactFlow
                        nodes={nodes}
                        edges={edges}
                        nodeTypes={nodeTypes}
                        onNodeClick={handleNodeClick}
                        fitView
                        defaultViewport={{ x: 0, y: 0, zoom: 1 }}
                    >
                        <Background />
                        <Controls />
                    </ReactFlow>
                </ReactFlowProvider>
            </ErrorBoundary>
        </div>
    );
} 