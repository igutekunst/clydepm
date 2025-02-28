"""
GitHub-based package registry implementation.
"""
from pathlib import Path
from typing import Dict, List, Optional, Union
import json
import tempfile
import shutil

from github import Github, Repository, GitRelease
from github.GithubException import GithubException
from semantic_version import Version

from ..core.package import Package, BuildMetadata, CompilerInfo


class GitHubRegistry:
    """
    GitHub-based package registry that handles both source and binary packages.
    Uses GitHub releases for versioning and GitHub Packages for binary storage.
    """
    def __init__(
        self,
        token: str,
        organization: Optional[str] = None,
        cache_dir: Optional[Path] = None
    ):
        self.github = Github(token)
        self.org = organization
        self.cache_dir = Path(cache_dir or tempfile.gettempdir()) / "clydepm"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_repo(self, package_name: str) -> Repository.Repository:
        """Get GitHub repository for package."""
        try:
            if self.org:
                return self.github.get_organization(self.org).get_repo(package_name)
            return self.github.get_repo(package_name)
        except GithubException as e:
            raise ValueError(f"Package {package_name} not found: {e}")
            
    def _get_release(
        self,
        repo: Repository.Repository,
        version: str
    ) -> GitRelease.GitRelease:
        """Get GitHub release for package version."""
        try:
            return repo.get_release(f"v{version}")
        except GithubException as e:
            raise ValueError(f"Version {version} not found: {e}")
            
    def _download_asset(
        self,
        release: GitRelease.GitRelease,
        asset_name: str,
        dest_path: Path
    ) -> None:
        """Download release asset to destination path."""
        for asset in release.get_assets():
            if asset.name == asset_name:
                with tempfile.NamedTemporaryFile() as tmp:
                    asset.download(tmp.name)
                    shutil.copy2(tmp.name, dest_path)
                return
        raise ValueError(f"Asset {asset_name} not found in release")
    
    def get_package(
        self,
        name: str,
        version: str,
        build_metadata: Optional[BuildMetadata] = None
    ) -> Package:
        """
        Get package from registry.
        
        Args:
            name: Package name
            version: Package version
            build_metadata: Optional build metadata to match binary package
            
        Returns:
            Package instance
            
        If build_metadata is provided, tries to find matching binary package.
        Falls back to source package if no matching binary is found.
        """
        repo = self._get_repo(name)
        release = self._get_release(repo, version)
        
        # Try to find matching binary if build metadata provided
        if build_metadata:
            metadata_hash = build_metadata.get_hash()
            try:
                # Download binary package
                binary_path = self.cache_dir / f"{name}-{version}-{metadata_hash}.tar.gz"
                self._download_asset(
                    release,
                    f"{name}-{version}-{metadata_hash}.tar.gz",
                    binary_path
                )
                return Package(binary_path, form="binary")
            except ValueError:
                # No matching binary found, fall back to source
                pass
                
        # Download source package
        source_path = self.cache_dir / f"{name}-{version}.tar.gz"
        self._download_asset(release, f"{name}-{version}.tar.gz", source_path)
        return Package(source_path)
    
    def publish_package(
        self,
        package: Package,
        create_binary: bool = True
    ) -> None:
        """
        Publish package to registry.
        
        Args:
            package: Package to publish
            create_binary: Whether to create and publish binary package
            
        Creates a new release with source package and optionally binary package.
        """
        repo = self._get_repo(package.name)
        
        # Create release
        release = repo.create_git_release(
            f"v{package.version}",
            f"Release {package.version}",
            f"Release {package.version} of {package.name}"
        )
        
        # Upload source package
        release.upload_asset(
            str(package.path),
            f"{package.name}-{package.version}.tar.gz",
            "application/gzip"
        )
        
        # Create and upload binary if requested
        if create_binary and package.form == "source":
            binary_path = self._create_binary(package)
            if binary_path:
                release.upload_asset(
                    str(binary_path),
                    f"{package.name}-{package.version}-{package.build_metadata.get_hash()}.tar.gz",
                    "application/gzip"
                )
                
    def _create_binary(self, package: Package) -> Optional[Path]:
        """Create binary package from source package."""
        # TODO: Implement binary package creation
        return None
    
    def get_versions(self, name: str) -> List[Version]:
        """Get available versions for package."""
        repo = self._get_repo(name)
        versions = []
        for release in repo.get_releases():
            if release.tag_name.startswith("v"):
                try:
                    versions.append(Version(release.tag_name[1:]))
                except ValueError:
                    continue
        return sorted(versions) 