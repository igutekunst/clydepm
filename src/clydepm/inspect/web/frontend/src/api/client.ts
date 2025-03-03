import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Position {
  x: number;
  y: number;
}

export interface DependencyWarning {
  id: string;
  package: string;
  message: string;
  level: string;
  context: Record<string, string>;
}

export interface DependencyNode {
  id: string;
  name: string;
  version: string;
  is_dev_dep: boolean;
  has_warnings: boolean;
  warnings?: DependencyWarning[];  // Optional array of warnings
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

export interface BuildMetrics {
  total_time: number;
  cache_hits: number;
  cache_misses: number;
  artifact_sizes: Record<string, number>;
  memory_usage: number;
  cpu_usage: number;
  timestamp: string;
}

export interface GraphLayout {
  nodes: DependencyNode[];
  edges: DependencyEdge[];
  warnings: DependencyWarning[];
}

export const getDependencyGraph = async (): Promise<GraphLayout> => {
  const response = await api.get<GraphLayout>('/dependencies');
  return response.data;
};

export const getPackageDetails = async (packageName: string): Promise<DependencyNode> => {
  const response = await api.get<DependencyNode>(`/dependencies/${packageName}`);
  return response.data;
};

export const getBuildMetrics = async (): Promise<BuildMetrics> => {
  const response = await api.get<BuildMetrics>('/metrics');
  return response.data;
}; 