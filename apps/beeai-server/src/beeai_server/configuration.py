# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import base64
import logging
from collections import defaultdict
from datetime import timedelta
from functools import cache
from pathlib import Path
from typing import Literal

from pydantic import AnyUrl, BaseModel, Field, Secret, ValidationError, field_validator, model_validator
from pydantic_core.core_schema import ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict

from beeai_server.domain.models.registry import RegistryLocation

logger = logging.getLogger(__name__)


class LoggingConfiguration(BaseModel):
    level: int = logging.INFO
    level_uvicorn: int = Field(default=logging.FATAL, validate_default=True)
    level_sqlalchemy: int = Field(default=None, validate_default=True)

    @model_validator(mode="after")
    def level_uvicorn_validator(self):
        if self.level == logging.DEBUG:
            self.level_uvicorn = logging.WARNING
        return self

    @field_validator("level_sqlalchemy", mode="before")
    @classmethod
    def level_sqlalchemy_validator(cls, v: str | int | None, info: ValidationInfo):
        if v is not None:
            return cls.validate_level(v)
        return logging.INFO if cls.validate_level(info.data["level"]) == logging.DEBUG else logging.WARNING

    @field_validator("level", "level_uvicorn", mode="before")
    @classmethod
    def validate_level(cls, v: str | int | None):
        return v if isinstance(v, int) else logging.getLevelNamesMapping()[v.upper()]


class OCIRegistryConfiguration(BaseModel, extra="allow"):
    username: str | None = None
    password: Secret[str] | None = None
    insecure: bool = False
    auth_header: Secret[str] | None = None

    @property
    def protocol(self):
        return "http" if self.insecure else "https"

    @property
    def basic_auth_str(self) -> str | None:
        if self.auth_header:
            return self.auth_header.get_secret_value()
        if self.username and self.password:
            return base64.b64encode(f"{self.username}:{self.password.get_secret_value()}".encode()).decode()
        return None


class AgentRegistryConfiguration(BaseModel):
    locations: dict[str, RegistryLocation] = Field(default_factory=dict)
    sync_period_cron: str = Field(default="*/5 * * * *")  # every 10 minutes


class AuthConfiguration(BaseModel):
    admin_password: Secret[str] | None = Field(default=None)
    disable_auth: bool = False

    @model_validator(mode="after")
    def validate_auth(self):
        if self.disable_auth:
            logger.critical("Authentication is disabled! This is suitable only for local (desktop) deployment.")
            return self
        if self.admin_password is None:
            raise ValueError("Admin password must be provided if authentication is enabled")
        return self


class ObjectStorageConfiguration(BaseModel):
    endpoint_url: AnyUrl = AnyUrl("http://seaweedfs-all-in-one:9009")
    access_key_id: Secret[str] = Secret("beeai-admin-user")
    access_key_secret: Secret[str] = Secret("beeai-admin-password")
    bucket_name: str = "beeai-files"
    region: str = "us-east-1"
    use_ssl: bool = False
    storage_limit_per_user_bytes: int = 1 * (1024 * 1024 * 1024)  # 1GiB
    max_single_file_size: int = 100 * (1024 * 1024)  # 100 MiB


class PersistenceConfiguration(BaseModel):
    db_url: Secret[AnyUrl] = Secret(AnyUrl("postgresql+asyncpg://beeai-user:password@postgresql:5432/beeai"))
    encryption_key: Secret[str] | None = None
    finished_requests_remove_after_sec: int = timedelta(minutes=30).total_seconds()
    stale_requests_remove_after_sec: int = timedelta(hours=1).total_seconds()
    vector_db_schema: str = Field("vector_db", pattern=r"^[a-zA-Z0-9_]+$")
    procrastinate_schema: str = Field("procrastinate", pattern=r"^[a-zA-Z0-9_]+$")


class VectorStoresConfiguration(BaseModel):
    expire_after_days: int = 7  # Number of days after which a vector store is considered expired
    storage_limit_per_user_bytes: int = 1 * (1024 * 1024 * 1024)  # 1GiB


class TelemetryConfiguration(BaseModel):
    collector_url: AnyUrl = AnyUrl("http://otel-collector-svc:4318")


class UIFeatureFlags(BaseModel):
    user_navigation: bool = Field(default=True)


class FeatureFlagsConfiguration(BaseModel):
    ui: UIFeatureFlags = UIFeatureFlags()


class DockerConfigJsonAuth(BaseModel, extra="allow"):
    auth: Secret[str] | None = None
    username: str | None = None
    password: Secret[str] | None = None


class DockerConfigJson(BaseModel):
    auths: dict[str, DockerConfigJsonAuth] = Field(default_factory=dict)


class ManagedProviderConfiguration(BaseModel):
    auto_remove_enabled: bool = False
    manifest_template_dir: Path | None = None
    self_registration_use_local_network: bool = Field(
        False,
        description="Which network to use for self-registered providers - should be False when running in cluster",
    )


class DoclingExtractionConfiguration(BaseModel):
    backend: Literal["docling"] = "docling"
    enabled: bool = False
    docling_service_url: str = "http://docling-serve:15001"
    processing_timeout_sec: int = timedelta(minutes=5).total_seconds()


class Configuration(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", env_nested_delimiter="__", extra="ignore"
    )

    auth: AuthConfiguration = Field(default_factory=AuthConfiguration)
    logging: LoggingConfiguration = Field(default_factory=LoggingConfiguration)
    agent_registry: AgentRegistryConfiguration = Field(default_factory=AgentRegistryConfiguration)
    oci_registry: dict[str, OCIRegistryConfiguration] = Field(default_factory=dict)
    oci_registry_docker_config_json: dict[int, DockerConfigJson] = {}
    telemetry: TelemetryConfiguration = Field(default_factory=TelemetryConfiguration)
    persistence: PersistenceConfiguration = Field(default_factory=PersistenceConfiguration)
    object_storage: ObjectStorageConfiguration = Field(default_factory=ObjectStorageConfiguration)
    vector_stores: VectorStoresConfiguration = Field(default_factory=VectorStoresConfiguration)
    text_extraction: DoclingExtractionConfiguration = Field(default_factory=DoclingExtractionConfiguration)
    k8s_namespace: str | None = None
    k8s_kubeconfig: Path | None = None

    provider: ManagedProviderConfiguration = Field(default_factory=ManagedProviderConfiguration)
    feature_flags: FeatureFlagsConfiguration = Field(default_factory=FeatureFlagsConfiguration)

    platform_service_url: str = "beeai-platform-svc:8333"
    port: int = 8333

    @model_validator(mode="after")
    def _oci_registry_defaultdict(self):
        oci_registry = defaultdict(OCIRegistryConfiguration)
        oci_registry.update(self.oci_registry)
        self.oci_registry = oci_registry
        for docker_config_json in self.oci_registry_docker_config_json.values():
            try:
                for registry, conf in docker_config_json.auths.items():
                    registry_short = AnyUrl(registry).host if "://" in registry else registry.strip("/")
                    self.oci_registry[registry_short].username = conf.username
                    self.oci_registry[registry_short].password = conf.password
                    self.oci_registry[registry_short].auth_header = conf.auth
            except ValueError as e:
                logger.error(f"Failed to parse .dockerconfigjson: {e}. Some agent images might not work correctly.")
        return self


@cache
def get_configuration() -> Configuration:
    """Get cached configuration"""
    try:
        return Configuration()
    except ValidationError as ex:
        from beeai_server.logging_config import configure_logging

        configure_logging(configuration=LoggingConfiguration(level=logging.ERROR))

        logging.error(f"Improperly configured, Error: {ex!r}")
        raise ValueError("Improperly configured, make sure to supply all required variables") from ex
