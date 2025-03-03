import React, { useEffect, useState } from 'react';
import { fetchPackageDetails } from '../api/client';
import type { DependencyNode } from '../types';
import { BuildInspector } from './BuildInspector';

interface DependencyDetailsProps {
    packageId: string | null;
}

export const DependencyDetails: React.FC<DependencyDetailsProps> = ({ packageId }) => {
    const [details, setDetails] = useState<DependencyNode | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!packageId) {
            setDetails(null);
            return;
        }

        const loadDetails = async () => {
            try {
                setLoading(true);
                setError(null);
                const data = await fetchPackageDetails(packageId);
                setDetails(data);
            } catch (err) {
                setError('Failed to load package details');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        loadDetails();
    }, [packageId]);

    if (!packageId) {
        return (
            <div className="details-empty">
                <p>Select a package to view details</p>
            </div>
        );
    }

    if (loading) {
        return <div className="details-loading">Loading...</div>;
    }

    if (error) {
        return <div className="details-error">{error}</div>;
    }

    if (!details) {
        return null;
    }

    return (
        <div className="details-content">
            <div className="package-header">
                <h2>{details.name}@{details.version}</h2>
                <div className="package-badges">
                    {details.is_dev_dep && <span className="badge dev">Dev</span>}
                    {details.has_warnings && <span className="badge warning">⚠️ Warnings</span>}
                </div>
            </div>

            <div className="metrics-summary">
                <div className="metric">
                    <label>Build Time</label>
                    <span>{details.build_metrics.total_time.toFixed(2)}s</span>
                </div>
                <div className="metric">
                    <label>Cache</label>
                    <span>{details.build_metrics.cache_hits}/{details.build_metrics.cache_hits + details.build_metrics.cache_misses}</span>
                </div>
                <div className="metric">
                    <label>Size</label>
                    <span>{(details.size / 1024).toFixed(1)} KB</span>
                </div>
                <div className="metric">
                    <label>Files</label>
                    <span>{details.build_metrics.files_compiled}</span>
                </div>
            </div>

            <div className="compiler-config">
                <h3>Compiler Configuration</h3>
                {Object.entries(details.compiler_config).map(([key, value]) => (
                    <div key={key} className="config-item">
                        <label>{key}</label>
                        <code>{value}</code>
                    </div>
                ))}
            </div>

            <BuildInspector
                sourceTree={details.source_tree}
                includePaths={details.include_paths}
            />

            <div className="details-section">
                <h3>Dependencies</h3>
                <p>Direct: {details.direct_deps.length}</p>
                <p>Total: {details.all_deps.length}</p>
                <ul>
                    {details.direct_deps.map(dep => (
                        <li key={dep}>{dep}</li>
                    ))}
                </ul>
            </div>

            <div className="details-section">
                <h3>Last Used</h3>
                <p>{new Date(details.last_used).toLocaleString()}</p>
            </div>
        </div>
    );
}; 