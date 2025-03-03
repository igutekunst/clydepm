import { DependencyGraph, PackageDetails, BuildMetrics, GraphSettings } from '../types';

const API_BASE = '/api';

export async function fetchDependencyGraph(): Promise<DependencyGraph> {
    const response = await fetch(`${API_BASE}/dependencies`);
    if (!response.ok) throw new Error('Failed to fetch dependency graph');
    return response.json();
}

export async function fetchPackageDetails(packageId: string): Promise<PackageDetails> {
    const response = await fetch(`${API_BASE}/dependencies/${packageId}`);
    if (!response.ok) throw new Error('Failed to fetch package details');
    return response.json();
}

export async function fetchBuildMetrics(): Promise<BuildMetrics> {
    const response = await fetch(`${API_BASE}/metrics`);
    if (!response.ok) throw new Error('Failed to fetch build metrics');
    return response.json();
}

export async function fetchGraphSettings(): Promise<GraphSettings> {
    const response = await fetch(`${API_BASE}/graph-settings`);
    if (!response.ok) throw new Error('Failed to fetch graph settings');
    return response.json();
} 