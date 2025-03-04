import React, { useEffect, useState } from 'react';
import { DependencyGraph } from './components/DependencyGraph';
import { DependencyDetails } from './components/DependencyDetails';
import { BuildDetails } from './components/BuildDetails';
import { BuildList } from './components/BuildList';
import { getAllBuilds, getLatestPackageBuild } from './api/client';
import type { DependencyNode, BuildData } from './types';
import './styles/DependencyGraph.css';
import './styles/main.css';
import './styles/App.css';
import './styles/BuildDetails.css';
import './styles/BuildList.css';

export function App() {
    const [selectedNode, setSelectedNode] = useState<DependencyNode | null>(null);
    const [allBuilds, setAllBuilds] = useState<BuildData[]>([]);
    const [selectedBuild, setSelectedBuild] = useState<BuildData | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    const handleNodeSelect = (node: DependencyNode | null) => {
        setSelectedNode(node);
    };

    useEffect(() => {
        async function loadBuilds() {
            try {
                setIsLoading(true);
                setError(null);
                
                // Get all builds
                const builds = await getAllBuilds();
                setAllBuilds(builds);
                
                // If we have builds, try to get the latest build for the first package
                if (builds.length > 0 && builds[0].package?.name) {
                    try {
                        const latestBuild = await getLatestPackageBuild(builds[0].package.name);
                        if (latestBuild) {
                            setSelectedBuild(latestBuild);
                        } else {
                            // If we can't get the latest build, use the first one
                            setSelectedBuild(builds[0]);
                        }
                    } catch (latestError) {
                        console.error('Error loading latest build:', latestError);
                        // If we fail to get the latest build but have all builds, just use the first one
                        setSelectedBuild(builds[0]);
                    }
                }
            } catch (e) {
                const errorMessage = e instanceof Error ? e.message : 'Failed to load builds';
                console.error('Error loading builds:', e);
                setError(errorMessage);
            } finally {
                setIsLoading(false);
            }
        }
        
        loadBuilds();
    }, []);

    const handleSelectBuild = async (build: BuildData) => {
        try {
            setError(null);
            // Try to get the latest build for this package
            if (build.package?.name) {
                try {
                    const latestBuild = await getLatestPackageBuild(build.package.name);
                    if (latestBuild) {
                        setSelectedBuild(latestBuild);
                        return;
                    }
                } catch (e) {
                    console.error('Error getting latest build:', e);
                }
            }
            // If we can't get the latest build, use the selected one
            setSelectedBuild(build);
        } catch (e) {
            console.error('Error selecting build:', e);
            // If we fail to get the latest build, just use the selected one
            setSelectedBuild(build);
        }
    };

    if (isLoading) {
        return <div className="loading">Loading builds...</div>;
    }

    if (error && !allBuilds.length) {
        return <div className="error">Error: {error}</div>;
    }

    return (
        <div className="app">
            <div className="sidebar">
                <BuildList
                    builds={allBuilds}
                    selectedBuild={selectedBuild}
                    onSelectBuild={handleSelectBuild}
                />
            </div>
            <div className="main-content">
                <header className="app-header">
                    <h1>Clyde Build Inspector</h1>
                </header>
                
                <main className="app-content">
                    {selectedBuild ? (
                        <BuildDetails build={selectedBuild} />
                    ) : (
                        <div className="no-build-selected">
                            Select a build to view details
                        </div>
                    )}
                </main>
            </div>
        </div>
    );
} 