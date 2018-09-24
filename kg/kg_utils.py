__author__ = "Pierre-Alexandre Fonta"
__maintainer__ = "Pierre-Alexandre Fonta"

import copy
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Any, Dict, Tuple, Iterable


JSON = Dict[str, Any]


def find(uuid: str, data: Iterable[JSON], uuid_field: str = "providerId") -> Optional[JSON]:
    found = next(x for x in data if x[uuid_field] == uuid)
    if found:
        return found
    else:
        return None


def prepare(data: JSON, replacements: List[Tuple[str, str]]) -> str:
    _str = json.dumps(data, indent=2)
    for old, new in replacements:
        _str = _str.replace(old, new)
    return _str


def remove_empty_values(data: JSON) -> None:
    for key, value in data.copy().items():
        if isinstance(value, dict):
            remove_empty_values(value)
        elif isinstance(value, list) and value:
            for x in value:
                if isinstance(value, dict):
                    remove_empty_values(x)
        elif isinstance(value, (str, list)) and not value:
            del data[key]


@dataclass
class TestDataConfiguration:

    organization: str
    neuroshapes_dir: str
    replacements: List[Tuple[str, str]] = field(default_factory=list)
    valid_data_path: Path = field(init=False)
    invalid_data_path: Path = field(init=False)

    def __post_init__(self):
        part_1 = Path(self.neuroshapes_dir, "modules", self.organization, "src/test/resources")
        part_2 = Path("neurosciencegraph", self.organization)
        self.valid_data_path = part_1 / "data" / part_2
        self.invalid_data_path = part_1 / "invalid" / part_2

    def write(self, data: JSON, schema_name: str, schema_version: str,
              optional_properties: List[str], flavour: str = None) -> None:
        # Avoid copyright issues.
        try:
            del data["hasTarget"]["hasSelector"]["text"]
        except KeyError:
            pass

        min_data = data.copy()

        for x in optional_properties:
            del min_data[x]

        name_template = "auto-{}-fields"
        filename = name_template.format("all")
        min_filename = name_template.format("min")

        if flavour is not None:
            filename += f"-{flavour}"
            min_filename += f"-{flavour}"

        schema_test_path = self.valid_data_path / schema_name / schema_version

        file_path = schema_test_path / f"{filename}.json"
        min_file_path = schema_test_path / f"{min_filename}.json"

        prepared_data = prepare(data, self.replacements)
        prepared_min_data = prepare(min_data, self.replacements)

        with file_path.open("w") as f:
            f.write(prepared_data)
            self._print_written(file_path, self.valid_data_path)

        with min_file_path.open("w") as f:
            f.write(prepared_min_data)
            self._print_written(min_file_path, self.valid_data_path)

    def write_missing(self, schema_name: str, schema_version: str, base_filename: str,
                      config: List[Tuple[str, str]]) -> None:
        schema_path = Path(schema_name, schema_version)
        min_file_path = self.valid_data_path / schema_path / f"{base_filename}.json"

        with min_file_path.open("r") as f1:
            data = json.load(f1)

            for key, name in config:
                dcopy = copy.deepcopy(data)

                if "." in key:
                    splits = key.split(".")
                    cmd = "del dcopy[\"" + "\"][\"".join(splits) + "\"]"
                    exec(cmd)
                else:
                    del dcopy[key]

                filename = f"auto-missing-{name}.json"
                missing_file_path = self.invalid_data_path / schema_path / filename

                with missing_file_path.open("w") as f2:
                    _str = json.dumps(dcopy, indent=2)
                    f2.write(_str)
                    self._print_written(missing_file_path, self.invalid_data_path)

    @staticmethod
    def _print_written(full_path: Path, base_path: Path) -> None:
        print("<written>", full_path.relative_to(base_path))
