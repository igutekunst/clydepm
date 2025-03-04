import React, { useState, useEffect } from 'react';
import { DependencyGraph } from './components/DependencyGraph';
import { DependencyDetails } from './components/DependencyDetails';
import { BuildDetails } from './components/BuildDetails';
import { BuildList } from './components/BuildList';
import { getLatestPackageBuild, getAllBuilds } from './api/client';
import type { DependencyNode, BuildData } from './types';
import './styles/DependencyGraph.css';
import './styles/main.css';
import './styles/App.css';
import './styles/BuildDetails.css';
import './styles/BuildList.css';

export function App() {
    const [selectedNode, setSelectedNode] = useState<DependencyNode | null>(null);
    const [selectedBuild, setSelectedBuild] = useState<BuildData | undefined>(undefined);
    const [builds, setBuilds] = useState<BuildData[]>([]);
    const [error, setError] = useState<string | null>(null);

    const handleNodeSelect = (node: DependencyNode | null) => {
        setSelectedNode(node);
    };

    useEffect(() => {
        const loadBuilds = async () => {
            try {
                const allBuilds = await getAllBuilds();
                setBuilds(allBuilds);
                if (allBuilds.length > 0) {
                    const latestBuild = await getLatestPackageBuild(allBuilds[0].package_name);
                    setSelectedBuild(latestBuild || undefined);
                }
            } catch (error) {
                console.error('Failed to load builds:', error);
                setError(error instanceof Error ? error.message : 'Failed to load builds');
            }
        };
        loadBuilds();
    }, []);

    return (
        <div className="app">
            <div className="sidebar">
                <BuildList
                    builds={builds}
                    selectedBuild={selectedBuild}
                    onSelectBuild={setSelectedBuild}
                />
            </div>
            <div className="main-content">
                <header className="app-header">
                    <h1>Clyde Build Inspector</h1>
                </header>
                
                <main className="app-content">
                    {error && (
                        <div className="error-message">
                            {error}
                        </div>
                    )}
                    
                    <div className="content-grid">
                        <div className="graph-section">
                            <DependencyGraph onNodeSelect={handleNodeSelect} />
                        </div>
                        <div className="details-section">
                            {selectedNode && (
                                <DependencyDetails packageId={selectedNode.id} />
                            )}
                            {selectedBuild && (
                                <BuildDetails build={selectedBuild} />
                            )}
                        </div>
                    </div>
                </main>
            </div>
        </div>
    );
} 