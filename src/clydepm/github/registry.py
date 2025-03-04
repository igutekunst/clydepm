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
from ..core.version.version import Version
from rich import print as rprint
from rich.console import Console

from ..core.package import Package, BuildMetadata, CompilerInfo

logger = logging.getLogger(__name__)
console = Console()

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
        """Get package from GitHub.
        
        Args:
            name: Package name
            version: Package version or "latest"
            
        Returns:
            Package instance
            
        Raises:
            ValueError: If package or version not found
        """
        try:
            # First try to find a release
            releases_url = f"https://api.github.com/repos/{self.organization}/{name}/releases"
            response = self.session.get(releases_url)
            
            selected_release = None
            tarball_url = None
            
            if response.status_code == 200:
                releases = response.json()
                if releases:
                    if version == "latest":
                        # Get latest release
                        selected_release = releases[0]
                        version = selected_release["tag_name"].lstrip("v")
                        console.print(f"✓ Found matching tag: [green]{version}[/green]")
                        logger.debug(f"Using latest release: {version}")
                        tarball_url = selected_release["tarball_url"]
                    else:
                        # Find specific version
                        for release in releases:
                            if release["tag_name"].lstrip("v") == version:
                                selected_release = release
                                tarball_url = release["tarball_url"]
                                break
                        if not selected_release:
                            logger.debug("[dim]No matching release found, checking tags...[/dim]")

            # If no release found, try tags
            if not selected_release:
                tags_url = f"https://api.github.com/repos/{self.organization}/{name}/tags"
                response = self.session.get(tags_url)
                
                if response.status_code != 200:
                    raise ValueError(f"Failed to get versions for {name}: {response.text}")
                    
                tags = response.json()
                
                if tags:
                    tag_names = [t['name'] for t in tags]
                    logger.debug(f"Available tags: {', '.join(tag_names)}")
                    if version == "latest":
                        # Use first tag (most recent)
                        tag = tags[0]
                        version = tag["name"].lstrip("v")
                        console.print(f"✓ Found matching tag: [green]{version}[/green]")
                        logger.debug(f"Using latest tag: {version}")
                        tarball_url = f"https://api.github.com/repos/{self.organization}/{name}/tarball/{tag['name']}"
                    else:
                        # Find matching tag
                        for tag in tags:
                            if tag["name"].lstrip("v") == version:
                                console.print(f"✓ Found matching tag: [green]{tag['name']}[/green]")
                                logger.debug(f"Found matching tag: {tag['name']}")
                                tarball_url = f"https://api.github.com/repos/{self.organization}/{name}/tarball/{tag['name']}"
                                break
                        else:
                            raise ValueError(f"Version {version} not found in tags")
                elif version == "latest":
                    # No tags, fall back to main branch
                    logger.debug("[dim]No tags found, using main branch[/dim]")
                    tarball_url = f"https://api.github.com/repos/{self.organization}/{name}/tarball/main"
                    version = "main"
                else:
                    raise ValueError(f"No versions found for package {name}")

            if not tarball_url:
                raise ValueError(f"Could not find version {version} for package {name}")
            
            # Create package directory under ~/.clydepm/sources
            sources_dir = Path.home() / ".clydepm" / "sources" / self.organization / name / version
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
        except Exception as e:
            logger.error("Failed to get package: %s", e)
            raise ValueError(f"Failed to get package {name}@{version}: {e}")

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

    def _get_repo(self, package_name: str) -> Dict:
        """Get GitHub repository for package, creating it if it doesn't exist.
        Also ensures local git remote is configured correctly.
        """
        try:
            # First try to get existing repo
            logger.debug("Getting repository for package %s", package_name)
            
            # Try both org and user contexts to find the repo
            repo = None
            
            # If organization is specified, try that first
            if self.organization:
                response = self.session.get(f"https://api.github.com/repos/{self.organization}/{package_name}")
                if response.status_code == 200:
                    repo = response.json()
                    logger.debug("Found repository in organization %s", self.organization)
            
            # If no org or repo not found in org, try user's repos
            if not repo:
                # First get the authenticated user
                user_response = self.session.get("https://api.github.com/user")
                if user_response.status_code != 200:
                    raise ValueError("Failed to get authenticated user. Please check your GitHub token.")
                
                user = user_response.json()
                username = user['login']
                
                # Try to find repo in user's account
                response = self.session.get(f"https://api.github.com/repos/{username}/{package_name}")
                if response.status_code == 200:
                    repo = response.json()
                    # If no organization was specified, use the username
                    if not self.organization:
                        self.organization = username
                    logger.debug("Found repository in user account")
                
            # If repo still not found, create it
            if not repo:
                logger.warning("Repository %s not found, will create it", package_name)
                # Create in organization if specified, otherwise in user account
                if self.organization:
                    create_url = f"https://api.github.com/orgs/{self.organization}/repos"
                else:
                    create_url = "https://api.github.com/user/repos"
                    
                create_data = {
                    "name": package_name,
                    "private": False,
                    "auto_init": False
                }
                
                response = self.session.post(create_url, json=create_data)
                if response.status_code != 201:
                    raise ValueError(f"Failed to create repository: {response.text}")
                
                repo = response.json()
                if not self.organization:
                    self.organization = repo['owner']['login']
            
            # Check local git repo and remote
            try:
                git_repo = git.Repo(os.getcwd())
                
                # Check if remote exists
                try:
                    origin = git_repo.remote("origin")
                    current_url = origin.url
                    
                    # Construct expected SSH URL
                    expected_url = f"git@github.com:{self.organization}/{package_name}.git"
                        
                    if current_url != expected_url:
                        logger.info("Updating remote URL from %s to %s", current_url, expected_url)
                        origin.set_url(expected_url)
                except ValueError:
                    # Remote doesn't exist, create it
                    logger.info("Creating origin remote")
                    url = f"git@github.com:{self.organization}/{package_name}.git"
                    git_repo.create_remote("origin", url)
                
            except git.InvalidGitRepositoryError:
                logger.warning("Not in a git repository, skipping remote setup")
            
            return repo
        
        except Exception as e:
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
        
        # Get repo will ensure we have the correct organization
        repo = self._get_repo(package.name)
        owner = repo['owner']['login']

        # Check if release already exists
        try:
            response = self.session.get(f"https://api.github.com/repos/{owner}/{package.name}/releases/tags/v{package.version}")
            if response.status_code == 200:
                existing_release = response.json()
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
                    f"The existing release can be found at: {existing_release['html_url']}"
                )
        except requests.exceptions.RequestException as e:
            if e.response and e.response.status_code != 404:
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
                # Create release using GitHub API
                logger.debug("Creating release v%s", package.version)
                release_data = {
                    "tag_name": f"v{package.version}",
                    "name": f"Release {package.version}",
                    "body": f"Release {package.version} of {package.name}",
                    "draft": False,
                    "prerelease": False
                }
                response = self.session.post(
                    f"https://api.github.com/repos/{owner}/{package.name}/releases",
                    json=release_data
                )
                response.raise_for_status()
                release = response.json()
                
                # Upload source package
                logger.debug("Uploading source package %s", tarball_path)
                with open(tarball_path, "rb") as f:
                    files = {
                        "file": (f"{package.name}-{package.version}.tar.gz", f, "application/gzip")
                    }
                    response = self.session.post(
                        release["upload_url"].replace("{?name,label}", ""),
                        files=files,
                        params={"name": f"{package.name}-{package.version}.tar.gz"}
                    )
                    response.raise_for_status()
                
                # Create and upload binary if requested
                if create_binary and package.form == "source":
                    logger.debug("Creating binary package")
                    binary_path = self._create_binary(package)
                    if binary_path:
                        logger.debug("Uploading binary package %s", binary_path)
                        with open(binary_path, "rb") as f:
                            files = {
                                "file": (
                                    f"{package.name}-{package.version}-{package.build_metadata.get_hash()}.tar.gz",
                                    f,
                                    "application/gzip"
                                )
                            }
                            response = self.session.post(
                                release["upload_url"].replace("{?name,label}", ""),
                                files=files,
                                params={
                                    "name": f"{package.name}-{package.version}-{package.build_metadata.get_hash()}.tar.gz"
                                }
                            )
                            response.raise_for_status()
                            
                logger.info("Successfully published %s version %s", package.name, package.version)
                console.print(f"\n[green]✓[/green] Published {package.name} {package.version}")
                
            except requests.exceptions.RequestException as e:
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
        try:
            repo = self._get_repo(name)
            versions = []
            for release in repo.get_releases():
                try:
                    # Strip 'v' prefix if present and parse as Version
                    version_str = release.tag_name.lstrip("v")
                    versions.append(Version.parse(version_str))
                except ValueError:
                    logger.warning("Invalid version tag: %s", release.tag_name)
                    continue
            logger.debug("Found versions: %s", versions)
            return sorted(versions)  # Version class implements proper comparison
        except Exception as e:
            logger.error("Failed to get versions: %s", e)
            return []

    def _print_publish_instructions(self, package: Package) -> None:
        """Print instructions for publishing a package."""
        rprint("\nTo publish a new version:\n")
        return sorted(versions) 