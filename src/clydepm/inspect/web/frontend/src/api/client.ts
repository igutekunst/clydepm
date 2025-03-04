import { DependencyGraph, BuildMetrics, GraphSettings, BuildData } from '../types';
import type { SourceFile } from '../types';

const API_BASE = '/api';

export async function fetchDependencyGraph(): Promise<DependencyGraph> {
    const response = await fetch(`${API_BASE}/dependencies`);
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to fetch dependency graph: ${response.statusText}\n${errorText}`);
    }
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

export async function getLatestPackageBuild(packageName: string): Promise<BuildData | null> {
    if (!packageName) {
        console.warn('getLatestPackageBuild called with empty package name');
        return null;
    }

    try {
        const response = await fetch(`${API_BASE}/builds/${encodeURIComponent(packageName)}/latest`);
        if (!response.ok) {
            if (response.status === 404) {
                console.warn(`No latest build found for package ${packageName}`);
                return null;
            }
            const errorText = await response.text();
            throw new Error(`Failed to fetch latest build for package ${packageName}: ${response.statusText}\n${errorText}`);
        }
        const data = await response.json();
        if (!data || !data.id || !data.package?.name) {
            console.warn(`Invalid build data received for package ${packageName}:`, data);
            return null;
        }
        return data;
    } catch (error) {
        console.error(`Error fetching latest build for package ${packageName}:`, error);
        throw new Error(`Failed to fetch latest build for package ${packageName}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
} 