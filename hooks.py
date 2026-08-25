# Hooks proxy — برای اینکه hrms.hooks به hrms.hrms.hooks اشاره کند
import importlib
_real_hooks = importlib.import_module('hrms.hrms.hooks')
from hrms.hrms.hooks import *
