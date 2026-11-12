import pytest
from packaging.version import Version

from pip_audit._dependency_source import DependencyFixError, DependencySourceError, PyLockSource
from pip_audit._fix import ResolvedFixVersion
from pip_audit._service import ResolvedDependency, SkippedDependency


class TestPyLockSource:
    def test_basic(self, asset):
        pylock = asset("pylock.basic.toml")
        source = PyLockSource([pylock])

        deps = list(source.collect())
        assert deps == [
            ResolvedDependency(name="attrs", version=Version("25.1.0")),
            ResolvedDependency(name="cattrs", version=Version("24.1.2")),
            ResolvedDependency(name="numpy", version=Version("2.2.3")),
        ]

    def test_skipped(self, asset):
        pylock = asset("pylock.skipped.toml")
        source = PyLockSource([pylock])

        deps = list(source.collect())
        assert deps == [SkippedDependency(name="attrs", skip_reason="no version specified")]

    @pytest.mark.parametrize(
        ("name", "error"),
        [
            ("pylock.invalid.toml", "invalid TOML in lockfile"),
            ("pylock.missing-version.toml", "missing lock-version in lockfile"),
            ("pylock.invalid-version.toml", "lockfile version 666 is not supported"),
            ("pylock.missing-packages.toml", "missing packages in lockfile"),
            ("pylock.package-missing-name.toml", "invalid package #0: no name"),
        ],
    )
    def test_invalid_pylock(self, asset, name, error):
        pylock = asset(name)
        source = PyLockSource([pylock])

        with pytest.raises(DependencySourceError, match=error):
            list(source.collect())

    def test_fix_not_supported(self, asset):
        # Lockfiles are managed by their packaging tool, so `pip-audit`
        # refuses to rewrite them. The failure must be a `DependencyFixError`
        # (not a bare `NotImplementedError`) so that the CLI can skip the fix
        # gracefully and continue with any remaining ones.
        pylock = asset("pylock.basic.toml")
        source = PyLockSource([pylock])

        with pytest.raises(DependencyFixError, match="lockfiles cannot be fixed directly"):
            source.fix(
                ResolvedFixVersion(
                    dep=ResolvedDependency(name="attrs", version=Version("25.1.0")),
                    version=Version("25.2.0"),
                )
            )
