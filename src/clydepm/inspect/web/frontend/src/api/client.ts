import { DependencyGraph, PackageDetails, BuildMetrics, GraphSettings, BuildData } from '../types';
import type { SourceFile } from '../types';

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

export async function fetchFileInfo(filePath: string): Promise<SourceFile> {
    const response = await fetch(`/api/file-info/${encodeURIComponent(filePath)}`);
    if (!response.ok) {
        throw new Error(`Failed to fetch file info: ${response.statusText}`);
    }
    return response.json();
}

export async function getAllBuilds(): Promise<BuildData[]> {
    const response = await fetch(`${API_BASE}/builds`);
    if (!response.ok) {
        throw new Error(`Failed to fetch builds: ${response.statusText}`);
    }
    return response.json();
}

export async function getPackageBuilds(packageName: string): Promise<BuildData[]> {
    const response = await fetch(`${API_BASE}/builds/${packageName}`);
    if (!response.ok) {
        throw new Error(`Failed to fetch builds for package ${packageName}: ${response.statusText}`);
    }
    return response.json();
}

export async function getLatestPackageBuild(packageName: string): Promise<BuildData> {
    const response = await fetch(`${API_BASE}/builds/${packageName}/latest`);
    if (!response.ok) {
        throw new Error(`Failed to fetch latest build for package ${packageName}: ${response.statusText}`);
    }
    return response.json();
} 