import React from 'react';
import { BuildData } from '../types';
import { formatDateTime } from '../utils/time';

interface BuildListProps {
    builds: BuildData[];
    selectedBuild: BuildData | null;
    onSelectBuild: (build: BuildData) => void;
}

export function BuildList({ builds, selectedBuild, onSelectBuild }: BuildListProps) {
    return (
        <div className="build-list">
            <h2>Build History</h2>
            <div className="builds">
                {builds.map((build) => (
                    <div
                        key={`${build.id}-${build.package.name}-${build.version}`}
                        className={`build-item ${build.status === 'success' ? 'success' : 'error'} ${selectedBuild?.id === build.id ? 'selected' : ''}`}
                        onClick={() => onSelectBuild(build)}
                    >
                        <div className="build-item-header">
                            <span className="package-name">{build.package.name}</span>
                            <span className="package-version">{build.version}</span>
                        </div>
                        <div className="build-item-time">
                            {formatDateTime(new Date(build.timestamp))}
                        </div>
                        <div className="build-item-status">
                            {build.status === 'success' ? 'Success' : 'Failed'}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
} 