"""Tests to validate the Postgres init-script bootstrap contract (one-shot first boot).

Postgres's /docker-entrypoint-initdb.d/ mechanism executes *.sql scripts exactly once:
when the data directory is empty. This test suite verifies the contract that the seed
is declarative, read-only and does not produce re-loads on subsequent starts.
"""
import pytest
import yaml
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_PATH = PROJECT_ROOT / "docker-compose.yml"
SEED_PATH = PROJECT_ROOT / "SQL" / "deudores_morosos.sql"
EXPECTED_SEED_MOUNT = "./SQL/deudores_morosos.sql:/docker-entrypoint-initdb.d/01-deudores_morosos.sql:ro"


class TestInitSeedContract:
    """Contract tests for Postgres one-shot bootstrap via docker-entrypoint-initdb.d."""

    def test_seed_file_exists(self):
        """The SQL seed file must exist in the project."""
        assert SEED_PATH.exists(), f"Seed file not found at {SEED_PATH}"
        assert SEED_PATH.is_file(), f"Seed path must be a file: {SEED_PATH}"

    def test_seed_file_not_empty(self):
        """The SQL seed file must contain actual content."""
        size = SEED_PATH.stat().st_size
        assert size > 0, "Seed SQL file must not be empty"

    def test_compose_declares_init_mount(self):
        """docker-compose.yml must mount the seed into Postgres's init script dir."""
        with open(COMPOSE_PATH) as f:
            data = yaml.safe_load(f)
        pg = data["services"]["postgres"]
        assert "volumes" in pg, "postgres must declare volumes"

        init_mounts = [v for v in pg["volumes"] if "/docker-entrypoint-initdb.d/" in v]
        assert init_mounts, (
            "Postgres must mount a script into /docker-entrypoint-initdb.d/. "
            "Expected: ./SQL/deudores_morosos.sql:/docker-entrypoint-initdb.d/01-deudores_morosos.sql:ro"
        )
        assert EXPECTED_SEED_MOUNT in pg["volumes"], (
            "postgres must declare the exact seed mount "
            "./SQL/deudores_morosos.sql:/docker-entrypoint-initdb.d/01-deudores_morosos.sql:ro"
        )

    def test_init_mount_is_readonly(self):
        """The init-script mount must be declared read-only ([:ro] suffix)."""
        with open(COMPOSE_PATH) as f:
            data = yaml.safe_load(f)
        pg = data["services"]["postgres"]
        init_mounts = [v for v in pg["volumes"] if "/docker-entrypoint-initdb.d/" in v]
        assert any(":ro" in m for m in init_mounts), \
            "Init-script mount must use :ro (read-only) flag"

    def test_persistent_volume_coexists_with_init_mount(self):
        """The postgres_data named volume must coexist with the init mount.

        Postgres's init mechanism runs only on first boot (empty data directory).
        The presence of postgres_data volume ensures data persists across restarts,
        preventing re-execution of init scripts on subsequent container starts.
        """
        with open(COMPOSE_PATH) as f:
            data = yaml.safe_load(f)
        pg = data["services"]["postgres"]
        assert "volumes" in pg
        volumes = pg["volumes"]

        # Must have postgres_data for persistence
        assert any("postgres_data" in v for v in volumes), \
            "postgres must declare postgres_data volume for persistence"

        # Must have init script mount
        init_mounts = [v for v in volumes if "/docker-entrypoint-initdb.d/" in v]
        assert init_mounts, "postgres must mount the seed SQL in /docker-entrypoint-initdb.d/"

    def test_init_script_naming_convention(self):
        """Init scripts should follow Postgres convention (alphabetical prefix ordering)."""
        with open(COMPOSE_PATH) as f:
            data = yaml.safe_load(f)
        pg = data["services"]["postgres"]
        init_mounts = [v for v in pg["volumes"] if "/docker-entrypoint-initdb.d/" in v]
        # Should use a numeric prefix for deterministic execution order
        assert any("01-" in m or "001-" in m for m in init_mounts), \
            "Init script name should start with a numeric prefix (e.g. 01-) for execution order"
