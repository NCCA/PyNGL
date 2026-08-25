# Miscellaneous Classes

Auto-generated API reference. For a guided introduction to the vector
array classes see the [Vector Arrays tutorial](tutorials/vector_arrays.md).

## Random

::: ncca.ngl.Random

## PySideEventHandlingMixin

::: ncca.ngl.opengl.PySideEventHandlingMixin

## Vec2Array

::: ncca.ngl.Vec2Array

## Vec3Array

::: ncca.ngl.Vec3Array

## Vec4Array

::: ncca.ngl.Vec4Array

## Logging

`ncca.ngl.logger` is a ready-made `logging.Logger` shared by the whole
library — it writes coloured output to the console and plain text to
`NGLDebug.log`. Import it and use it directly:

```python
from ncca.ngl import logger

logger.info("shader compiled")
```

`setup_logger` builds it, and is only worth calling yourself if you want
a second, separately configured logger.

### setup_logger

::: ncca.ngl.log.setup_logger
