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

            {file.compiler_command && (
                <div className="compiler-info">
                    <h4>Compiler Command</h4>
                    <pre className="command-line">{file.compiler_command.command_line}</pre>
                    <div className="info-row">
                        <span className="label">Duration:</span>
                        <span className="value">{file.compiler_command.duration_ms}ms</span>
                    </div>
                    <div className="info-row">
                        <span className="label">Cache:</span>
                        <span className="value">{file.compiler_command.cache_hit ? 'Hit' : 'Miss'}</span>
                    </div>
                    {file.compiler_command.flags.length > 0 && (
                        <div className="flags">
                            <h4>Compiler Flags</h4>
                            <ul>
                                {file.compiler_command.flags.map((flag, index) => (
                                    <li key={index}>{flag}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            )}

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