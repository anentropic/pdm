"""Test for git dependencies with subdirectory parameter.

This test performs real git operations (not mocked) to verify that
git dependencies with subdirectory parameter work correctly on all platforms,
including Windows where different ref formats may be required.
"""
import pytest


@pytest.mark.integration
@pytest.mark.network
def test_git_dependency_with_subdirectory(pdm, project, tmp_path):
    """Test pdm sync and lock with a real git dependency that has a subdirectory parameter.
    
    This test verifies the specific case mentioned in the issue:
    git+https://github.com/user/repo.git@branch#subdirectory=subdir
    
    It performs actual git clone operations to test cross-platform compatibility,
    particularly for Windows where @refs/heads/branch may be required.
    """
    # Configure the test project with git dependency with subdirectory
    project.project_config["python.use_venv"] = True
    
    # Set up pyproject.toml with the specific dependency from the issue
    project.pyproject.set_data({
        "project": {
            "name": "test-git-subdirectory",
            "version": "0.1.0",
            "requires-python": ">=3.10",
            "dependencies": [
                "dbt-core>=1.10.11",
                "dbt-snowflake @ git+https://github.com/ifm-pgarner/dbt-adapters.git@ifm#egg=dbt-snowflake&subdirectory=dbt-snowflake",
            ],
        },
        "build-system": {
            "requires": ["pdm-backend"],
            "build-backend": "pdm.backend",
        },
    })
    project.pyproject.write()
    
    # Test pdm lock - this should resolve and lock the dependencies
    result = pdm(["lock", "-v"], obj=project, strict=True)
    assert result.exit_code == 0, f"pdm lock failed: {result.stderr}"
    assert project.lockfile.exists(), "Lock file was not created"
    
    # Verify the git dependency is in the lockfile
    lockfile_packages = project.lockfile["package"]
    dbt_snowflake = next((p for p in lockfile_packages if p.get("name") == "dbt-snowflake"), None)
    assert dbt_snowflake is not None, "dbt-snowflake not found in lockfile"
    assert "git" in dbt_snowflake, "dbt-snowflake should be a git dependency"
    assert "subdirectory" in dbt_snowflake, "subdirectory parameter not preserved"
    assert dbt_snowflake["subdirectory"] == "dbt-snowflake", "subdirectory value incorrect"
    
    # Test pdm sync - this should install the dependencies
    result = pdm(["sync", "-v"], obj=project, strict=True)
    assert result.exit_code == 0, f"pdm sync failed: {result.stderr}"
    
    # Verify installation
    installed = project.environment.get_working_set()
    assert "dbt-snowflake" in installed, "dbt-snowflake was not installed"
    assert "dbt-core" in installed, "dbt-core was not installed"
