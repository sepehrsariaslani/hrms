# Namespace package root — proxy hooks to hrms.hrms.hooks
import sys
import importlib

# When someone does `from hrms import hooks`, redirect to hrms.hrms.hooks
_hooks_module = importlib.import_module('hrms.hrms.hooks')
sys.modules['hrms.hooks'] = _hooks_module
