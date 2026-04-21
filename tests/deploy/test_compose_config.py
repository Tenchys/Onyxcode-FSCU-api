"""Unit tests for docker-compose configuration validation."""
import os
import re
from pathlib import Path

import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_PATH = PROJECT_ROOT / "docker-compose.yml"
DOCKERFILE_PATH = PROJECT_ROOT / "Dockerfile"
ENV_EXAMPLE_PATH = PROJECT_ROOT / ".env.example"


class TestDockerComposeConfig:
    """Tests for docker-compose.yml structural validity."""

    def test_compose_file_exists(self):
        """docker-compose.yml must exist in project root."""
        assert COMPOSE_PATH.exists(), f"Expected {COMPOSE_PATH} to exist"

    def test_compose_is_valid_yaml(self):
        """docker-compose.yml must be parseable as YAML."""
        with open(COMPOSE_PATH) as f:
            data = yaml.safe_load(f)
        assert isinstance(data, dict), "docker-compose.yml must parse to a dict"
        assert "services" in data

    def test_defines_postgres_service(self):
        """Services must include postgres."""
        with open(COMPOSE_PATH) as f:
            data = yaml.safe_load(f)
        assert "postgres" in data["services"]

    def test_defines_api_service(self):
        """Services must include api."""
        with open(COMPOSE_PATH) as f:
            data = yaml.safe_load(f)
        assert "api" in data["services"]

    def test_postgres_has_healthcheck(self):
        """Postgres service must have a healthcheck configured."""
        with open(COMPOSE_PATH) as f:
            data = yaml.safe_load(f)
        pg = data["services"]["postgres"]
        assert "healthcheck" in pg, "postgres service must have healthcheck"

    def test_api_has_healthcheck(self):
        """API service must have a healthcheck configured."""
        with open(COMPOSE_PATH) as f:
            data = yaml.safe_load(f)
        api = data["services"]["api"]
        assert "healthcheck" in api, "api service must have healthcheck"

    def test_postgres_depends_on_health(self):
        """postgres depends_on must use condition: service_healthy."""
        with open(COMPOSE_PATH) as f:
            data = yaml.safe_load(f)
        api = data["services"]["api"]
        assert "depends_on" in api
        deps = api["depends_on"]
        assert isinstance(deps, dict), "depends_on should use long-form syntax"
        assert deps["postgres"]["condition"] == "service_healthy"

    def test_api_build_section_present(self):
        """API service must have a build section pointing to Dockerfile."""
        with open(COMPOSE_PATH) as f:
            data = yaml.safe_load(f)
        api = data["services"]["api"]
        assert "build" in api
        assert api["build"].get("dockerfile") == "Dockerfile"

    def test_persistent_volume_declared(self):
        """A named volume must be declared for Postgres data persistence."""
        with open(COMPOSE_PATH) as f:
            data = yaml.safe_load(f)
        assert "volumes" in data
        assert any("postgres_data" in v for v in data["volumes"])

    def test_no_hardcoded_secrets(self):
        """Secrets must come from environment variables, not be hardcoded."""
        with open(COMPOSE_PATH) as f:
            content = f.read()
        # Check no bare password strings
        assert "my_secret_password" not in content
        assert "change-me" not in content or "${POSTGRES_PASSWORD}" in content

    def test_exposes_app_port(self):
        """API service must expose APP_PORT."""
        with open(COMPOSE_PATH) as f:
            data = yaml.safe_load(f)
        api = data["services"]["api"]
        assert "ports" in api
        ports = str(api["ports"])
        assert "${APP_PORT" in ports or "8000" in ports

    def test_postgres_init_script_mount_readonly(self):
        """Postgres must mount SQL seed as read-only in /docker-entrypoint-initdb.d/."""
        with open(COMPOSE_PATH) as f:
            data = yaml.safe_load(f)
        pg = data["services"]["postgres"]
        assert "volumes" in pg, "postgres service must have volumes"
        volumes = pg["volumes"]
        # Find mount pointing to /docker-entrypoint-initdb.d/
        init_mounts = [v for v in volumes if "/docker-entrypoint-initdb.d/" in v]
        assert init_mounts, "postgres must have an init script mount in /docker-entrypoint-initdb.d/"
        # Assert it's read-only (:ro suffix)
        assert any(":ro" in m for m in init_mounts), "init script mount must be read-only (:ro)"
        # Assert seed file exists in project
        seed_path = PROJECT_ROOT / "SQL" / "deudores_morosos.sql"
        assert seed_path.exists(), f"Seed file must exist at {seed_path}"

    def test_postgres_persistent_volume_preserved(self):
        """Postgres must preserve the named volume postgres_data for persistence."""
        with open(COMPOSE_PATH) as f:
            data = yaml.safe_load(f)
        pg = data["services"]["postgres"]
        assert "volumes" in pg
        volumes = pg["volumes"]
        # Must have postgres_data volume for persistence
        assert any("postgres_data" in v for v in volumes), \
            "postgres must keep postgres_data volume for persistence"


class TestDockerfile:
    """Tests for Dockerfile structural validity."""

    def test_dockerfile_exists(self):
        """Dockerfile must exist in project root."""
        assert DOCKERFILE_PATH.exists()

    def test_exposes_port_8000(self):
        """Dockerfile must declare EXPOSE 8000."""
        with open(DOCKERFILE_PATH) as f:
            content = f.read()
        assert re.search(r"^\s*EXPOSE\s+8000", content, re.MULTILINE)

    def test_has_healthcheck_instruction(self):
        """Dockerfile must include a HEALTHCHECK instruction."""
        with open(DOCKERFILE_PATH) as f:
            content = f.read()
        assert "HEALTHCHECK" in content

    def test_no_sudo_or_root(self):
        """Dockerfile should not run as root (USER instruction present)."""
        with open(DOCKERFILE_PATH) as f:
            content = f.read()
        assert "USER" in content

    def test_copies_app_source(self):
        """Dockerfile must copy app source."""
        with open(DOCKERFILE_PATH) as f:
            content = f.read()
        assert "COPY app/" in content or "COPY app\\" in content


class TestEnvExample:
    """Tests for .env.example completeness."""

    def test_env_example_exists(self):
        """.env.example must exist."""
        assert ENV_EXAMPLE_PATH.exists()

    def test_includes_postgres_vars(self):
        """.env.example must include Postgres connection variables."""
        with open(ENV_EXAMPLE_PATH) as f:
            content = f.read()
        required = ["POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"]
        for var in required:
            assert var in content, f".env.example must include {var}"

    def test_includes_database_url(self):
        """.env.example must include DATABASE_URL."""
        with open(ENV_EXAMPLE_PATH) as f:
            content = f.read()
        assert "DATABASE_URL" in content

    def test_includes_rate_limit_vars(self):
        """.env.example must include rate limit variables."""
        with open(ENV_EXAMPLE_PATH) as f:
            content = f.read()
        required = ["RATE_LIMIT_ENABLED", "RATE_LIMIT_PER_MINUTE", "RATE_LIMIT_PER_IP", "RATE_LIMIT_PER_RUT"]
        for var in required:
            assert var in content, f".env.example must include {var}"

    def test_includes_utm_vars(self):
        """.env.example must include UTM conversion variables."""
        with open(ENV_EXAMPLE_PATH) as f:
            content = f.read()
        required = ["UTM_API_URL", "UTM_CACHE_TTL_SECONDS", "UTM_REQUEST_TIMEOUT_SECONDS"]
        for var in required:
            assert var in content, f".env.example must include {var}"
