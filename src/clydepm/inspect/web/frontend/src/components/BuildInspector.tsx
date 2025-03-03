import React, { useState } from 'react';
import { SourceTree as SourceTreeComponent } from './SourceTree';
import { BuildDetails } from './BuildDetails';
import type { SourceTree, SourceFile } from '../types';

interface BuildInspectorProps {
    sourceTree: SourceTree;
    includePaths: IncludePath[];
}

export const BuildInspector: React.FC<BuildInspectorProps> = ({
    sourceTree,
    includePaths,
}) => {
    const [selectedFile, setSelectedFile] = useState<SourceFile | null>(null);

    return (
        <div className="build-inspector">
            <div className="source-tree-container">
                <h3>Source Files</h3>
                <SourceTreeComponent
                    tree={sourceTree}
                    onFileSelect={setSelectedFile}
                />
            </div>
            <div className="include-paths">
                <h3>Include Paths</h3>
                <div className="include-paths-list">
                    {includePaths.map((path, index) => (
                        <div
                            key={index}
                            className={`include-path ${path.type}`}
                            title={path.fromPackage ? `From: ${path.fromPackage}` : undefined}
                        >
                            {path.path}
                        </div>
                    ))}
                </div>
            </div>
            {selectedFile && (
                <BuildDetails file={selectedFile} />
            )}
        </div>
    );
}; 