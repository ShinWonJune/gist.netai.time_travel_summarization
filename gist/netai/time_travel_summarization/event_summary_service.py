import json
from pathlib import Path
from typing import Dict, List, Tuple


class EventSummaryService:
    def __init__(self, module_dir: Path, repository):
        self._module_dir = module_dir
        self._repository = repository
        self._event_positions: Dict[str, Tuple[float, float, float]] = {}

    def get_event_position(self, timestamp: str):
        return self._event_positions.get(timestamp)

    def load_events_from_event_list(self) -> List[str]:
        eventlist_dir = self._module_dir / "event_list"
        if not eventlist_dir.exists():
            return []

        eventlist_files = list(eventlist_dir.glob("*_eventlist.jsonl"))
        if not eventlist_files:
            return []

        latest_file = max(eventlist_files, key=lambda path: path.stat().st_mtime)
        event_timestamps: List[str] = []
        event_positions: Dict[str, Tuple[float, float, float]] = {}

        with open(latest_file, "r", encoding="utf-8") as file:
            for line in file:
                entry = json.loads(line)
                timestamp = entry.get("timestamp")
                position = entry.get("position")
                if not timestamp or not position:
                    continue

                event_timestamps.append(timestamp)
                event_positions[timestamp] = (
                    position.get("x", 0),
                    position.get("y", 0),
                    position.get("z", 0),
                )

        self._event_positions = event_positions
        return event_timestamps

    def process_event_json(self, json_path: str) -> bool:
        from .event_post_processing_core import consolidate_events, load_json, save_jsonl

        source_path = Path(json_path)
        if not source_path.exists():
            return False

        vlm_data = load_json(str(source_path))
        events = consolidate_events(vlm_data, base_date="2025-01-01")

        processed_dir = source_path.parent.parent / "intermediate_results"
        processed_dir.mkdir(exist_ok=True)
        output_jsonl = processed_dir / f"{source_path.stem}_intermediate.jsonl"
        save_jsonl(events, str(output_jsonl))

        event_list = self._generate_event_list(events)
        if not event_list:
            return False

        event_list_dir = source_path.parent.parent / "event_list"
        event_list_dir.mkdir(exist_ok=True)
        output_eventlist = event_list_dir / f"{source_path.stem}_eventlist.jsonl"

        with open(output_eventlist, "w", encoding="utf-8") as file:
            for entry in event_list:
                file.write(json.dumps(entry, ensure_ascii=False) + "\n")

        self._event_positions = {
            entry["timestamp"]: (
                entry["position"]["x"],
                entry["position"]["y"],
                entry["position"]["z"],
            )
            for entry in event_list
        }
        return True

    def _generate_event_list(self, events: Dict[str, List[List[str]]]) -> List[Dict]:
        position_data = []
        for timestamp, obj_pairs in events.items():
            if not obj_pairs or not obj_pairs[0]:
                continue

            first_objid = obj_pairs[0][0]
            time_obj = self._repository.parse_timestamp(timestamp)
            time_data = self._repository.get_data_at_time(time_obj)
            if first_objid not in time_data:
                continue

            x, y, z = time_data[first_objid]
            position_data.append(
                {
                    "timestamp": timestamp,
                    "objid": first_objid,
                    "position": {"x": x, "y": y, "z": z},
                }
            )

        return position_data
