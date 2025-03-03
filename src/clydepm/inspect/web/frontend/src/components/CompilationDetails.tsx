import React from 'react';
import type { SourceFile } from '../types';
import '../styles/CompilationDetails.css';

interface CompilationDetailsProps {
    file: SourceFile;
}

export const CompilationDetails: React.FC<CompilationDetailsProps> = ({ file }) => {
    return (
        <div className="compilation-details">
            <h3>Compilation Details</h3>
            
            {/* Basic file info */}
            <div className="file-info">
                <div className="info-row">
                    <span className="label">File:</span>
                    <span className="value">{file.path}</span>
                </div>
                <div className="info-row">
                    <span className="label">Type:</span>
                    <span className="value">{file.type}</span>
                </div>
                <div className="info-row">
                    <span className="label">Size:</span>
                    <span className="value">{file.size} bytes</span>
                </div>
            </div>

            {/* Header relationships */}
            <div className="header-info">
                <h4>Header Information</h4>
                {file.includes && file.includes.length > 0 && (
                    <div className="includes-section">
                        <h5>Included Headers</h5>
                        <ul className="include-list">
                            {Object.entries(
                                file.includes.reduce<Record<string, string[]>>((groups, include) => {
                                    const type = include.startsWith('<') ? 'system' :
                                               include.includes('my-project/') ? 'project' : 'local';
                                    if (!groups[type]) groups[type] = [];
                                    groups[type].push(include);
                                    return groups;
                                }, {})
                            ).map(([type, headers]) => (
                                <div key={type} className="include-group">
                                    <h6>{type.charAt(0).toUpperCase() + type.slice(1)} Headers</h6>
                                    {headers.map((include, index) => (
                                        <li key={index} className={`include-item ${type}`}>
                                            <code>{include}</code>
                                        </li>
                                    ))}
                                </div>
                            ))}
                        </ul>
                    </div>
                )}
                {file.included_by && file.included_by.length > 0 && (
                    <div className="included-by-section">
                        <h5>Included By</h5>
                        <ul className="include-list">
                            {file.included_by.map((includer, index) => (
                                <li key={index} className="include-item">
                                    <code>{includer}</code>
                                </li>
                            ))}
                        </ul>
                    </div>
                )}
            </div>

            {/* Compiler command section */}
            {file.compiler_command && (
                <div className="compiler-info">
                    <h4>Compiler Command</h4>
                    <pre className="command-line">{file.compiler_command.command_line}</pre>
                    
                    {/* Include paths */}
                    <div className="include-paths-section">
                        <h5>Include Paths</h5>
                        <ul className="include-paths-list">
                            {file.compiler_command.include_paths.map((path, index) => (
                                <li key={index} className={`include-path ${path.type}`}>
                                    <span className="path-type">{path.type}</span>
                                    <span className="path-value">{path.path}</span>
                                </li>
                            ))}
                        </ul>
                    </div>

                    {/* Compiler flags */}
                    <div className="flags">
                        <h5>Compiler Flags</h5>
                        <ul>
                            {file.compiler_command.flags.map((flag, index) => (
                                <li key={index}>{flag}</li>
                            ))}
                        </ul>
                    </div>

                    {/* Defines */}
                    {file.compiler_command.defines && (
                        <div className="defines">
                            <h5>Preprocessor Defines</h5>
                            <ul className="defines-list">
                                {Object.entries(file.compiler_command.defines).map(([key, value], index) => (
                                    <li key={index} className="define">
                                        <span className="define-name">{key}</span>
                                        {value !== null && (
                                            <span className="define-value">= {value}</span>
                                        )}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}

                    <div className="info-row">
                        <span className="label">Duration:</span>
                        <span className="value">{file.compiler_command.duration_ms}ms</span>
                    </div>
                    <div className="info-row">
                        <span className="label">Cache:</span>
                        <span className="value">{file.compiler_command.cache_hit ? 'Hit' : 'Miss'}</span>
                    </div>
                </div>
            )}

            {/* Warnings section */}
            {file.warnings && file.warnings.length > 0 && (
                <div className="warnings">
                    <h4>Warnings</h4>
                    <ul className="warning-list">
                        {file.warnings.map((warning, index) => (
                            <li key={index} className="warning-item">
                                <div className="warning-location">{warning.location}</div>
                                <div className="warning-message">{warning.message}</div>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}; 