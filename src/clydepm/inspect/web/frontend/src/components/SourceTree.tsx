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
        } else if (tree.file_info) {
            onFileSelect(tree.file_info);
        }
    };

    const isSelected = selectedFile?.path === tree.path;

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
                {tree.file_info?.warnings?.length > 0 && (
                    <span className="warning-count">⚠️ {tree.file_info.warnings.length}</span>
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