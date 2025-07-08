import logging
from pathlib import Path
from typing import Dict, Optional, List
from .entity import Entity

# Set up logging for this module
logger = logging.getLogger(__name__)


class EntityGroup:
    """A collection of entities that can be managed and operated on as a group"""

    def __init__(self, entities: Dict[str, Entity] = None):
        """
        Initialize an entity group

        Args:
            entitys: Dictionary mapping handles to Entity instances
        """
        self.entitys = entities or {}

    def __len__(self) -> int:
        """Return the number of entities in the group"""
        return len(self.entitys)

    def __iter__(self):
        """Iterate over entity handles and instances"""
        return iter(self.entitys.items())

    def __getitem__(self, handle: str) -> Entity:
        """Get an entity by handle"""
        return self.entitys[handle]

    def get(self, handle: str, default: Entity = None) -> Optional[Entity]:
        """Get an entity by handle with default fallback"""
        return self.entitys.get(handle, default)

    def keys(self):
        """Return entity handles"""
        return self.entitys.keys()

    def values(self):
        """Return entity instances"""
        return self.entitys.values()

    def items(self):
        """Return handle, entity pairs"""
        return self.entitys.items()

    def add_entity(self, entity: Entity):
        """Add an entity to the group"""
        self.entitys[entity.handle] = entity
        logger.info(f"✅ Added entity: {entity.name} (handle: {entity.handle}) to group")

    def remove_entity(self, handle: str) -> Optional[Entity]:
        """Remove an entity by handle"""
        entity = self.entitys.pop(handle, None)
        if entity:
            logger.info(f"🗑️ Removed entity: {entity.name} (handle: {handle}) from group")
        return entity

    def find_entity_by_mention(self, message_content: str) -> List[Entity]:
        """Find all entities being mentioned in the message"""
        import re

        message_lower = message_content.lower()
        mentioned_entitys = []

        # Check for pseudo-mentions like "@tomas", "@anna"
        pseudo_mention_pattern = r"@(\w+)"
        pseudo_mentions = re.findall(pseudo_mention_pattern, message_lower)
        pseudo_mentions = [mention.lower() for mention in pseudo_mentions]

        # Check if any handle appears in the message or pseudo-mentions
        for handle, entity in self.entitys.items():
            if (
                f"@{handle.lower()}" in message_lower
                or handle.lower() in pseudo_mentions
                and entity not in mentioned_entitys
            ):
                mentioned_entitys.append(entity)

        return mentioned_entitys

    def _normalize_entity_name(self, name: str) -> str:
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

    def get_entity_by_name(self, name: str) -> Optional[Entity]:
        """
        Find an entity by their display name (case-insensitive)

        Args:
            name: The entity's display name

        Returns:
            Entity instance if found, None otherwise
        """
        normalized_name = self._normalize_entity_name(name).lower()

        for entity in self.entitys.values():
            if self._normalize_entity_name(entity.name).lower() == normalized_name:
                return entity

        return None

    @classmethod
    def load_from_directory(
        cls, directory: str, ignore_errors: bool = True
    ) -> "EntityGroup":
        """
        Load all entity configurations from a directory

        Args:
            directory: Path to directory containing entity config files
            ignore_errors: If False, raises ValueError when an entity fails to load

        Returns:
            EntityGroup instance with loaded entities

        Raises:
            ValueError: If ignore_errors is False and any entity fails to load
        """
        logger.info(f"📁 Loading entities from directory: {directory}")

        entity_group = cls()
        directory_path = Path(directory)

        if not directory_path.exists():
            error_msg = f"Directory {directory} does not exist"
            logger.warning(f"⚠️  {error_msg}")
            if not ignore_errors:
                raise ValueError(error_msg)
            return entity_group

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
            return entity_group

        # Load each entity
        for file_path in config_files:
            try:
                entity = Entity.load_from_file(file_path)
                entity_group.add_entity(entity)
            except ValueError as e:
                if not ignore_errors:
                    raise ValueError(
                        f"Failed to load entity from {file_path}: {str(e)}"
                    ) from e
                logger.error(
                    f"⚠️  Skipping failed entity load from {file_path}: {str(e)}",
                    exc_info=True,
                )

        if len(entity_group) == 0 and not ignore_errors:
            raise ValueError(f"No entities were successfully loaded from {directory}")

        return entity_group

    def __str__(self) -> str:
        return f"EntityGroup({len(self.entitys)} entities: {list(self.entitys.keys())})"
