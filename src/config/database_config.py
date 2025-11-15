"""
Database Configuration
Defines database connection and management settings
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from pathlib import Path
from src.config.base_config import BaseConfig, ValidationMixin


@dataclass
class DatabaseConnectionConfig(ValidationMixin):
    """Database connection settings"""

    # Database type
    db_type: str = "sqlite"  # Currently only SQLite supported
    db_path: str = "data/trading_system.db"

    # Connection settings
    timeout: int = 30  # seconds
    check_same_thread: bool = False  # For SQLite multi-threading
    isolation_level: str = "DEFERRED"  # SQLite transaction isolation

    # Connection pooling (for future scalability)
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30

    def validate(self) -> tuple[bool, List[str]]:
        """Validate connection config"""
        errors = []

        if self.db_type not in ["sqlite"]:
            errors.append(f"Unsupported database type: {self.db_type}")

        if error := self.validate_positive(self.timeout, "timeout"):
            errors.append(error)

        if self.timeout < 5:
            errors.append("Timeout must be at least 5 seconds")

        if self.pool_size < 1:
            errors.append("Pool size must be at least 1")

        # Validate db_path exists or can be created
        db_file = Path(self.db_path)
        if not db_file.parent.exists():
            try:
                db_file.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create database directory: {e}")

        return (len(errors) == 0, errors)


@dataclass
class DatabaseMaintenanceConfig(ValidationMixin):
    """Database maintenance and optimization settings"""

    # Backup settings
    enable_auto_backup: bool = True
    backup_frequency_hours: int = 24  # Daily backup
    backup_directory: str = "data/backups"
    max_backups_to_keep: int = 7  # Keep last 7 days

    # Vacuum/Optimize
    enable_auto_vacuum: bool = True
    vacuum_frequency_days: int = 7  # Weekly vacuum

    # Archive old data
    enable_auto_archive: bool = True
    archive_after_days: int = 365  # Archive data older than 1 year
    archive_directory: str = "data/archives"

    # Data retention
    delete_old_market_data_days: int = 90  # Keep 90 days of intraday data
    delete_old_logs_days: int = 30

    def validate(self) -> tuple[bool, List[str]]:
        """Validate maintenance config"""
        errors = []

        if self.backup_frequency_hours < 1:
            errors.append("Backup frequency must be at least 1 hour")

        if self.max_backups_to_keep < 1:
            errors.append("Must keep at least 1 backup")

        if self.vacuum_frequency_days < 1:
            errors.append("Vacuum frequency must be at least 1 day")

        if self.archive_after_days < 30:
            errors.append("Archive threshold must be at least 30 days")

        return (len(errors) == 0, errors)


@dataclass
class DatabasePerformanceConfig(ValidationMixin):
    """Performance optimization settings"""

    # Query optimization
    enable_query_cache: bool = True
    query_cache_size_mb: int = 50
    query_cache_ttl_seconds: int = 300  # 5 minutes

    # Indexing
    auto_create_indexes: bool = True
    analyze_frequency_hours: int = 24  # Run ANALYZE daily

    # Batch operations
    batch_insert_size: int = 1000  # Insert in batches of 1000
    enable_batch_commits: bool = True

    # Read optimization
    enable_read_uncommitted: bool = False  # For faster reads (less safe)
    use_wal_mode: bool = True  # Write-Ahead Logging for better concurrency

    def validate(self) -> tuple[bool, List[str]]:
        """Validate performance config"""
        errors = []

        if self.query_cache_size_mb < 1:
            errors.append("Query cache size must be at least 1 MB")

        if self.query_cache_ttl_seconds < 10:
            errors.append("Cache TTL must be at least 10 seconds")

        if self.batch_insert_size < 100:
            errors.append("Batch size must be at least 100")

        return (len(errors) == 0, errors)


@dataclass
class DatabaseConfig(BaseConfig, ValidationMixin):
    """
    Main Database Configuration

    Manages all database-related settings
    """

    # Sub-configurations
    connection: DatabaseConnectionConfig = field(default_factory=DatabaseConnectionConfig)
    maintenance: DatabaseMaintenanceConfig = field(default_factory=DatabaseMaintenanceConfig)
    performance: DatabasePerformanceConfig = field(default_factory=DatabasePerformanceConfig)

    # Schema management
    schema_version: str = "1.0"
    auto_migrate: bool = True  # Auto-migrate schema on version change
    strict_schema_validation: bool = True

    # Logging
    log_queries: bool = False  # For debugging only
    log_slow_queries: bool = True
    slow_query_threshold_ms: int = 1000  # Log queries > 1 second

    def validate(self) -> tuple[bool, List[str]]:
        """Validate database configuration"""
        errors = []

        # Validate all sub-configurations
        for sub_config in [self.connection, self.maintenance, self.performance]:
            is_valid, sub_errors = sub_config.validate()
            errors.extend(sub_errors)

        # Validate slow query threshold
        if self.slow_query_threshold_ms < 100:
            errors.append("Slow query threshold must be at least 100ms")

        return (len(errors) == 0, errors)

    def from_dict(self, data: Dict[str, Any]) -> 'DatabaseConfig':
        """Create from dictionary"""
        if 'connection' in data:
            data['connection'] = DatabaseConnectionConfig(**data['connection'])
        if 'maintenance' in data:
            data['maintenance'] = DatabaseMaintenanceConfig(**data['maintenance'])
        if 'performance' in data:
            data['performance'] = DatabasePerformanceConfig(**data['performance'])

        return DatabaseConfig(**data)

    def get_summary(self) -> str:
        """Human-readable summary"""
        return f"""
Database Configuration Summary:
- Type: {self.connection.db_type.upper()}
- Path: {self.connection.db_path}
- Schema Version: {self.schema_version}
- Auto Backup: {'Enabled' if self.maintenance.enable_auto_backup else 'Disabled'}
- Backup Frequency: Every {self.maintenance.backup_frequency_hours} hours
- Query Cache: {'Enabled' if self.performance.enable_query_cache else 'Disabled'}
- WAL Mode: {'Enabled' if self.performance.use_wal_mode else 'Disabled'}
- Auto Vacuum: {'Enabled' if self.maintenance.enable_auto_vacuum else 'Disabled'}
        """.strip()

    def get_connection_string(self) -> str:
        """Generate database connection string"""
        if self.connection.db_type == "sqlite":
            return f"sqlite:///{self.connection.db_path}"
        else:
            raise ValueError(f"Unsupported database type: {self.connection.db_type}")

    def get_absolute_db_path(self) -> Path:
        """Get absolute path to database file"""
        return Path(self.connection.db_path).resolve()
