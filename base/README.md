FabSim base directory
======

This directory contains the base functionality of FabSim. Although the Python
files here can be technically modified, it is not recommended as these
functionalities are expected to be relied upon by customized modules.

Moreover, these base functionalities will be periodically maintained and
extended by the core dev team.

However, any custom FabSim file can rely on these functionalities, and extend
or combine them simply by doing the right import at the beginning, e.g.:
```
from base.fab import *
```

