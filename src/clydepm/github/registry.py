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
import requests
import base64
import io

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
    def __init__(self, token: str, organization: str):
        self.token = token
        self.organization = organization
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        })
        
    def get_package(self, name: str, version: str = "latest") -> Package:
        """Get a package from the registry.
        
        Args:
            name: Package name
            version: Package version or "latest"
            
        Returns:
            Package instance
            
        Raises:
            ValueError: If package or version not found
        """
        if not name:
            raise ValueError("Package name cannot be empty")
            
        if not self.organization:
            raise ValueError("No organization specified. Use --org option or configure default organization")
            
        logger.debug(f"Looking up package {name} in {self.organization}")
        
        # First check if repository exists
        repo_url = f"https://api.github.com/repos/{self.organization}/{name}"
        response = self.session.get(repo_url)
        
        if response.status_code == 404:
            raise ValueError(f"Package {name} not found in {self.organization}")
        elif response.status_code != 200:
            raise ValueError(f"Failed to lookup package {name}: {response.text}")
            
        # First try to find a release
        releases_url = f"https://api.github.com/repos/{self.organization}/{name}/releases"
        response = self.session.get(releases_url)
        
        if response.status_code == 200:
            releases = response.json()
            selected_release = None
            
            if releases:
                release_tags = [r['tag_name'] for r in releases]
                logger.debug(f"Found releases: {release_tags}")
                if version == "latest":
                    # Use latest release
                    selected_release = releases[0]
                    version = selected_release["tag_name"].lstrip("v")
                    logger.info(f"Using latest release: {version}")
                else:
                    # Find matching release
                    for release in releases:
                        if release["tag_name"].lstrip("v") == version:
                            selected_release = release
                            logger.info(f"Found matching release: {release['tag_name']}")
                            break
                            
            if selected_release:
                # Download release tarball
                tarball_url = selected_release["tarball_url"]
                logger.debug(f"Using release tarball: {tarball_url}")
            else:
                logger.info("No matching release found, falling back to tags")
                
        # If no release found, try tags
        if not selected_release:
            tags_url = f"https://api.github.com/repos/{self.organization}/{name}/tags"
            response = self.session.get(tags_url)
            
            if response.status_code != 200:
                raise ValueError(f"Failed to get versions for {name}: {response.text}")
                
            tags = response.json()
            
            if tags:
                tag_names = [t['name'] for t in tags]
                logger.info(f"Found tags: {tag_names}")
                if version == "latest":
                    # Use first tag (most recent)
                    tag = tags[0]
                    version = tag["name"].lstrip("v")
                    logger.info(f"Using latest tag: {version}")
                    tarball_url = f"https://api.github.com/repos/{self.organization}/{name}/tarball/{tag['name']}"
                else:
                    # Find matching tag
                    for tag in tags:
                        if tag["name"].lstrip("v") == version:
                            logger.info(f"Found matching tag: {tag['name']}")
                            tarball_url = f"https://api.github.com/repos/{self.organization}/{name}/tarball/{tag['name']}"
                            break
                    else:
                        raise ValueError(f"Version {version} not found in tags")
            elif version == "latest":
                # No tags, fall back to main branch
                logger.info("No tags found, falling back to main branch")
                tarball_url = f"https://api.github.com/repos/{self.organization}/{name}/tarball/main"
                version = "main"
            else:
                raise ValueError(f"No versions found for package {name}")
                
        # Create package directory under ~/.clyde/sources
        sources_dir = Path.home() / ".clyde" / "sources" / self.organization / name / version
        sources_dir.mkdir(parents=True, exist_ok=True)
        
        # Download source code if not already downloaded
        package_yml = sources_dir / "package.yml"
        if not package_yml.exists():
            logger.debug(f"Downloading source from: {tarball_url}")
            response = self.session.get(tarball_url)
            
            if response.status_code != 200:
                raise ValueError(f"Failed to download source code for {name}@{version}")
                
            # Extract archive
            with tarfile.open(fileobj=io.BytesIO(response.content), mode="r:gz") as tar:
                # Get the root directory name from the archive
                root_dir = tar.getnames()[0]
                logger.debug(f"Extracting from tarball root: {root_dir}")
                
                # First find and extract package.yml
                package_yml_locations = [
                    "package.yml",
                    f"{name}/package.yml",
                    "src/package.yml",
                    f"src/{name}/package.yml"
                ]
                
                package_yml_found = False
                for member in tar.getmembers():
                    for location in package_yml_locations:
                        full_path = f"{root_dir}/{location}"
                        if member.name == full_path:
                            logger.debug(f"Found package.yml at {location} in tarball")
                            # Extract package.yml to root of sources dir
                            member.name = "package.yml"
                            tar.extract(member, sources_dir)
                            package_yml_found = True
                            break
                    if package_yml_found:
                        break
                        
                if not package_yml_found:
                    raise ValueError(
                        f"No package.yml found in {version} of {self.organization}/{name}. "
                        "This version may not be properly packaged for Clyde. "
                        "Make sure package.yml is included in releases/tags."
                    )
                
                # Now extract everything else
                for member in tar.getmembers():
                    if member.name == f"{root_dir}/package.yml":
                        continue
                    # Remove root directory from path
                    member.name = member.name.replace(f"{root_dir}/", "", 1)
                    tar.extract(member, sources_dir)
                    
        # Create package instance from sources directory
        return Package(sources_dir)

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
            if self.organization:
                org = self.session.get(f"https://api.github.com/orgs/{self.organization}").json()
                return org.create_repo(
                    name=package_name,
                    private=private,
                    auto_init=False  # Don't initialize with README since we'll push existing code
                )
            else:
                return self.session.get(f"https://api.github.com/user/repos").json()[0].create_repo(
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
            if self.organization:
                try:
                    repo = self.session.get(f"https://api.github.com/repos/{self.organization}/{package_name}").json()
                    logger.debug("Found repository in organization %s", self.organization)
                except GithubException as e:
                    if e.status != 404:  # Only ignore 404 Not Found
                        raise
                
            if not repo:
                try:
                    repo = self.session.get(f"https://api.github.com/user/repos").json()[0]
                    logger.debug("Found repository in user account")
                except GithubException as e:
                    if e.status != 404:  # Only ignore 404 Not Found
                        raise
                
            # If repo still not found, create it
            if not repo:
                logger.warning("Repository %s not found, will create it", package_name)
                repo = self.create_repo(package_name)
            
            # Check local git repo and remote
            try:
                git_repo = git.Repo(os.getcwd())
                
                # Check if remote exists
                try:
                    origin = git_repo.remote("origin")
                    current_url = origin.url
                    
                    # Construct expected SSH URL
                    if self.organization:
                        expected_url = f"git@github.com:{self.organization}/{package_name}.git"
                    else:
                        expected_url = f"git@github.com:{repo['owner']['login']}/{package_name}.git"
                        
                    if current_url != expected_url:
                        logger.info("Updating remote URL from %s to %s", current_url, expected_url)
                        origin.set_url(expected_url)
                except ValueError:
                    # Remote doesn't exist, create it
                    logger.info("Creating origin remote")
                    if self.organization:
                        url = f"git@github.com:{self.organization}/{package_name}.git"
                    else:
                        url = f"git@github.com:{repo['owner']['login']}/{package_name}.git"
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
            logger.debug("Getting release v%s for repo %s", version, repo['full_name'])
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
        logger.debug("Downloading asset %s from release %s", asset_name, release['tag_name'])
        for asset in release.get_assets():
            if asset.name == asset_name:
                with tempfile.NamedTemporaryFile() as tmp:
                    logger.debug("Downloading to temp file %s", tmp.name)
                    asset.download(tmp.name)
                    shutil.copy2(tmp.name, dest_path)
                logger.debug("Successfully downloaded asset to %s", dest_path)
                return
        logger.error("Asset %s not found in release %s", asset_name, release['tag_name'])
        raise ValueError(f"Asset {asset_name} not found in release")
    
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
                        f"The existing release can be found at: {repo['html_url']}/releases/tag/v{package.version}"
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