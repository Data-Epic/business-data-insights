import pytest
import sys
from unittest.mock import patch, MagicMock

from src import pipeline


def test_apply_migrations_success():
    """Test that migrations are applied successfully using Alembic's command API."""
    with patch("src.pipeline.Config") as mock_config_class, \
         patch("src.pipeline.command.upgrade") as mock_upgrade:
        
        # Setup mock return value for Config
        mock_cfg_instance = MagicMock()
        mock_config_class.return_value = mock_cfg_instance

        pipeline.apply_migrations()

        mock_config_class.assert_called_once()
        mock_upgrade.assert_called_once_with(mock_cfg_instance, "head")


def test_apply_migrations_failure():
    """Test that an exception in Alembic upgrades propagates upward."""
    with patch("src.pipeline.Config"), \
         patch("src.pipeline.command.upgrade", side_effect=Exception("Alembic error")):
        
        with pytest.raises(Exception, match="Alembic error"):
            pipeline.apply_migrations()


@patch("src.pipeline.run_aggregations")
@patch("src.pipeline.load_parquet_to_dw")
@patch("src.pipeline.apply_migrations")
@patch("src.pipeline.run_cleaning_pipeline")
def test_run_pipeline_success(mock_clean, mock_migrate, mock_load, mock_aggregate):
    """Test that all pipeline phases are called in the correct sequential order."""
    pipeline.run_pipeline()

    mock_clean.assert_called_once()
    mock_migrate.assert_called_once()
    mock_load.assert_called_once()
    mock_aggregate.assert_called_once()


@patch("src.pipeline.sys.exit")
@patch("src.pipeline.run_cleaning_pipeline", side_effect=Exception("Extraction Failed"))
@patch("src.pipeline.apply_migrations")
@patch("src.pipeline.load_parquet_to_dw")
@patch("src.pipeline.run_aggregations")
def test_run_pipeline_failure_exits(mock_aggregate, mock_load, mock_migrate, mock_clean, mock_exit):
    """Test that a failure in any step aborts the pipeline and exits with status 1."""
    pipeline.run_pipeline()

    # Ensure it failed at the first step
    mock_clean.assert_called_once()
    
    # Ensure downstream steps were NOT executed
    mock_migrate.assert_not_called()
    mock_load.assert_not_called()
    mock_aggregate.assert_not_called()
    
    # Ensure system exit was triggered
    mock_exit.assert_called_once_with(1)