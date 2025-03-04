export interface Position {
    x: number;
    y: number;
}

export interface PackageIdentifier {
    name: string;
    organization?: string;
}

export interface DependencyNode {
    id: string;
    package: PackageIdentifier;
    name: string;
    version: string;
    type: 'runtime' | 'dev';
    position: Position;
    metrics: BuildMetrics | null;
    has_warnings: boolean;
}

export interface DependencyEdge {
    id: string;
    source: string;
    target: string;
    type: 'runtime' | 'dev';
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
    content?: string;
    warnings?: string[];
    errors?: string[];
}

export interface SourceTree {
    name: string;
    path: string;
    type: 'directory' | 'source' | 'header';
    children?: SourceTree[];
    file_info?: {
        warnings?: string[];
        errors?: string[];
    } | null;
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

export interface CompilationStep {
    source_file: string;
    object_file: string;
    command: string[];
    include_paths: string[];
    start_time: string;
    end_time?: string;
    success: boolean;
    error?: string;
}

export interface BuildData {
    id: string;
    package: {
        name: string;
        organization: string | null;
    };
    version: string;
    timestamp: string;
    status: 'success' | 'failure' | 'in_progress';
    compiler_info: {
        name: string;
        version: string;
        target: string;
    };
    resolved_dependencies: Array<{
        package: {
            name: string;
            organization: string | null;
        };
        version: string;
        type: string;
        source_tree: SourceTree;
        include_paths: string[];
    }>;
    compilation_steps: Array<{
        source_file: string;
        object_file: string;
        command: string[];
        include_paths: string[];
        start_time: string;
        end_time?: string;
        success: boolean;
        error?: string;
    }>;
    include_paths: string[];
    library_paths: string[];
    metrics: {
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
    } | null;
    error: string | null;
} 