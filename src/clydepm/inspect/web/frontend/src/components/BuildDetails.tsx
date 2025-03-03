import React from 'react';
import type { SourceFile } from '../types';

interface BuildDetailsProps {
    file: SourceFile;
}

export const BuildDetails: React.FC<BuildDetailsProps> = ({ file }) => {
    return (
        <div className="build-details">
            <h3>{file.path}</h3>
            
            <div className="file-info">
                <div className="info-item">
                    <label>Type:</label>
                    <span>{file.type}</span>
                </div>
                <div className="info-item">
                    <label>Size:</label>
                    <span>{(file.size / 1024).toFixed(2)} KB</span>
                </div>
                {file.objectSize && (
                    <div className="info-item">
                        <label>Object Size:</label>
                        <span>{(file.objectSize / 1024).toFixed(2)} KB</span>
                    </div>
                )}
            </div>

            {file.compilerCommand && (
                <div className="compiler-info">
                    <h4>Compiler Command</h4>
                    <pre className="command-line">{file.compilerCommand.commandLine}</pre>
                    
                    <div className="compilation-stats">
                        <div className="stat">
                            <label>Duration:</label>
                            <span>{file.compilerCommand.durationMs.toFixed(2)}ms</span>
                        </div>
                        <div className="stat">
                            <label>Cache:</label>
                            <span className={file.compilerCommand.cacheHit ? 'hit' : 'miss'}>
                                {file.compilerCommand.cacheHit ? 'HIT' : 'MISS'}
                            </span>
                        </div>
                    </div>
                </div>
            )}

            {file.warnings.length > 0 && (
                <div className="warnings">
                    <h4>Warnings</h4>
                    {file.warnings.map((warning, index) => (
                        <div key={index} className={`warning ${warning.level}`}>
                            <div className="warning-header">
                                <span className="location">{warning.line}:{warning.column}</span>
                                {warning.flag && <span className="flag">{warning.flag}</span>}
                            </div>
                            <div className="message">{warning.message}</div>
                        </div>
                    ))}
                </div>
            )}

            <div className="dependencies">
                <h4>Dependencies</h4>
                <div className="includes">
                    <h5>Includes ({file.includes.length})</h5>
                    <ul>
                        {file.includes.map((include, index) => (
                            <li key={index}>{include}</li>
                        ))}
                    </ul>
                </div>
                <div className="included-by">
                    <h5>Included By ({file.includedBy.length})</h5>
                    <ul>
                        {file.includedBy.map((includer, index) => (
                            <li key={index}>{includer}</li>
                        ))}
                    </ul>
                </div>
            </div>
        </div>
    );
}; 