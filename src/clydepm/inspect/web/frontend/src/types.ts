export interface Position {
    x: number;
    y: number;
}

export interface DependencyNode {
    id: string;
    name: string;
    version: string;
    is_dev_dep: boolean;
    has_warnings: boolean;
    size: number;
    direct_deps: string[];
    all_deps: string[];
    position: Position;
    last_used: string;
    source_tree: SourceTree;
    include_paths: IncludePath[];
    build_metrics: BuildMetrics;
    compiler_config: Record<string, string>;
}

export interface DependencyEdge {
    id: string;
    source: string;
    target: string;
    is_circular: boolean;
}

export interface DependencyWarning {
    id: string;
    package: string;
    message: string;
    level: string;
    context: Record<string, string>;
}

export interface DependencyGraph {
    nodes: DependencyNode[];
    edges: DependencyEdge[];
    warnings: DependencyWarning[];
}

export interface BuildMetrics {
    total_time: number;
    cache_hits: number;
    cache_misses: number;
    artifact_sizes: Record<string, number>;
    memory_usage: number;
    cpu_usage: number;
    timestamp: string;
    files_compiled: number;
    total_warnings: number;
    total_errors: number;
}

export enum IncludePathType {
    SYSTEM = "system",
    PUBLIC = "public",
    PRIVATE = "private",
    DEPENDENCY = "dependency"
}

export interface IncludePath {
    path: string;
    type: 'system' | 'user' | 'dependency';
    from_package?: string;
}

export interface CompilerCommand {
    command_line: string;
    duration_ms: number;
    cache_hit: boolean;
    flags: string[];
    include_paths: IncludePath[];
    defines?: Record<string, string | null>;
}

export interface BuildWarning {
    location: string;
    message: string;
}

export interface SourceFile {
    path: string;
    type: 'source' | 'header';
    size: number;
    compiler_command?: CompilerCommand;
    warnings?: BuildWarning[];
    included_by?: string[];
    includes?: string[];
}

export interface SourceTree {
    name: string;
    path: string;
    type: 'directory' | 'source' | 'header';
    children?: SourceTree[];
    file_info?: SourceFile;
}

export interface GraphSettings {
    zoom: {
        initial: number;
        min: number;
        max: number;
    };
    layout: {
        width: number;
        height: number;
        nodeSpacing: number;
        rankSpacing: number;
    };
    physics: {
        enabled: boolean;
        stabilization: boolean;
        repulsion: {
            nodeDistance: number;
        };
    };
} 