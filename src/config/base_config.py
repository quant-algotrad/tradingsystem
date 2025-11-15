"""
Base Configuration Classes
Abstract base classes and interfaces for configuration management
Follows SOLID principles and provides extensibility
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
import copy


# ============================================
# INTERFACE: Configuration Contract
# ============================================

class IConfiguration(ABC):
    """
    Interface for all configuration classes

    SOLID Principles:
    - Interface Segregation: Specific interfaces for different config types
    - Dependency Inversion: Depend on abstractions, not concretions
    """

    @abstractmethod
    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate configuration parameters

        Returns:
            tuple: (is_valid, list_of_errors)
        """
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        pass

    @abstractmethod
    def from_dict(self, data: Dict[str, Any]) -> 'IConfiguration':
        """Create configuration from dictionary"""
        pass

    @abstractmethod
    def get_summary(self) -> str:
        """Get human-readable summary of configuration"""
        pass


# ============================================
# ABSTRACT BASE: Configuration Base Class
# ============================================

@dataclass
class BaseConfig(IConfiguration, ABC):
    """
    Abstract base class for all configurations

    SOLID Principles:
    - Single Responsibility: Base functionality only
    - Open/Closed: Open for extension, closed for modification
    """

    config_version: str = "1.0"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    enabled: bool = True

    def __post_init__(self):
        """Post-initialization validation"""
        is_valid, errors = self.validate()
        if not is_valid:
            raise ValueError(f"Configuration validation failed: {', '.join(errors)}")

    @abstractmethod
    def validate(self) -> tuple[bool, List[str]]:
        """Implement in derived classes"""
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Convert dataclass to dictionary"""
        result = {}
        for field_name, field_value in self.__dict__.items():
            if isinstance(field_value, datetime):
                result[field_name] = field_value.isoformat()
            elif isinstance(field_value, Enum):
                result[field_name] = field_value.value
            else:
                result[field_name] = field_value
        return result

    def get_immutable_copy(self) -> 'BaseConfig':
        """
        Return deep copy for immutability

        Pattern: Prototype Pattern
        """
        return copy.deepcopy(self)

    def update_timestamp(self):
        """Update the modification timestamp"""
        self.updated_at = datetime.now()

    def __str__(self) -> str:
        return self.get_summary()


# ============================================
# MIXIN: Validation Helpers
# ============================================

class ValidationMixin:
    """
    Mixin class providing common validation methods

    Pattern: Mixin Pattern for code reuse
    """

    @staticmethod
    def validate_range(value: float, min_val: float, max_val: float,
                       field_name: str) -> Optional[str]:
        """Validate numeric range"""
        if not (min_val <= value <= max_val):
            return f"{field_name} must be between {min_val} and {max_val}, got {value}"
        return None

    @staticmethod
    def validate_positive(value: float, field_name: str) -> Optional[str]:
        """Validate positive number"""
        if value <= 0:
            return f"{field_name} must be positive, got {value}"
        return None

    @staticmethod
    def validate_non_negative(value: float, field_name: str) -> Optional[str]:
        """Validate non-negative number"""
        if value < 0:
            return f"{field_name} must be non-negative, got {value}"
        return None

    @staticmethod
    def validate_percentage(value: float, field_name: str) -> Optional[str]:
        """Validate percentage (0-100)"""
        if not (0 <= value <= 100):
            return f"{field_name} must be between 0 and 100, got {value}"
        return None

    @staticmethod
    def validate_not_empty(value: Any, field_name: str) -> Optional[str]:
        """Validate non-empty value"""
        if not value:
            return f"{field_name} cannot be empty"
        return None

    @staticmethod
    def validate_list_not_empty(value: List, field_name: str) -> Optional[str]:
        """Validate list is not empty"""
        if not value or len(value) == 0:
            return f"{field_name} list cannot be empty"
        return None


# ============================================
# ABSTRACT: Numeric Config
# ============================================

@dataclass
class NumericConfig(BaseConfig, ValidationMixin, ABC):
    """Base class for numeric configuration parameters"""

    def validate_numeric_field(self, value: float, field_name: str,
                               min_val: Optional[float] = None,
                               max_val: Optional[float] = None,
                               must_be_positive: bool = False) -> Optional[str]:
        """Unified numeric validation"""
        errors = []

        if must_be_positive:
            error = self.validate_positive(value, field_name)
            if error:
                errors.append(error)

        if min_val is not None and max_val is not None:
            error = self.validate_range(value, min_val, max_val, field_name)
            if error:
                errors.append(error)

        return errors[0] if errors else None


# ============================================
# INTERFACE: Observable Configuration
# ============================================

class IConfigObserver(ABC):
    """
    Observer interface for configuration changes

    Pattern: Observer Pattern
    """

    @abstractmethod
    def on_config_changed(self, config_name: str, old_value: Any, new_value: Any):
        """Called when configuration changes"""
        pass


class ObservableConfig(BaseConfig):
    """
    Configuration that notifies observers on changes

    Pattern: Observer Pattern for reactive updates
    """

    def __init__(self):
        super().__init__()
        self._observers: List[IConfigObserver] = []

    def attach_observer(self, observer: IConfigObserver):
        """Add observer"""
        if observer not in self._observers:
            self._observers.append(observer)

    def detach_observer(self, observer: IConfigObserver):
        """Remove observer"""
        if observer in self._observers:
            self._observers.remove(observer)

    def notify_observers(self, config_name: str, old_value: Any, new_value: Any):
        """Notify all observers of change"""
        for observer in self._observers:
            observer.on_config_changed(config_name, old_value, new_value)


# ============================================
# INTERFACE: Serializable Configuration
# ============================================

class ISerializable(ABC):
    """Interface for configuration serialization"""

    @abstractmethod
    def to_yaml(self) -> str:
        """Serialize to YAML"""
        pass

    @abstractmethod
    def to_json(self) -> str:
        """Serialize to JSON"""
        pass

    @abstractmethod
    def from_yaml(self, yaml_str: str) -> 'ISerializable':
        """Deserialize from YAML"""
        pass

    @abstractmethod
    def from_json(self, json_str: str) -> 'ISerializable':
        """Deserialize from JSON"""
        pass


# ============================================
# HELPER: Configuration Builder
# ============================================

class ConfigBuilder(ABC):
    """
    Abstract builder for complex configurations

    Pattern: Builder Pattern for step-by-step construction
    """

    def __init__(self):
        self._config = None

    @abstractmethod
    def reset(self):
        """Reset builder state"""
        pass

    @abstractmethod
    def build(self) -> BaseConfig:
        """Build and return configuration"""
        pass


# ============================================
# ENUM: Configuration Types
# ============================================

from enum import Enum


class ConfigType(Enum):
    """Types of configurations in the system"""
    TRADING = "trading"
    RISK = "risk"
    DATABASE = "database"
    API = "api"
    STRATEGY = "strategy"
    INDICATORS = "indicators"
    BROKER = "broker"
    NOTIFICATIONS = "notifications"
    SYSTEM = "system"
