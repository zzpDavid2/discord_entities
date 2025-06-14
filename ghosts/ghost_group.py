import logging
from pathlib import Path
from typing import Dict, Optional, List
from .ghost import Ghost

# Set up logging for this module
logger = logging.getLogger(__name__)


class GhostGroup:
    """A collection of ghosts that can be managed and operated on as a group"""

    def __init__(self, ghosts: Dict[str, Ghost] = None):
        """
        Initialize a ghost group

        Args:
            ghosts: Dictionary mapping handles to Ghost instances
        """
        self.ghosts = ghosts or {}

    def __len__(self) -> int:
        """Return the number of ghosts in the group"""
        return len(self.ghosts)

    def __iter__(self):
        """Iterate over ghost handles and instances"""
        return iter(self.ghosts.items())

    def __getitem__(self, handle: str) -> Ghost:
        """Get a ghost by handle"""
        return self.ghosts[handle]

    def get(self, handle: str, default: Ghost = None) -> Optional[Ghost]:
        """Get a ghost by handle with default fallback"""
        return self.ghosts.get(handle, default)

    def keys(self):
        """Return ghost handles"""
        return self.ghosts.keys()

    def values(self):
        """Return ghost instances"""
        return self.ghosts.values()

    def items(self):
        """Return handle, ghost pairs"""
        return self.ghosts.items()

    def add_ghost(self, ghost: Ghost):
        """Add a ghost to the group"""
        self.ghosts[ghost.handle] = ghost
        logger.info(f"✅ Added ghost: {ghost.name} (handle: {ghost.handle}) to group")

    def remove_ghost(self, handle: str) -> Optional[Ghost]:
        """Remove a ghost by handle"""
        ghost = self.ghosts.pop(handle, None)
        if ghost:
            logger.info(f"🗑️ Removed ghost: {ghost.name} (handle: {handle}) from group")
        return ghost

    def find_ghost_by_mention(self, message_content: str) -> List[Ghost]:
        """Find all ghosts being mentioned in the message"""
        import re

        message_lower = message_content.lower()
        mentioned_ghosts = []

        # Check for pseudo-mentions like "@tomas", "@anna"
        pseudo_mention_pattern = r"@(\w+)"
        pseudo_mentions = re.findall(pseudo_mention_pattern, message_lower)

        # Check direct mentions by handle
        for mention in pseudo_mentions:
            if mention in self.ghosts:
                mentioned_ghosts.append(self.ghosts[mention])

        # Check if any handle appears in the message
        for handle, ghost in self.ghosts.items():
            if handle in message_lower and ghost not in mentioned_ghosts:
                mentioned_ghosts.append(ghost)

        return mentioned_ghosts

    @classmethod
    def load_from_directory(
        cls, directory: str, ignore_errors: bool = False
    ) -> "GhostGroup":
        """
        Load all ghost configurations from a directory

        Args:
            directory: Path to directory containing ghost config files
            ignore_errors: If False, raises ValueError when a ghost fails to load

        Returns:
            GhostGroup instance with loaded ghosts

        Raises:
            ValueError: If ignore_errors is False and any ghost fails to load
        """
        logger.info(f"📁 Loading ghosts from directory: {directory}")

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
            error_msg = f"No ghost config files found in {directory}"
            logger.warning(f"⚠️  {error_msg}")
            if not ignore_errors:
                raise ValueError(error_msg)
            return ghost_group

        # Load each ghost
        for file_path in config_files:
            try:
                ghost = Ghost.load_from_file(file_path)
                ghost_group.add_ghost(ghost)
            except ValueError as e:
                if not ignore_errors:
                    raise ValueError(
                        f"Failed to load ghost from {file_path}: {str(e)}"
                    ) from e
                logger.warning(
                    f"⚠️  Skipping failed ghost load from {file_path}: {str(e)}"
                )

        if len(ghost_group) == 0 and not ignore_errors:
            raise ValueError(f"No ghosts were successfully loaded from {directory}")

        return ghost_group

    def __str__(self) -> str:
        return f"GhostGroup({len(self.ghosts)} ghosts: {list(self.ghosts.keys())})"
