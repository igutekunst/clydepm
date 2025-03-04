import React from 'react';
import { BuildData } from '../types';
import { formatDateTime } from '../utils/time';

interface BuildListProps {
    builds: BuildData[];
    selectedBuild?: BuildData;
    onSelectBuild: (build: BuildData) => void;
}

export function BuildList({ builds, selectedBuild, onSelectBuild }: BuildListProps) {
    return (
        <div className="build-list">
            <h2>Build History</h2>
            <div className="builds">
                {builds.map((build) => (
                    <div
                        key={build.start_time}
                        className={`build-item ${build.success ? 'success' : 'error'} ${selectedBuild?.start_time === build.start_time ? 'selected' : ''}`}
                        onClick={() => onSelectBuild(build)}
                    >
                        <div className="build-item-header">
                            <span className="package-name">{build.package_name}</span>
                            <span className="package-version">{build.package_version}</span>
                        </div>
                        <div className="build-item-time">
                            {formatDateTime(new Date(build.start_time))}
                        </div>
                        <div className="build-item-status">
                            {build.success ? 'Success' : 'Failed'}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
} 