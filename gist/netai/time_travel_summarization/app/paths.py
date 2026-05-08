from pathlib import Path


class ExtensionPaths:
    def __init__(self, module_dir: Path):
        self._module_dir = module_dir
        self._artifacts_dir = module_dir / "artifacts"

    @property
    def artifacts_dir(self) -> Path:
        self._artifacts_dir.mkdir(exist_ok=True)
        return self._artifacts_dir

    @property
    def videos_dir(self) -> Path:
        path = self.artifacts_dir / "video"
        path.mkdir(exist_ok=True)
        return path

    @property
    def vlm_outputs_dir(self) -> Path:
        path = self.artifacts_dir / "vlm_outputs"
        path.mkdir(exist_ok=True)
        return path

    @property
    def intermediate_results_dir(self) -> Path:
        path = self.artifacts_dir / "intermediate_results"
        path.mkdir(exist_ok=True)
        return path

    @property
    def event_list_dir(self) -> Path:
        path = self.artifacts_dir / "event_list"
        path.mkdir(exist_ok=True)
        return path

    def resolve_input_file(self, subdir: str, filename: str) -> Path:
        artifact_path = self.artifacts_dir / subdir / filename
        if artifact_path.exists():
            return artifact_path
        return self._module_dir / subdir / filename
