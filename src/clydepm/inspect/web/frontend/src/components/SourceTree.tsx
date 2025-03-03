import React, { useState } from 'react';
import type { SourceTree as SourceTreeType, SourceFile } from '../types';

interface SourceTreeProps {
    tree: SourceTreeType;
    onFileSelect: (file: SourceFile) => void;
    level?: number;
}

export const SourceTree: React.FC<SourceTreeProps> = ({
    tree,
    onFileSelect,
    level = 0
}) => {
    const [isExpanded, setIsExpanded] = useState(level < 2);

    const handleClick = () => {
        if (tree.type === 'directory') {
            setIsExpanded(!isExpanded);
        } else if (tree.fileInfo) {
            onFileSelect(tree.fileInfo);
        }
    };

    const getFileIcon = () => {
        if (tree.type === 'directory') {
            return isExpanded ? '📂' : '📁';
        }
        return tree.fileInfo?.type === 'header' ? '📄' : '📝';
    };

    return (
        <div className="source-tree-node" style={{ marginLeft: `${level * 20}px` }}>
            <div
                className={`tree-item ${tree.type} ${tree.fileInfo?.warnings.length ? 'has-warnings' : ''}`}
                onClick={handleClick}
            >
                <span className="icon">{getFileIcon()}</span>
                <span className="name">{tree.name}</span>
                {tree.fileInfo?.warnings.length > 0 && (
                    <span className="warning-count">⚠️ {tree.fileInfo.warnings.length}</span>
                )}
            </div>
            {isExpanded && tree.children && (
                <div className="children">
                    {tree.children.map((child, index) => (
                        <SourceTree
                            key={index}
                            tree={child}
                            onFileSelect={onFileSelect}
                            level={level + 1}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}; 