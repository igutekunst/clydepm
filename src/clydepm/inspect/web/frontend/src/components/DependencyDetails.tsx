import React, { useEffect, useState } from 'react';
import { fetchPackageDetails } from '../api/client';
import type { DependencyNode, SourceFile } from '../types';
import { BuildInspector } from './BuildInspector';
import { useDependencyDetails } from '../hooks/useDependencyDetails';
import '../styles/DependencyDetails.css';

interface DependencyDetailsProps {
    packageId: string | null;
}

export function DependencyDetails({ packageId }: DependencyDetailsProps) {
    const { details, isLoading, error } = useDependencyDetails(packageId);
    const [selectedFile, setSelectedFile] = useState<SourceFile | null>(null);

    if (isLoading) return <div>Loading...</div>;
    if (error) return <div>Error: {error.message}</div>;
    if (!details) return <div>Select a package to view details</div>;

    const handleFileSelect = (file: SourceFile | null) => {
        console.log('File selected:', file?.path);
        setSelectedFile(file);
    };

    return (
        <div className="dependency-details">
            <div className="package-header">
                <h2>{details.name} v{details.version}</h2>
                {details.has_warnings && (
                    <div className="warning-badge">⚠️ Has Warnings</div>
                )}
            </div>

            <BuildInspector
                sourceTree={details.source_tree}
                includePaths={details.include_paths}
                selectedFile={selectedFile}
                onFileSelect={handleFileSelect}
            />
        </div>
    );
} 