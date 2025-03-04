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
    const [selectedPackage, setSelectedPackage] = useState<string | null>(null);
    const [selectedBuild, setSelectedBuild] = useState<BuildData | null>(null);
    const [builds, setBuilds] = useState<BuildData[]>([]);
    const [error, setError] = useState<string | null>(null);

    const handleNodeSelect = (node: DependencyNode | null) => {
        setSelectedPackage(node?.id || null);
    };

    useEffect(() => {
        async function fetchBuilds() {
            try {
                const allBuilds = await getAllBuilds();
                setBuilds(allBuilds);
                if (allBuilds.length > 0) {
                    setSelectedBuild(allBuilds[0]); // Select the latest build
                }
            } catch (e) {
                setError(e instanceof Error ? e.message : 'Failed to fetch build data');
            }
        }
        fetchBuilds();
    }, []);

    return (
        <div className="app">
            <BuildList
                builds={builds}
                selectedBuild={selectedBuild || undefined}
                onSelectBuild={setSelectedBuild}
            />
            
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
                        {selectedBuild && (
                            <div className="build-panel">
                                <BuildDetails build={selectedBuild} />
                            </div>
                        )}
                        
                        <div className="graph-panel">
                            <h2>Dependency Graph</h2>
                            <div className="graph-container">
                                <DependencyGraph onNodeSelect={handleNodeSelect} />
                            </div>
                            
                            <aside className="details-panel">
                                <DependencyDetails packageId={selectedPackage} />
                            </aside>
                        </div>
                    </div>
                </main>
            </div>
        </div>
    );
} 