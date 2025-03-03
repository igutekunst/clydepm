import React from 'react';
import type { SourceFile } from '../types';

interface CompilationDetailsProps {
    file: SourceFile;
}

export const CompilationDetails: React.FC<CompilationDetailsProps> = ({ file }) => {
    console.log('Rendering compilation details for:', file); // Debug log

    return (
        <div className="compilation-details">
            <h3>Compilation Details: {file.path}</h3>
            
            {file.compiler_command ? (
                <>
                    <div className="command-section">
                        <h4>Compiler Command</h4>
                        <div className="command-line">
                            {file.compiler_command.command_line}
                        </div>
                        
                        <div className="compilation-stats">
                            <div className="stat">
                                <span>Duration:</span>
                                <span>{file.compiler_command.duration_ms}ms</span>
                            </div>
                            <div className="stat">
                                <span>Cache:</span>
                                <span className={file.compiler_command.cache_hit ? 'hit' : 'miss'}>
                                    {file.compiler_command.cache_hit ? 'Hit' : 'Miss'}
                                </span>
                            </div>
                        </div>

                        {file.compiler_command.flags.length > 0 && (
                            <div className="flags-section">
                                <h4>Compiler Flags</h4>
                                <div className="flags-list">
                                    {file.compiler_command.flags.map((flag, index) => (
                                        <span key={index} className="flag">{flag}</span>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>

                    {file.warnings && file.warnings.length > 0 && (
                        <div className="warnings-section">
                            <h4>Warnings ({file.warnings.length})</h4>
                            {file.warnings.map((warning, index) => (
                                <div key={index} className="warning">
                                    <div className="warning-header">
                                        <span className="location">{warning.location}</span>
                                    </div>
                                    <p className="message">{warning.message}</p>
                                </div>
                            ))}
                        </div>
                    )}
                </>
            ) : (
                <div className="no-compilation">
                    <p>No compilation information available for this file</p>
                    <p className="file-info">
                        Type: {file.type}<br />
                        Size: {file.size} bytes
                    </p>
                </div>
            )}
        </div>
    );
}; 