import { useState } from 'react';
import { DependencyGraph } from './components/DependencyGraph';
import { DependencyDetails } from './components/DependencyDetails';
import type { DependencyNode } from './types';
import './styles/DependencyGraph.css';
import './styles/main.css';

export function App() {
    const [selectedPackage, setSelectedPackage] = useState<string | null>(null);

    const handleNodeClick = (node: DependencyNode) => {
        setSelectedPackage(node.id);
    };

    return (
        <div className="app">
            <header className="app-header">
                <h1>Clyde Build Inspector</h1>
            </header>
            
            <main className="app-content">
                <div className="graph-container">
                    <DependencyGraph onNodeClick={handleNodeClick} />
                </div>
                
                <aside className="details-panel">
                    <DependencyDetails packageId={selectedPackage} />
                </aside>
            </main>
        </div>
    );
} 