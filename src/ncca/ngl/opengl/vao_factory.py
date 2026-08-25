"""Registry/factory for creating VAO instances by type name."""

import enum
from typing import Callable, Dict

from .abstract_vao import AbstractVAO
from .multi_buffer_vao import MultiBufferVAO
from .simple_index_vao import SimpleIndexVAO
from .simple_vao import SimpleVAO
from ..log import logger


class VAOType(enum.Enum):
    """Identifiers for the built-in VAO implementations."""

    SIMPLE = "simpleVAO"
    MULTI_BUFFER = "multiBufferVAO"
    SIMPLE_INDEX = "simpleIndexVAO"


class VAOFactory:
    """Factory for creating VAOs, extensible with custom creator functions."""

    _creators: Dict[VAOType, Callable[[int], AbstractVAO]] = {}

    @staticmethod
    def register_vao_creator(
        name: VAOType, creator_func: Callable[[int], AbstractVAO]
    ) -> None:
        """Register a creator callable for the given VAO type name."""
        VAOFactory._creators[name] = creator_func

    @staticmethod
    def create_vao(name: VAOType, mode: int) -> AbstractVAO:
        """Create a VAO of the named type with the given draw mode.

        Raises:
            ValueError: If the VAO type is not registered.
        """
        creator = VAOFactory._creators.get(name)
        if not creator:
            logger.warning(f"VAO type '{name}' not found.")
            raise ValueError(name)
        return creator(mode)


# pre-register the default VAO types
VAOFactory.register_vao_creator(VAOType.SIMPLE, SimpleVAO)
VAOFactory.register_vao_creator(VAOType.MULTI_BUFFER, MultiBufferVAO)
VAOFactory.register_vao_creator(VAOType.SIMPLE_INDEX, SimpleIndexVAO)
