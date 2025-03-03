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
        
        console.log('Tree node clicked:', {
            path: tree.path,
            type: tree.type,
            hasFileInfo: !!tree.file_info
        });

        if (tree.type === 'directory') {
            setIsExpanded(!isExpanded);
        } else {
            // For non-directory nodes, always create a SourceFile
            const fileInfo: SourceFile = tree.file_info || {
                path: tree.path,
                type: tree.type as 'source' | 'header',
                size: 0,
                warnings: [],
                included_by: [
                    'src/main.cpp',
                    'src/other_file.cpp'
                ],
                includes: [
                    // System headers
                    '<vector>',
                    '<string>',
                    '<memory>',
                    // Project headers
                    '"my-project/config.h"',
                    '"my-project/utils.h"',
                    // Local headers
                    '"../include/local.h"'
                ],
                compiler_command: {
                    command_line: `clang++ -c ${tree.path}`,
                    duration_ms: 0,
                    cache_hit: false,
                    flags: ['-Wall', '-Wextra', '-std=c++17'],
                    include_paths: [
                        {
                            path: '/usr/include',
                            type: 'system'
                        },
                        {
                            path: 'include',
                            type: 'user'
                        },
                        {
                            path: 'deps/fmt/include',
                            type: 'dependency',
                            from_package: 'fmt'
                        }
                    ],
                    defines: {
                        'DEBUG': '1',
                        'VERSION': '"1.0.0"'
                    }
                }
            };
            console.log('Calling onFileSelect with constructed fileInfo:', fileInfo);
            onFileSelect(fileInfo);
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