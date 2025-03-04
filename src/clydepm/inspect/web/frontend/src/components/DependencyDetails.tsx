import React from 'react';
import type { DependencyNode } from '../types';
import '../styles/DependencyDetails.css';

interface DependencyDetailsProps {
    node: DependencyNode | null;
}

export function DependencyDetails({ node }: DependencyDetailsProps) {
    if (!node) {
        return <div className="no-dependency-selected">Select a dependency to view details</div>;
    }

    return (
        <div className="dependency-details">
            <h2>{node.name} <span className="version">{node.version}</span></h2>
            
            {node.has_warnings && (
                <div className="warnings">
                    <h3>Warnings</h3>
                    <div className="warning-count">
                        {node.metrics?.total_warnings || 0} warnings
                    </div>
                </div>
            )}
            
            <div className="metrics">
                <h3>Build Metrics</h3>
                {node.metrics ? (
                    <div className="metrics-grid">
                        <div className="metric">
                            <label>Files Compiled</label>
                            <span>{node.metrics.files_compiled}</span>
                        </div>
                        <div className="metric">
                            <label>Cache Hits</label>
                            <span>{node.metrics.cache_hits}</span>
                        </div>
                        <div className="metric">
                            <label>Cache Misses</label>
                            <span>{node.metrics.cache_misses}</span>
                        </div>
                        <div className="metric">
                            <label>Total Time</label>
                            <span>{node.metrics.total_time.toFixed(2)}s</span>
                        </div>
                    </div>
                ) : (
                    <div className="no-metrics">No build metrics available</div>
                )}
            </div>
            
            <div className="dependencies">
                <h3>Dependencies</h3>
                {node.direct_deps.length > 0 ? (
                    <ul className="dependency-list">
                        {node.direct_deps.map(dep => (
                            <li key={dep}>{dep}</li>
                        ))}
                    </ul>
                ) : (
                    <div className="no-dependencies">No dependencies</div>
                )}
            </div>
            
            <div className="source-files">
                <h3>Source Files</h3>
                {/* Assuming BuildInspector component is still used for source files */}
            </div>
        </div>
    );
} 