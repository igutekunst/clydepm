import { useState, useEffect } from 'react';
import { fetchPackageDetails } from '../api/client';
import type { DependencyNode } from '../types';

interface UseDependencyDetailsResult {
    details: DependencyNode | null;
    isLoading: boolean;
    error: Error | null;
}

export function useDependencyDetails(packageId: string | null): UseDependencyDetailsResult {
    const [details, setDetails] = useState<DependencyNode | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<Error | null>(null);

    useEffect(() => {
        if (!packageId) {
            setDetails(null);
            return;
        }

        setIsLoading(true);
        setError(null);

        fetchPackageDetails(packageId)
            .then((data) => {
                setDetails(data);
                setIsLoading(false);
            })
            .catch((err) => {
                console.error('Failed to fetch package details:', err);
                setError(err);
                setIsLoading(false);
            });
    }, [packageId]);

    return { details, isLoading, error };
} 