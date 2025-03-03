import React from 'react';
import { SourceTree as SourceTreeComponent } from './SourceTree';
import { CompilationDetails } from './CompilationDetails';
import type { SourceTree, SourceFile, IncludePath } from '../types';
import '../styles/BuildInspector.css';

interface BuildInspectorProps {
    sourceTree: SourceTree;
    includePaths: IncludePath[];
    selectedFile: SourceFile | null;
    onFileSelect: (file: SourceFile | null) => void;
}

export const BuildInspector: React.FC<BuildInspectorProps> = ({
    sourceTree,
    includePaths,
    selectedFile,
    onFileSelect,
}) => {
    console.log('BuildInspector render:', {
        hasSourceTree: !!sourceTree,
        selectedFile,
        includePathsCount: includePaths?.length
    });

    return (
        <div className="build-inspector">
            <div className="source-panel">
                <h3>Source Files</h3>
                <SourceTreeComponent
                    tree={sourceTree}
                    onFileSelect={onFileSelect}
                    selectedFile={selectedFile}
                />
            </div>
            <div className="compilation-panel">
                {selectedFile ? (
                    <CompilationDetails file={selectedFile} />
                ) : (
                    <div className="package-info">
                        <h3>Package Information</h3>
                        <p>Select a source file to view compilation details</p>
                        <div className="include-paths">
                            <h4>Include Paths</h4>
                            {includePaths.map((path, index) => (
                                <div key={index} className={`include-path ${path.type}`}>
                                    {path.path}
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}; 