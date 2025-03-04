import React, { useState } from 'react';
import { BuildData, SourceFile, SourceTree } from '../types';
import { formatDuration, formatDateTime } from '../utils/time';
import { BuildInspector } from './BuildInspector';

interface BuildDetailsProps {
    build: BuildData;
}

function createSourceTree(packageName: string, build: BuildData): SourceTree {
    // Create a root node for the package
    const root: SourceTree = {
        name: packageName,
        path: '/',
        type: 'directory',
        children: []
    };

    // Add source files from compilation steps
    if (build.compilation_steps && build.compilation_steps.length > 0) {
        const sourceFiles = new Set<string>();
        build.compilation_steps.forEach(step => {
            sourceFiles.add(step.source_file);
            if (step.object_file) {
                sourceFiles.add(step.object_file);
            }
        });

        // Create source directory
        const sourceDir: SourceTree = {
            name: 'src',
            path: '/src',
            type: 'directory',
            children: Array.from(sourceFiles).map(file => ({
                name: file.split('/').pop() || file,
                path: file,
                type: file.endsWith('.h') || file.endsWith('.hpp') ? 'header' : 'source',
                children: []
            }))
        };
        root.children.push(sourceDir);
    }

    // Add dependencies as directories
    if (build.dependency_graph && build.dependency_graph[packageName]) {
        const depsDir: SourceTree = {
            name: 'deps',
            path: '/deps',
            type: 'directory',
            children: build.dependency_graph[packageName].map(dep => ({
                name: dep,
                path: `/deps/${dep}`,
                type: 'directory',
                children: []
            }))
        };
        root.children.push(depsDir);
    }

    return root;
}

export function BuildDetails({ build }: BuildDetailsProps) {
    const [selectedStepIndex, setSelectedStepIndex] = useState<number | null>(null);
    const [selectedFile, setSelectedFile] = useState<SourceFile | null>(null);
    
    const duration = build.end_time 
        ? formatDuration(new Date(build.start_time), new Date(build.end_time))
        : 'In progress';

    const sourceTree = createSourceTree(build.package_name, build);

    return (
        <div className="build-details">
            <div className="build-info">
                <h2>Build Details</h2>
                <div className="build-header">
                    <div>
                        <h3>{build.package_name} {build.package_version}</h3>
                        <div className={`build-status ${build.success ? 'success' : 'error'}`}>
                            {build.success ? 'Success' : 'Failed'}
                        </div>
                    </div>
                    <div className="build-timing">
                        <div>Started: {formatDateTime(new Date(build.start_time))}</div>
                        <div>Duration: {duration}</div>
                    </div>
                </div>

                {build.compiler_info && (
                    <div className="compiler-info">
                        <h3>Compiler Information</h3>
                        <div>Name: {build.compiler_info.name}</div>
                        <div>Version: {build.compiler_info.version}</div>
                        <div>Target: {build.compiler_info.target}</div>
                    </div>
                )}

                {build.include_paths && build.include_paths.length > 0 && (
                    <div className="build-paths">
                        <h3>Build Paths</h3>
                        <div className="include-paths">
                            <h4>Include Paths</h4>
                            <ul>
                                {build.include_paths.map((path, i) => (
                                    <li key={i}>{path}</li>
                                ))}
                            </ul>
                        </div>
                        {build.library_paths && build.library_paths.length > 0 && (
                            <div className="library-paths">
                                <h4>Library Paths</h4>
                                <ul>
                                    {build.library_paths.map((path, i) => (
                                        <li key={i}>{path}</li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                )}

                {build.dependencies && Object.keys(build.dependencies).length > 0 && (
                    <div className="dependencies">
                        <h3>Dependencies</h3>
                        <ul>
                            {Object.entries(build.dependencies).map(([name, version]) => (
                                <li key={name}>{name} @ {version}</li>
                            ))}
                        </ul>
                    </div>
                )}

                {build.compilation_steps && build.compilation_steps.length > 0 && (
                    <div className="compilation-steps">
                        <h3>Compilation Steps</h3>
                        {build.compilation_steps.map((step, i) => (
                            <div 
                                key={i} 
                                className={`compilation-step ${step.success ? 'success' : 'error'} ${selectedStepIndex === i ? 'selected' : ''}`}
                                onClick={() => setSelectedStepIndex(selectedStepIndex === i ? null : i)}
                            >
                                <div className="step-header">
                                    <div className="step-files">
                                        <div>Source: {step.source_file}</div>
                                        <div>Object: {step.object_file}</div>
                                    </div>
                                    <div className="step-timing">
                                        <div>Started: {formatDateTime(new Date(step.start_time))}</div>
                                        {step.end_time && (
                                            <div>
                                                Duration: {formatDuration(new Date(step.start_time), new Date(step.end_time))}
                                            </div>
                                        )}
                                    </div>
                                </div>
                                {step.error && (
                                    <div className="step-error">
                                        {step.error}
                                    </div>
                                )}
                                {selectedStepIndex === i && (
                                    <div className="step-details">
                                        {step.command && step.command.length > 0 && (
                                            <div className="step-command">
                                                <h4>Command</h4>
                                                <pre><code>{step.command.join(' ')}</code></pre>
                                            </div>
                                        )}
                                        {step.include_paths && step.include_paths.length > 0 && (
                                            <div className="step-includes">
                                                <h4>Include Paths</h4>
                                                <ul>
                                                    {step.include_paths.map((path, j) => (
                                                        <li key={j}>{path}</li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}

                {build.error && (
                    <div className="build-error">
                        <h3>Build Error</h3>
                        <pre>{build.error}</pre>
                    </div>
                )}
            </div>

            <div className="build-inspector-container">
                <h3>Source Files</h3>
                {sourceTree && (
                    <BuildInspector
                        sourceTree={sourceTree}
                        includePaths={build.include_paths.map(path => ({ path, type: 'user', from_package: build.package_name }))}
                        selectedFile={selectedFile}
                        onFileSelect={setSelectedFile}
                    />
                )}
            </div>
        </div>
    );
} 