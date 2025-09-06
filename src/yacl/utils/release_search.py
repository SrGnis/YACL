"""
Release Search for YACL

This module provides simple tag-based searching functionality for game releases.
"""

import logging
from typing import List, Optional

from yacl.models.release import GameRelease


class ReleaseSearchIndex:
    """
    Simple search index for game releases that searches by tag names.

    This class provides:
    - Fast tag-based searching
    - Case-insensitive partial matching
    - Simple and efficient implementation
    """

    def __init__(self):
        """Initialize the search index."""
        self.logger = logging.getLogger("YACL")

        # Store releases
        self.releases: List[GameRelease] = []

        self.logger.debug("Release search index initialized")
    
    def add_releases(self, releases: List[GameRelease]) -> None:
        """
        Add releases to the search index.

        Args:
            releases: List of releases to index
        """
        try:
            self.releases = releases.copy()
            self.logger.debug(f"Added {len(releases)} releases to search index")
        except Exception as e:
            self.logger.error(f"Error adding releases to index: {e}")

    def search(self, query: str) -> List[GameRelease]:
        """
        Search for releases by tag name containing the query.

        Args:
            query: Search query string

        Returns:
            List of releases with tags containing the query
        """
        try:
            if not query or not query.strip():
                # Return all releases if no query
                return self.releases.copy()

            # Normalize query (case-insensitive)
            normalized_query = query.strip().lower()

            # Find releases with tags containing the query
            matching_releases = []
            for release in self.releases:
                if release.tag_name:
                    normalized_tag = release.tag_name.lower()
                    if normalized_query in normalized_tag:
                        matching_releases.append(release)

            self.logger.debug(f"Search for '{query}' returned {len(matching_releases)} results")
            return matching_releases

        except Exception as e:
            self.logger.error(f"Error searching releases: {e}")
            return []

    def get_all_tags(self) -> List[str]:
        """
        Get all unique tags from indexed releases.

        Returns:
            List of unique tags
        """
        try:
            tags = set()
            for release in self.releases:
                if release.tag_name:
                    tags.add(release.tag_name)
            return sorted(list(tags))
        except Exception as e:
            self.logger.error(f"Error getting tags: {e}")
            return []
