from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from constants import NO_DATA_GRAPH_VALUE
from graphs import call_graph_creator, create_graph_async, create_graph_sync


class TestGraphs:
    def test_create_graph_sync_creates_file(self, tmp_path):
        categories = ["Food", "Transport"]
        values = [100.0, 50.0]
        graph_name = "test_graph.png"

        with patch("graphs.os.makedirs"):
            with patch("graphs.plt.savefig") as mock_save:
                result = create_graph_sync(categories, values, graph_name)
                assert result == f"graphs/{graph_name}"
                mock_save.assert_called_once()

    def test_create_graph_sync_handles_exception(self):
        categories = ["Food"]
        values = [100.0]
        graph_name = "test.png"

        with patch("graphs.os.makedirs"):
            with patch("graphs.plt.figure", side_effect=Exception("Test error")):
                with pytest.raises((OSError, ValueError, RuntimeError)):
                    create_graph_sync(categories, values, graph_name)

    @pytest.mark.asyncio
    async def test_create_graph_async(self):
        categories = ["Food", "Transport"]
        values = [100.0, 50.0]

        with patch("graphs.asyncio.get_running_loop") as mock_loop:
            mock_executor = MagicMock()
            mock_executor.return_value = "graphs/test_graph.png"
            mock_loop.return_value.run_in_executor = AsyncMock(
                return_value="graphs/test_graph.png"
            )

            result = await create_graph_async(categories, values)
            assert result == "graphs/test_graph.png"

    @pytest.mark.asyncio
    async def test_create_graph_async_handles_exception(self):
        categories = ["Food"]
        values = [100.0]

        with patch("graphs.asyncio.get_running_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(
                side_effect=Exception("Test error")
            )

            with pytest.raises((OSError, ValueError, RuntimeError)):
                await create_graph_async(categories, values)

    @pytest.mark.asyncio
    async def test_call_graph_creator_no_data(self):
        all_values = []
        with patch("graphs.create_graph_async") as mock_create:
            mock_create.return_value = "graphs/test.png"
            await call_graph_creator(all_values)
            mock_create.assert_called_once()
            call_args = mock_create.call_args[0]

            assert call_args[0] == ["No Data"]
            assert call_args[1] == [NO_DATA_GRAPH_VALUE]

    @pytest.mark.asyncio
    async def test_call_graph_creator_groups_small_categories(self):
        all_values = [
            ("food_out", 50.0),
            ("transport", 30.0),
            ("gifts", 1.5),
            ("debts", 0.5),
        ]

        with patch("graphs.create_graph_async") as mock_create:
            mock_create.return_value = "graphs/test.png"
            await call_graph_creator(all_values)

            call_args = mock_create.call_args[0]
            categories = call_args[0]
            values = call_args[1]

            assert "Fast Food" in categories
            assert "Transport" in categories
            assert "Miscellaneous" in categories
            assert 50.0 in values
            assert 30.0 in values
            assert 2.0 in values

    @pytest.mark.asyncio
    async def test_call_graph_creator_with_miscellaneous_already_exists(self):
        all_values = [
            ("other", 50.0),
            ("gifts", 1.0),
        ]

        with patch("graphs.create_graph_async") as mock_create:
            mock_create.return_value = "graphs/test.png"
            await call_graph_creator(all_values)

            call_args = mock_create.call_args[0]
            categories = call_args[0]
            values = call_args[1]

            misc_index = categories.index("Miscellaneous")
            assert values[misc_index] == 51.0  # 50.0 + 1.0

    @pytest.mark.asyncio
    async def test_call_graph_creator_handles_exception(self):
        all_values = [("food_out", 50.0)]

        with patch("graphs.create_graph_async", side_effect=Exception("Test error")):
            with pytest.raises((OSError, ValueError, RuntimeError)):
                await call_graph_creator(all_values)
