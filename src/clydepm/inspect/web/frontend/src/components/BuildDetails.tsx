import React, { useState } from 'react';
import { BuildData, SourceFile, SourceTree } from '../types';
import { formatDuration, formatDateTime } from '../utils/time';
import { BuildInspector } from './BuildInspector';

interface BuildDetailsProps {
    build: BuildData;
}

function createSourceTree(build: BuildData): SourceTree {
    const root: SourceTree = {
        name: build.package.name,
        path: `src/${build.package.name}`,
        type: 'directory',
        children: []
    };

    // Add source files from compilation steps
    const sourceFiles = new Set<string>();
    for (const step of build.compilation_steps) {
        sourceFiles.add(step.source_file);
        if (step.object_file) {
            sourceFiles.add(step.object_file);
        }
    }

    if (sourceFiles.size > 0) {
        const sourceDir: SourceTree = {
            name: 'src',
            path: `src/${build.package.name}/src`,
            type: 'directory',
            children: Array.from(sourceFiles).sort().map(path => ({
                name: path.split('/').pop() || path,
                path: path,
                type: path.endsWith('.h') || path.endsWith('.hpp') ? 'header' : 'source',
                children: []
            }))
        };
        if (!root.children) root.children = [];
        root.children.push(sourceDir);
    }

    // Add dependencies
    if (build.resolved_dependencies.length > 0) {
        const depsDir: SourceTree = {
            name: 'deps',
            path: `src/${build.package.name}/deps`,
            type: 'directory',
            children: build.resolved_dependencies.map(dep => dep.source_tree)
        };
        if (!root.children) root.children = [];
        root.children.push(depsDir);
    }

    return root;
}

export function BuildDetails({ build }: BuildDetailsProps) {
    const [selectedFile, setSelectedFile] = useState<SourceFile | null>(null);
    
    const duration = build.metrics?.total_time
        ? `${build.metrics.total_time.toFixed(2)}s`
        : 'In progress';

    const sourceTree = createSourceTree(build);

    return (
        <div className="build-details">
            <div className="build-details-scroll">
                <div className="build-info">
                    <h2>Build Details</h2>
                    <div className="build-header">
                        <div>
                            <h3>{build.package.name} {build.version}</h3>
                            <div className={`build-status ${build.error ? 'error' : 'success'}`}>
                                {build.error ? 'Failed' : 'Success'}
                            </div>
                        </div>
                        <div className="build-timing">
                            <div>Started: {formatDateTime(new Date(build.timestamp))}</div>
                            <div>Duration: {duration}</div>
                        </div>
                    </div>

                    {build.error && (
                        <div className="build-error">
                            <h3>Build Error</h3>
                            <pre>{build.error}</pre>
                        </div>
                    )}

                    {build.compiler_info && (
                        <div className="compiler-info">
                            <h3>Compiler Information</h3>
                            <div>Name: {build.compiler_info.name}</div>
                            <div>Version: {build.compiler_info.version}</div>
                            <div>Target: {build.compiler_info.target}</div>
                        </div>
                    )}

                    {build.include_paths.length > 0 && (
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
                            {build.library_paths.length > 0 && (
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

                    {build.resolved_dependencies.length > 0 && (
                        <div className="dependencies">
                            <h3>Dependencies</h3>
                            <ul>
                                {build.resolved_dependencies.map((dep) => (
                                    <li key={`${dep.package.name}-${dep.version}`}>
                                        {dep.package.name} @ {dep.version}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>

                <div className="source-files-section">
                    <h3>Source Files</h3>
                    {sourceTree && (
                        <BuildInspector
                            sourceTree={sourceTree}
                            includePaths={build.include_paths.map(path => ({
                                path,
                                type: 'user',
                                from_package: build.package.name
                            }))}
                            selectedFile={selectedFile}
                            onFileSelect={setSelectedFile}
                        />
                    )}
                </div>
            </div>
        </div>
    );
} 