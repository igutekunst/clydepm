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