import React, { useEffect, useState } from 'react';
import { fetchPackageDetails } from '../api/client';
import type { PackageDetails } from '../types';

interface DependencyDetailsProps {
    packageId: string | null;
}

export const DependencyDetails: React.FC<DependencyDetailsProps> = ({ packageId }) => {
    const [details, setDetails] = useState<PackageDetails | null>(null);
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
            <h2>{details.name}@{details.version}</h2>
            
            <div className="details-section">
                <h3>Size</h3>
                <p>{(details.size / 1024).toFixed(1)} KB</p>
            </div>

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

            {details.has_warnings && (
                <div className="details-section warnings">
                    <h3>⚠️ Warnings</h3>
                    <p>This package has warnings</p>
                </div>
            )}

            <div className="details-section">
                <h3>Last Used</h3>
                <p>{new Date(details.last_used).toLocaleString()}</p>
            </div>
        </div>
    );
}; 