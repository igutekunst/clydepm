import React, { useState } from 'react';
import type { SourceTree as SourceTreeType, SourceFile } from '../types';
import { fetchFileInfo } from '../api/client';

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
    const [isLoading, setIsLoading] = useState(false);

    const handleClick = async (e: React.MouseEvent) => {
        e.stopPropagation();
        
        console.log('Tree node clicked:', {
            path: tree.path,
            type: tree.type,
            hasFileInfo: !!tree.file_info
        });

        if (tree.type === 'directory') {
            setIsExpanded(!isExpanded);
        } else {
            try {
                setIsLoading(true);
                const fileInfo = await fetchFileInfo(tree.path);
                onFileSelect(fileInfo);
            } catch (error) {
                console.error('Failed to fetch file info:', error);
                // You might want to show an error message to the user
            } finally {
                setIsLoading(false);
            }
        }
    };

    const isSelected = selectedFile?.path === tree.path;

    return (
        <div className="source-tree-node">
            <div
                className={`tree-item ${tree.type} ${isSelected ? 'selected' : ''} ${isLoading ? 'loading' : ''}`}
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
                {isLoading && <span className="loading-indicator">⌛</span>}
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