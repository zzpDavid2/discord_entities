import logging
from pathlib import Path
from typing import Dict, Optional, List
from .ghost import Ghost

# Set up logging for this module
logger = logging.getLogger(__name__)


class GhostGroup:
    """A collection of entities that can be managed and operated on as a group"""

    def __init__(self, ghosts: Dict[str, Ghost] = None):
        """
        Initialize an entity group

        Args:
            ghosts: Dictionary mapping handles to Ghost instances
        """
        self.ghosts = ghosts or {}

    def __len__(self) -> int:
        """Return the number of entities in the group"""
        return len(self.ghosts)

    def __iter__(self):
        """Iterate over entity handles and instances"""
        return iter(self.ghosts.items())

    def __getitem__(self, handle: str) -> Ghost:
        """Get an entity by handle"""
        return self.ghosts[handle]

    def get(self, handle: str, default: Ghost = None) -> Optional[Ghost]:
        """Get an entity by handle with default fallback"""
        return self.ghosts.get(handle, default)

    def keys(self):
        """Return entity handles"""
        return self.ghosts.keys()

    def values(self):
        """Return entity instances"""
        return self.ghosts.values()

    def items(self):
        """Return handle, entity pairs"""
        return self.ghosts.items()

    def add_ghost(self, ghost: Ghost):
        """Add an entity to the group"""
        self.ghosts[ghost.handle] = ghost
        logger.info(f"✅ Added entity: {ghost.name} (handle: {ghost.handle}) to group")

    def remove_ghost(self, handle: str) -> Optional[Ghost]:
        """Remove an entity by handle"""
        ghost = self.ghosts.pop(handle, None)
        if ghost:
            logger.info(f"🗑️ Removed entity: {ghost.name} (handle: {handle}) from group")
        return ghost

    def find_ghost_by_mention(self, message_content: str) -> List[Ghost]:
        """Find all entities being mentioned in the message"""
        import re

        message_lower = message_content.lower()
        mentioned_ghosts = []

        # Check for pseudo-mentions like "@tomas", "@anna"
        pseudo_mention_pattern = r"@(\w+)"
        pseudo_mentions = re.findall(pseudo_mention_pattern, message_lower)
        pseudo_mentions = [mention.lower() for mention in pseudo_mentions]

        # Check if any handle appears in the message or pseudo-mentions
        for handle, ghost in self.ghosts.items():
            if (
                f"@{handle.lower()}" in message_lower
                or handle.lower() in pseudo_mentions
                and ghost not in mentioned_ghosts
            ):
                mentioned_ghosts.append(ghost)

        return mentioned_ghosts

    def _normalize_ghost_name(self, name: str) -> str:
        """
        Normalize an entity name by removing emojis and special characters

        Args:
            name: The entity name to normalize

        Returns:
            Normalized name with only letters, numbers, and spaces
        """
        import re

        # Remove emojis and special characters, keep letters, numbers, and spaces
        normalized = re.sub(r"[^\w\s]", "", name, flags=re.UNICODE)
        # Remove extra whitespace
        normalized = " ".join(normalized.split())
        return normalized.strip()

    def get_ghost_by_name(self, name: str) -> Optional[Ghost]:
        """
        Find an entity by their display name (case-insensitive)

        Args:
            name: The entity's display name

        Returns:
            Ghost instance if found, None otherwise
        """
        normalized_name = self._normalize_ghost_name(name).lower()

        for ghost in self.ghosts.values():
            if self._normalize_ghost_name(ghost.name).lower() == normalized_name:
                return ghost

        return None

    @classmethod
    def load_from_directory(
        cls, directory: str, ignore_errors: bool = True
    ) -> "GhostGroup":
        """
        Load all entity configurations from a directory

        Args:
            directory: Path to directory containing entity config files
            ignore_errors: If False, raises ValueError when an entity fails to load

        Returns:
            GhostGroup instance with loaded entities

        Raises:
            ValueError: If ignore_errors is False and any entity fails to load
        """
        logger.info(f"📁 Loading entities from directory: {directory}")

        ghost_group = cls()
        directory_path = Path(directory)

        if not directory_path.exists():
            error_msg = f"Directory {directory} does not exist"
            logger.warning(f"⚠️  {error_msg}")
            if not ignore_errors:
                raise ValueError(error_msg)
            return ghost_group

        # Supported file extensions
        supported_extensions = [".json", ".yaml", ".yml"]

        # Find all config files
        config_files = []
        for ext in supported_extensions:
            config_files.extend(directory_path.glob(f"*{ext}"))

        if not config_files:
            error_msg = f"No entity config files found in {directory}"
            logger.warning(f"⚠️  {error_msg}")
            if not ignore_errors:
                raise ValueError(error_msg)
            return ghost_group

        # Load each entity
        for file_path in config_files:
            try:
                ghost = Ghost.load_from_file(file_path)
                ghost_group.add_ghost(ghost)
            except ValueError as e:
                if not ignore_errors:
                    raise ValueError(
                        f"Failed to load entity from {file_path}: {str(e)}"
                    ) from e
                logger.error(
                    f"⚠️  Skipping failed entity load from {file_path}: {str(e)}",
                    exc_info=True,
                )

        if len(ghost_group) == 0 and not ignore_errors:
            raise ValueError(f"No entities were successfully loaded from {directory}")

        return ghost_group

    def __str__(self) -> str:
        return f"EntityGroup({len(self.ghosts)} entities: {list(self.ghosts.keys())})"
