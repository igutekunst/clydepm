"""
GitHub-based package registry implementation.
"""
from pathlib import Path
from typing import Dict, List, Optional, Union
import json
import tempfile
import shutil
import logging
import git
import os
import tarfile

from github import Github, Repository, GitRelease
from github.GithubException import GithubException
from semantic_version import Version
from rich import print as rprint

from ..core.package import Package, BuildMetadata, CompilerInfo

logger = logging.getLogger(__name__)

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
        logger.debug("Initializing GitHubRegistry with org=%s", organization)
        self.github = Github(token)
        self.org = organization
        self.cache_dir = Path(cache_dir or tempfile.gettempdir()) / "clydepm"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.debug("Using cache directory: %s", self.cache_dir)
        
    def create_repo(self, package_name: str, private: bool = False) -> Repository.Repository:
        """Create a new GitHub repository for the package.
        
        Args:
            package_name: Name of the package/repository
            private: Whether the repository should be private
            
        Returns:
            The created GitHub repository
            
        Raises:
            ValueError: If repository creation fails
        """
        try:
            logger.debug("Creating repository %s (private=%s)", package_name, private)
            if self.org:
                org = self.github.get_organization(self.org)
                return org.create_repo(
                    name=package_name,
                    private=private,
                    auto_init=False  # Don't initialize with README since we'll push existing code
                )
            else:
                return self.github.get_user().create_repo(
                    name=package_name,
                    private=private,
                    auto_init=False
                )
        except GithubException as e:
            logger.error("Failed to create repository %s: %s", package_name, e)
            raise ValueError(f"Failed to create repository {package_name}: {e}")

    def _get_repo(self, package_name: str) -> Repository.Repository:
        """Get GitHub repository for package, creating it if it doesn't exist.
        Also ensures local git remote is configured correctly.
        """
        try:
            # First try to get existing repo
            logger.debug("Getting repository for package %s", package_name)
            
            # Try both org and user contexts to find the repo
            repo = None
            if self.org:
                try:
                    repo = self.github.get_organization(self.org).get_repo(package_name)
                    logger.debug("Found repository in organization %s", self.org)
                except GithubException as e:
                    if e.status != 404:  # Only ignore 404 Not Found
                        raise
                
            if not repo:
                try:
                    repo = self.github.get_user().get_repo(package_name)
                    logger.debug("Found repository in user account")
                except GithubException as e:
                    if e.status != 404:  # Only ignore 404 Not Found
                        raise
                
            # If repo still not found, create it
            if not repo:
                logger.info("Repository %s not found, will create it", package_name)
                repo = self.create_repo(package_name)
            
            # Check local git repo and remote
            try:
                git_repo = git.Repo(os.getcwd())
                
                # Check if remote exists
                try:
                    origin = git_repo.remote("origin")
                    current_url = origin.url
                    
                    # Construct expected SSH URL
                    if self.org:
                        expected_url = f"git@github.com:{self.org}/{package_name}.git"
                    else:
                        expected_url = f"git@github.com:{repo.owner.login}/{package_name}.git"
                        
                    if current_url != expected_url:
                        logger.info("Updating remote URL from %s to %s", current_url, expected_url)
                        origin.set_url(expected_url)
                except ValueError:
                    # Remote doesn't exist, create it
                    logger.info("Creating origin remote")
                    if self.org:
                        url = f"git@github.com:{self.org}/{package_name}.git"
                    else:
                        url = f"git@github.com:{repo.owner.login}/{package_name}.git"
                    git_repo.create_remote("origin", url)
                
            except git.InvalidGitRepositoryError:
                logger.warning("Not in a git repository, skipping remote setup")
            
            return repo
        
        except GithubException as e:
            logger.error("Failed to get/create repository %s: %s", package_name, e)
            raise ValueError(f"Failed to access repository {package_name}: {e}")
            
    def _get_release(
        self,
        repo: Repository.Repository,
        version: str
    ) -> GitRelease.GitRelease:
        """Get GitHub release for package version."""
        try:
            logger.debug("Getting release v%s for repo %s", version, repo.full_name)
            return repo.get_release(f"v{version}")
        except GithubException as e:
            logger.error("Failed to get release v%s: %s", version, e)
            raise ValueError(f"Version {version} not found: {e}")
            
    def _download_asset(
        self,
        release: GitRelease.GitRelease,
        asset_name: str,
        dest_path: Path
    ) -> None:
        """Download release asset to destination path."""
        logger.debug("Downloading asset %s from release %s", asset_name, release.tag_name)
        for asset in release.get_assets():
            if asset.name == asset_name:
                with tempfile.NamedTemporaryFile() as tmp:
                    logger.debug("Downloading to temp file %s", tmp.name)
                    asset.download(tmp.name)
                    shutil.copy2(tmp.name, dest_path)
                logger.debug("Successfully downloaded asset to %s", dest_path)
                return
        logger.error("Asset %s not found in release %s", asset_name, release.tag_name)
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
        logger.debug("Getting package %s version %s", name, version)
        repo = self._get_repo(name)
        release = self._get_release(repo, version)
        
        # Try to find matching binary if build metadata provided
        if build_metadata:
            metadata_hash = build_metadata.get_hash()
            logger.debug("Trying to find binary package with hash %s", metadata_hash)
            try:
                # Download binary package
                binary_path = self.cache_dir / f"{name}-{version}-{metadata_hash}.tar.gz"
                self._download_asset(
                    release,
                    f"{name}-{version}-{metadata_hash}.tar.gz",
                    binary_path
                )
                logger.debug("Found and downloaded matching binary package")
                return Package(binary_path, form="binary")
            except ValueError:
                logger.debug("No matching binary found, falling back to source")
                # No matching binary found, fall back to source
                pass
                
        # Download source package
        source_path = self.cache_dir / f"{name}-{version}.tar.gz"
        logger.debug("Downloading source package to %s", source_path)
        self._download_asset(release, f"{name}-{version}.tar.gz", source_path)
        return Package(source_path)
    
    def publish_package(
        self,
        package: Package,
        create_binary: bool = True,
        push: bool = True
    ) -> None:
        """
        Publish package to registry.
        
        Args:
            package: Package to publish
            create_binary: Whether to create and publish binary package
            push: Whether to push changes to remote
            
        Creates a new release with source package and optionally binary package.
        """
        logger.debug("Publishing package %s version %s", package.name, package.version)
        repo = self._get_repo(package.name)

        # Check if release already exists
        try:
            existing_release = repo.get_release(f"v{package.version}")
            logger.error("Version %s already exists", package.version)
            raise ValueError(
                f"\n[red]Error: Version {package.version} already exists[/red]\n\n"
                f"To publish a new version:\n"
                f"1. Update the version in [bold]package.yml[/bold]:\n"
                f"   version: {package.version}\n"
                f"2. Commit and tag the changes:\n"
                f"   git commit -am 'Release {package.version}'\n"
                f"   git tag v{package.version}\n"
                f"3. Push to GitHub:\n"
                f"   git push origin main --tags\n"
                f"4. Publish the package:\n"
                f"   clyde publish\n"
                f"The existing release can be found at: {existing_release.html_url}"
            )
        except GithubException as e:
            if e.status != 404:  # Only ignore 404 Not Found
                raise ValueError(f"Failed to check existing release: {e}")

        # Create source tarball
        with tempfile.TemporaryDirectory() as temp_dir:
            tarball_path = Path(temp_dir) / f"{package.name}-{package.version}.tar.gz"
            logger.debug("Creating source tarball at %s", tarball_path)
            
            # Create tarball excluding .git, __pycache__, etc.
            with tarfile.open(tarball_path, "w:gz") as tar:
                def filter_func(tarinfo):
                    # Skip common files/dirs we don't want to include
                    name = tarinfo.name
                    excludes = ['.git', '__pycache__', '*.pyc', '.DS_Store', '.venv', 'venv']
                    for exclude in excludes:
                        if exclude.startswith('*'):
                            if name.endswith(exclude[1:]):
                                return None
                        elif exclude in name.split('/'):
                            return None
                    return tarinfo
                
                tar.add(package.path, arcname=package.name, filter=filter_func)
        
            try:
                # Create release
                logger.debug("Creating release v%s", package.version)
                release = repo.create_git_release(
                    f"v{package.version}",
                    f"Release {package.version}",
                    f"Release {package.version} of {package.name}"
                )
                
                # Upload source package
                logger.debug("Uploading source package %s", tarball_path)
                release.upload_asset(
                    str(tarball_path),
                    f"{package.name}-{package.version}.tar.gz",
                    "application/gzip"
                )
                
                # Create and upload binary if requested
                if create_binary and package.form == "source":
                    logger.debug("Creating binary package")
                    binary_path = self._create_binary(package)
                    if binary_path:
                        logger.debug("Uploading binary package %s", binary_path)
                        release.upload_asset(
                            str(binary_path),
                            f"{package.name}-{package.version}-{package.build_metadata.get_hash()}.tar.gz",
                            "application/gzip"
                        )
            except GithubException as e:
                if "already_exists" in str(e):
                    logger.error("Version %s already exists", package.version)
                    raise ValueError(
                        f"\n[red]Error: Version {package.version} already exists[/red]\n\n"
                        f"To publish a new version:\n"
                        f"1. Update the version in [bold]package.yml[/bold]:\n"
                        f"   version: {package.version}\n"
                        f"2. Commit and tag the changes:\n"
                        f"   git commit -am 'Release {package.version}'\n"
                        f"   git tag v{package.version}\n"
                        f"3. Push to GitHub:\n"
                        f"   git push origin main --tags\n"
                        f"4. Publish the package:\n"
                        f"   clyde publish\n"
                        f"The existing release can be found at: {repo.html_url}/releases/tag/v{package.version}"
                    )
                raise ValueError(f"Failed to create release: {e}")
    
    def _create_binary(self, package: Package) -> Optional[Path]:
        """Create binary package from source package."""
        # TODO: Implement binary package creation
        logger.debug("Binary package creation not yet implemented")
        return None
    
    def get_versions(self, name: str) -> List[Version]:
        """Get available versions for package."""
        logger.debug("Getting versions for package %s", name)
        repo = self._get_repo(name)
        versions = []
        for release in repo.get_releases():
            if release.tag_name.startswith("v"):
                try:
                    versions.append(Version(release.tag_name[1:]))
                except ValueError:
                    logger.warning("Invalid version tag: %s", release.tag_name)
                    continue
        logger.debug("Found versions: %s", versions)
        return sorted(versions)

    def _print_publish_instructions(self, package: Package) -> None:
        """Print instructions for publishing a package."""
        rprint("\nTo publish a new version:\n")
        return sorted(versions) 