# src/validate/validator/base_validator.py

from abc import ABC, abstractmethod
from typing import Dict, Any

class Validator(ABC):
    @abstractmethod
    def run(self) -> bool:
        """
        Run the validator.

        Returns:
        - bool: True if validation passed, False otherwise.
        """
        pass
