import React, { useEffect, useState, useCallback } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { fetchDependencyGraph, fetchGraphSettings } from '../api/client';
import type { DependencyNode, DependencyEdge, GraphSettings } from '../types';

interface DependencyGraphProps {
    onNodeSelect: (node: DependencyNode | null) => void;
}

interface ForceGraphNode extends DependencyNode {
    x?: number;
    y?: number;
}

interface ForceGraphLink extends Omit<DependencyEdge, 'source' | 'target'> {
    source: ForceGraphNode;
    target: ForceGraphNode;
}

interface GraphData {
    nodes: ForceGraphNode[];
    links: ForceGraphLink[];
}

export function DependencyGraph({ onNodeSelect }: DependencyGraphProps) {
    const [graphData, setGraphData] = useState<GraphData | null>(null);
    const [settings, setSettings] = useState<GraphSettings | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function loadGraphData() {
            try {
                const [graph, graphSettings] = await Promise.all([
                    fetchDependencyGraph(),
                    fetchGraphSettings()
                ]);

                // Create a map of nodes by ID for quick lookup
                const nodesMap = new Map(graph.nodes.map(node => [node.id, { ...node }]));
                
                // Create the graph data structure that ForceGraph2D expects
                const graphData: GraphData = {
                    nodes: Array.from(nodesMap.values()),
                    links: graph.edges.map(edge => ({
                        ...edge,
                        source: nodesMap.get(edge.source)!,
                        target: nodesMap.get(edge.target)!
                    }))
                };
                
                setGraphData(graphData);
                setSettings(graphSettings);
            } catch (e) {
                setError(e instanceof Error ? e.message : 'Failed to load graph data');
            }
        }
        loadGraphData();
    }, []);

    const handleNodeClick = useCallback((node: ForceGraphNode) => {
        onNodeSelect(node);
    }, [onNodeSelect]);

    if (error) {
        return <div className="graph-error">{error}</div>;
    }

    if (!graphData || !settings) {
        return <div className="graph-loading">Loading graph data...</div>;
    }

    return (
        <ForceGraph2D
            graphData={graphData}
            nodeId="id"
            nodeLabel="name"
            nodeColor={(node: ForceGraphNode) => node.has_warnings ? '#c5221f' : '#1a73e8'}
            nodeVal={(node: ForceGraphNode) => node.size / 1000}
            linkColor={(link: ForceGraphLink) => link.is_circular ? '#c5221f' : '#999'}
            width={settings.layout.width}
            height={settings.layout.height}
            onNodeClick={handleNodeClick}
            nodeCanvasObject={(node: ForceGraphNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
                const label = node.name;
                const fontSize = 12/globalScale;
                ctx.font = `${fontSize}px Sans-Serif`;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillStyle = '#333';
                ctx.fillText(label, node.x || 0, node.y || 0);
            }}
            cooldownTicks={50}
            d3VelocityDecay={0.1}
        />
    );
} 