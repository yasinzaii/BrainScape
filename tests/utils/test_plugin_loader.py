#tests/utils/test_plugin_loader.py

import os
import sys
import shutil
import importlib
import tempfile
import unittest
from pathlib import Path
from typing import List, Tuple, Any, Dict
from unittest.mock import patch, MagicMock
from src.utils.plugin_loader import PluginLoader



# Define Test Base Plugin Class
class_base_plugin = """
# test_base_plugin.py
from abc import ABC, abstractmethod

class TestBasePlugin(ABC):
    
    @abstractmethod
    def tester (self) -> int:
        # Just a simple tester function
        pass
        
    @abstractmethod
    def get_name(self) -> str:
        # Return the name of the plugin.
        pass
    
"""

# First Test Plugin
first_plugin = """
# first_plugin.py
from test_base_plugin import TestBasePlugin

class FirstPlugin(TestBasePlugin):
    
    # Class-specific plugin name (not instance-specific)
    plugin_name = "FirstTestPlugin"
    
    def __init__(self):
        pass
        
    def tester (self) -> int:
        print("This is the First Plugin, Returns 10")
        return 10
    
    @classmethod
    def get_name(cls) -> str:
        # Return the name of the plugin.
        return cls.plugin_name
"""

# Second Test Plugin
second_plugin = """
# second_plugin.py
from test_base_plugin import TestBasePlugin

class SecondPlugin(TestBasePlugin):
    
    # Class-specific plugin name (not instance-specific)
    plugin_name = "SecondTestPlugin"
    
    def __init__(self):
        pass

    def tester (self) -> int:
        print("This is the Second Plugin, Returns 20")
        return 20
    
    @classmethod
    def get_name(cls) -> str:
        # Return the name of the plugin.
        return cls.plugin_name
"""


class TestPluginLoader(unittest.TestCase):
    
    def setUp(self):
        
        # Create a temporary directory
        self.temp_dir = tempfile.mkdtemp()
        
        # Plugins Directory
        self.plugins_dir = os.path.join(self.temp_dir, "plugins")
        os.makedirs(self.plugins_dir, exist_ok=True)
        
        # Add __init__.py to make it a package    
        init_path = os.path.join(self.plugins_dir, "__init__.py")
        with open(init_path, 'w') as file:
            file.write("# Init file for plugins package")
    
        # Write the base plugin class definition to a file
        self.class_base_plugin_path = os.path.join(self.plugins_dir, "test_base_plugin.py" )
        with open(self.class_base_plugin_path, 'w') as file:
            file.write(class_base_plugin)
        
        # Write the base plugin class definition to a file
        first_plugin_path = os.path.join(self.plugins_dir, "first_plugin.py" )
        with open(first_plugin_path, 'w') as file:
            file.write(first_plugin)
            
        # Write the base plugin class definition to a file
        second_plugin_path = os.path.join(self.plugins_dir, "second_plugin.py" )
        with open(second_plugin_path, 'w') as file:
            file.write(second_plugin)
            
        # Load the base plugin class and register it in sys.modules
        spec = importlib.util.spec_from_file_location("test_base_plugin", self.class_base_plugin_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        sys.modules['test_base_plugin'] = module  # Register the module
        self.base_plugin_class = getattr(module, "TestBasePlugin")
        
        
    def tearDown(self):
        """
        Clean up the test environment after each test method.
        Removes the temporary directory and its contents.
        """
        shutil.rmtree(self.temp_dir)
        sys.modules.pop('test_base_plugin', None)
        
    def test_plugins_loaded_correctly(self):
        
        
        plugin_manager = PluginLoader(self.plugins_dir, self.base_plugin_class)
        
        # loading plugin. 
        plugin_manager.load_plugins()
        
        # Test that the plugins were loaded
        self.assertEqual(len(plugin_manager.get_all_plugin_names()), 2)
        self.assertEqual(sorted(plugin_manager.get_all_plugin_names()), sorted(["FirstTestPlugin","SecondTestPlugin"]))
        
        # Instantiate and test each plugin
        plugin_classes = [plugin_manager.get_plugin_by_name(name) for name in plugin_manager.get_all_plugin_names()]
        plugin_instances = [item()  for item in plugin_classes]
        names = [instance.get_name() for instance in plugin_instances]
        self.assertIn("FirstTestPlugin", names)
        self.assertIn("SecondTestPlugin", names)
        
        # Test the tester methods
        tester_results = [instance.tester() for instance in plugin_instances]
        self.assertIn(10, tester_results)
        self.assertIn(20, tester_results)
        
        
        
if __name__ == "__main__":
    unittest.main()