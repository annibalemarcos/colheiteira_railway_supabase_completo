"""
core/__init__.py
Módulo core do Colheiteira
"""
from .plugin_loader import PluginLoader
from .scorer import Scorer
from .validator import Validator
from .config_loader import ConfigLoader

__all__ = ['PluginLoader', 'Scorer', 'Validator', 'ConfigLoader']
__version__ = '1.0.0'