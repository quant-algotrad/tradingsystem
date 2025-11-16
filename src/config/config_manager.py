"""
Configuration Manager
Centralized configuration management with Singleton pattern
Thread-safe, lazy-loaded, and environment-aware
"""

import threading
from pathlib import Path
from typing import Optional, Dict, Any
import yaml
import json
from dataclasses import asdict

from src.config.base_config import BaseConfig, ConfigType
from src.config.trading_config import TradingConfig
from src.config.risk_config import RiskConfig
from src.config.database_config import DatabaseConfig
from src.config.api_config import APIConfig
from src.config.constants import Environment


class ConfigurationManager:
    """
    Singleton Configuration Manager

    Pattern: Singleton (Thread-safe with double-checked locking)
    Responsibilities:
    - Load configurations from files
    - Validate configurations
    - Provide centralized access to configs
    - Support environment-specific configs
    """

    _instance: Optional['ConfigurationManager'] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls):
        """
        Thread-safe singleton implementation

        Uses double-checked locking pattern for performance
        """
        if cls._instance is None:
            with cls._lock:
                # Double-check after acquiring lock
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize only once"""
        if self._initialized:
            return

        self._initialized = True
        self._configs: Dict[ConfigType, BaseConfig] = {}
        self._environment: Environment = Environment.DEVELOPMENT
        self._config_dir: Path = Path("config/environments")
        self._loaded: bool = False

    @classmethod
    def get_instance(cls) -> 'ConfigurationManager':
        """
        Get singleton instance

        Returns:
            ConfigurationManager instance
        """
        return cls()

    def set_environment(self, env: Environment):
        """Set the operating environment"""
        self._environment = env
        self._loaded = False  # Force reload with new environment

    def set_config_directory(self, config_dir: str | Path):
        """Set configuration files directory"""
        self._config_dir = Path(config_dir)
        if not self._config_dir.exists():
            raise FileNotFoundError(f"Config directory not found: {self._config_dir}")

    def load_all_configs(self, force_reload: bool = False):
        """
        Load all configurations from environment-specific files

        Args:
            force_reload: Force reload even if already loaded
        """
        if self._loaded and not force_reload:
            return

        # Determine config file based on environment
        config_file = self._config_dir / f"{self._environment.value}.yaml"

        if not config_file.exists():
            print(f"[WARNING] Config file not found: {config_file}")
            print(f"[INFO] Loading default configurations")
            self._load_defaults()
        else:
            print(f"[INFO] Loading config from: {config_file}")
            self._load_from_file(config_file)

        # Validate all configs
        self._validate_all()
        self._loaded = True

    def _load_from_file(self, config_file: Path):
        """Load configurations from YAML file"""
        try:
            with open(config_file, 'r') as f:
                data = yaml.safe_load(f)

            # Load each config type
            if 'trading' in data:
                self._configs[ConfigType.TRADING] = self._create_trading_config(data['trading'])

            if 'risk' in data:
                self._configs[ConfigType.RISK] = self._create_risk_config(data['risk'])

            if 'database' in data:
                self._configs[ConfigType.DATABASE] = self._create_database_config(data['database'])

            if 'api' in data:
                self._configs[ConfigType.API] = self._create_api_config(data['api'])

        except Exception as e:
            print(f"[ERROR] Failed to load config file: {e}")
            raise

    def _load_defaults(self):
        """Load default configurations"""
        self._configs[ConfigType.TRADING] = TradingConfig()
        self._configs[ConfigType.RISK] = RiskConfig()
        self._configs[ConfigType.DATABASE] = DatabaseConfig()
        self._configs[ConfigType.API] = APIConfig()

    def _create_trading_config(self, data: Dict[str, Any]) -> TradingConfig:
        """Factory method for TradingConfig"""
        return TradingConfig().from_dict(data)

    def _create_risk_config(self, data: Dict[str, Any]) -> RiskConfig:
        """Factory method for RiskConfig"""
        return RiskConfig().from_dict(data)

    def _create_database_config(self, data: Dict[str, Any]) -> DatabaseConfig:
        """Factory method for DatabaseConfig"""
        return DatabaseConfig().from_dict(data)

    def _create_api_config(self, data: Dict[str, Any]) -> APIConfig:
        """Factory method for APIConfig"""
        return APIConfig().from_dict(data)

    def _validate_all(self):
        """Validate all loaded configurations"""
        errors = []

        for config_type, config in self._configs.items():
            is_valid, config_errors = config.validate()
            if not is_valid:
                errors.extend([f"{config_type.value}: {err}" for err in config_errors])

        if errors:
            error_msg = "\n".join(errors)
            raise ValueError(f"Configuration validation failed:\n{error_msg}")

    def get_trading_config(self) -> TradingConfig:
        """Get trading configuration"""
        if not self._loaded:
            self.load_all_configs()
        return self._configs.get(ConfigType.TRADING, TradingConfig())

    def get_risk_config(self) -> RiskConfig:
        """Get risk management configuration"""
        if not self._loaded:
            self.load_all_configs()
        return self._configs.get(ConfigType.RISK, RiskConfig())

    def get_database_config(self) -> DatabaseConfig:
        """Get database configuration"""
        if not self._loaded:
            self.load_all_configs()
        return self._configs.get(ConfigType.DATABASE, DatabaseConfig())

    def get_api_config(self) -> APIConfig:
        """Get API configuration"""
        if not self._loaded:
            self.load_all_configs()
        return self._configs.get(ConfigType.API, APIConfig())

    def get_config(self, config_type: ConfigType) -> BaseConfig:
        """
        Get configuration by type

        Args:
            config_type: Type of configuration to retrieve

        Returns:
            Configuration object
        """
        if not self._loaded:
            self.load_all_configs()
        return self._configs.get(config_type)

    def update_config(self, config_type: ConfigType, config: BaseConfig):
        """
        Update a configuration

        Args:
            config_type: Type of configuration
            config: New configuration object
        """
        # Validate before updating
        is_valid, errors = config.validate()
        if not is_valid:
            raise ValueError(f"Invalid configuration: {', '.join(errors)}")

        self._configs[config_type] = config

    def save_to_file(self, output_file: Path):
        """
        Save current configurations to YAML file

        Args:
            output_file: Path to output file
        """
        data = {}

        for config_type, config in self._configs.items():
            # Convert dataclass to dict
            config_dict = self._config_to_dict(config)
            data[config_type.value] = config_dict

        # Write to YAML
        with open(output_file, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        print(f"[SUCCESS] Configuration saved to: {output_file}")

    def _config_to_dict(self, config: BaseConfig) -> Dict[str, Any]:
        """
        Convert configuration to dictionary (recursive)

        Handles nested dataclasses and enums
        """
        def convert_value(value):
            if hasattr(value, '__dataclass_fields__'):  # Is dataclass
                return asdict(value)
            elif hasattr(value, 'value'):  # Is enum
                return value.value
            elif isinstance(value, (list, tuple)):
                return [convert_value(v) for v in value]
            elif isinstance(value, dict):
                return {k: convert_value(v) for k, v in value.items()}
            else:
                return value

        return convert_value(asdict(config))

    def get_summary(self) -> str:
        """Get summary of all configurations"""
        if not self._loaded:
            self.load_all_configs()

        summary = [
            "="*60,
            "CONFIGURATION SUMMARY",
            "="*60,
            f"Environment: {self._environment.value.upper()}",
            ""
        ]

        for config_type, config in self._configs.items():
            summary.append(f"\n{config_type.value.upper()} CONFIGURATION:")
            summary.append("-"*60)
            summary.append(config.get_summary())

        summary.append("="*60)
        return "\n".join(summary)

    def print_summary(self):
        """Print configuration summary"""
        print(self.get_summary())

    def reset(self):
        """Reset configuration manager (for testing)"""
        self._configs.clear()
        self._loaded = False

    @classmethod
    def reset_instance(cls):
        """Reset singleton instance (for testing only)"""
        with cls._lock:
            cls._instance = None


# ==================================================
# Convenience Functions
# ==================================================

def get_config_manager() -> ConfigurationManager:
    """
    Get the global configuration manager instance

    Returns:
        ConfigurationManager singleton
    """
    return ConfigurationManager.get_instance()


def get_trading_config() -> TradingConfig:
    """Quick access to trading configuration"""
    return get_config_manager().get_trading_config()


def get_risk_config() -> RiskConfig:
    """Quick access to risk configuration"""
    return get_config_manager().get_risk_config()


def get_database_config() -> DatabaseConfig:
    """Quick access to database configuration"""
    return get_config_manager().get_database_config()


def get_api_config() -> APIConfig:
    """Quick access to API configuration"""
    return get_config_manager().get_api_config()


# ==================================================
# Example Usage
# ==================================================

if __name__ == '__main__':
    # Initialize configuration manager
    config_mgr = ConfigurationManager.get_instance()

    # Set environment
    config_mgr.set_environment(Environment.DEVELOPMENT)

    # Load configurations (will use defaults if file not found)
    config_mgr.load_all_configs()

    # Print summary
    config_mgr.print_summary()

    # Access specific configs
    trading = config_mgr.get_trading_config()
    print(f"\nMax Position Capital: ₹{trading.get_max_position_capital():,.2f}")

    risk = config_mgr.get_risk_config()
    print(f"Daily Loss Limit: {risk.loss_limits.max_daily_loss_percent}%")

    # Calculate position size
    capital = 50000
    entry = 500
    stop_loss = 490
    position_size = risk.calculate_position_size(capital, entry, stop_loss)
    print(f"Position Size: {position_size} shares")
