import datetime
from pathlib import Path
import unittest

from gist.netai.time_travel_summarization.app_config import ExtensionConfig
from gist.netai.time_travel_summarization.playback_controller import PlaybackController
from gist.netai.time_travel_summarization.trajectory_repository import TrajectoryRepository


class RefactoringSmokeTest(unittest.TestCase):
    def test_extension_config_loads_current_package_shape(self):
        config_path = Path(__file__).resolve().parents[1] / "config.json"
        config = ExtensionConfig.from_file(str(config_path))

        self.assertTrue(config.data_path.endswith(".csv"))
        self.assertIsInstance(config.prim_map, dict)

    def test_trajectory_repository_returns_last_known_value(self):
        repository = TrajectoryRepository()
        csv_path = Path(__file__).resolve().parents[1] / "data" / "living_trajectory_1min_0.2s.csv"

        self.assertTrue(repository.load_csv(csv_path))
        between = datetime.datetime(2025, 1, 1, 0, 0, 0, 100000)
        data = repository.get_data_at_time(between)

        self.assertTrue(data)

    def test_playback_controller_clamps_progress_into_range(self):
        playback = PlaybackController()
        start = datetime.datetime(2025, 1, 1, 0, 0, 0)
        end = datetime.datetime(2025, 1, 1, 0, 0, 10)
        playback.configure_data_range(start, end)

        playback.set_progress(2.0)

        self.assertEqual(playback.get_current_time(), end)


if __name__ == "__main__":
    unittest.main()
