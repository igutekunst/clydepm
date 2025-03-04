import React, { useState } from 'react';
import type { SourceTree as SourceTreeType, SourceFile } from '../types';

interface SourceTreeProps {
    tree: SourceTreeType;
    onFileSelect: (file: SourceFile | null) => void;
    selectedFile: SourceFile | null;
    level?: number;
}

export const SourceTree: React.FC<SourceTreeProps> = ({
    tree,
    onFileSelect,
    selectedFile,
    level = 0
}) => {
    const [isExpanded, setIsExpanded] = useState(level < 2);

    const handleClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        
        if (tree.type === 'directory') {
            setIsExpanded(!isExpanded);
        } else {
            // Create a SourceFile object from the tree node
            const file: SourceFile = {
                path: tree.path,
                warnings: tree.file_info?.warnings || [],
                errors: tree.file_info?.errors || []
            };
            onFileSelect(file);
        }
    };

    const isSelected = selectedFile?.path === tree.path;
    const warningCount = tree.file_info?.warnings?.length ?? 0;

    return (
        <div className="source-tree-node">
            <div
                className={`tree-item ${tree.type} ${isSelected ? 'selected' : ''}`}
                onClick={handleClick}
                style={{ paddingLeft: `${level * 20}px` }}
            >
                <span className="icon">
                    {tree.type === 'directory' ? (isExpanded ? '📂' : '📁') : 
                     tree.type === 'header' ? '📄' : '📝'}
                </span>
                <span className="name">{tree.name}</span>
                {warningCount > 0 && (
                    <span className="warning-count">⚠️ {warningCount}</span>
                )}
            </div>
            {isExpanded && tree.children && tree.children.length > 0 && (
                <div className="children">
                    {tree.children.map((child, index) => (
                        <SourceTree
                            key={`${child.path}-${index}`}
                            tree={child}
                            onFileSelect={onFileSelect}
                            selectedFile={selectedFile}
                            level={level + 1}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}; 