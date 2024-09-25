# src/utils/plugin_loader.py

import os
import pkgutil
import logging
import importlib
from typing import List, Type, TypeVar, Dict

# Define a generic type variable for plugin classes
T = TypeVar('T')


class PluginLoader:
    def __init__(self, plugin_package_path: str, base_plugin_class: Type[T]):
        """
        Initialize the PluginLoader.

        Args:
            plugin_package_path (str): The directory path where plugins are located.
            base_plugin_class (Type[T]): The base class that plugins should inherit from.
        """
        self.plugin_package_path = plugin_package_path
        self.base_plugin_class = base_plugin_class
        self.plugin_map: Dict[str, Type[T]] = {}
        
        self.logger = logging.getLogger(__name__)
        

    def load_plugins(self) -> None:
        """
        Load plugins from the plugin package directory.
        """
    
        if not os.path.isdir(self.plugin_package_path):
            raise ValueError(f"The plugin package directory '{self.plugin_package_path}' does not exist.")
    
    
        # Iterate over all .py files in the plugin package directory
        for filename in os.listdir(self.plugin_package_path):
            if filename.endswith('.py') and filename != '__init__.py':
                
                module_name, _ = os.path.splitext(filename)  # Strip .py extension
                module_file_path = os.path.join(self.plugin_package_path, filename)
                spec = importlib.util.spec_from_file_location(module_name, module_file_path)
        
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Now inspect the module for plugin classes
                    for attribute_name in dir(module):
                        attribute = getattr(module, attribute_name)
                        if (
                            isinstance(attribute, type)  # Check if the attribute is a class
                            and issubclass(attribute, self.base_plugin_class)  # Check if it's a subclass of the base plugin class
                            and attribute is not self.base_plugin_class  # Exclude the base plugin class itself
                        ):
                            
                            # Check if the plugin class has a 'get_name' method or 'plugin_name' attribute
                            plugin_name = None
                            if hasattr(attribute, 'get_name') and callable(getattr(attribute, 'get_name')):
                                # If 'get_name' is a class method
                                plugin_name = attribute.get_name()
                            elif hasattr(attribute, 'plugin_name'):
                                # If 'plugin_name' is a class attribute
                                plugin_name = getattr(attribute, 'plugin_name')
                            
                            if plugin_name:
                                self.plugin_map[plugin_name] = attribute
                                self.logger.info(f"Loaded plugin '{plugin_name}' from class '{attribute.__name__}'")
                            else:
                                self.logger.warning(f"Plugin class '{attribute.__name__}' does not have a 'get_name' method or 'plugin_name' attribute.")
        
                else:
                    self.logger.error(f"Could not load module {module_name} from {module_file_path}")
    
    
    def get_plugin_by_name(self, name: str) -> Type[T]:
        """
        Get a plugin class by its name.

        Args:
            name (str): The name of the plugin.

        Returns:
            Type[T]: The plugin class with the given name, or None if not found.
        """
        try:
            ret_plugin = self.plugin_map.get(name)
            return ret_plugin
        except Exception as e:
            self.logger.error(f"- PluginLoader - Attempted to Load invalid plugin (Name: {name}), Avaliable Plugin List: {self.get_all_plugin_names()}")
        
        return None
    
    
    def get_all_plugin_names(self) -> List[str]:
        """
        Get a list of all loaded plugin names.

        Returns:
            List[str]: A list of plugin names.
        """
        return list(self.plugin_map.keys())
    
