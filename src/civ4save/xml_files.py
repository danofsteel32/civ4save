"""
xml_files.py
This module is responsible for reading the Civ4 XML files and transforming them
into python Enums.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Generator, Optional

import xmltodict
from jinja2 import Template

from civ4save.utils import get_game_dir


def get_n_parents(path: Path, num: int) -> Path:
    path = path.resolve()
    name = path.name
    parents = []
    for n in range(num):
        path = path.parent
        if not path.name:
            break
        parents.append(path.name)
    return Path(parents[-1]).joinpath(*reversed(parents[:-1])) / name


@dataclass
class Civ4XmlFile:
    path: Path
    _parsed: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.path.suffix == ".xml":
            raise ValueError(f"{get_n_parents(self.path, 4)} not a xml file")

    def __str__(self) -> str:
        return str(get_n_parents(self.path, 4))

    @property
    def name(self):
        return self.path.name

    @property
    def enum_name(self):
        name = self.path.stem.replace("Infos", "")
        name = name.replace("CIV4", "")
        name = name.replace("Info", "")
        name = name.replace("_", "")
        return name + "Type"

    @property
    def negative_one(self):
        name = re.sub(r'(?<!^)(?=[A-Z])', '_', self.enum_name)
        return "NO_" + name.replace("_Type", "").upper()

    @property
    def parent_category(self) -> Optional[str]:
        parent = self.path.parent.name
        if self.path.parent.name == "XML":
            return None
        return parent

    @property
    def root_key(self) -> str:
        if not self._parsed:
            self.read()
        return [key for key in self._parsed].pop()

    def types(self):
        root = self._parsed[self.root_key]
        key = list(root.keys())[-1]
        names = [(self.negative_one, -1)]
        for n, entry in enumerate(root[key][key[:-1]]):
            names.append((entry["Type"], n))
        return names

    def to_enum(self):
        return Enum(self.enum_name, self.types())

    def read(self) -> dict:
        if not self.path.exists():
            raise FileNotFoundError(f"{self.path} does not exist!")
        with open(self.path, "r") as xml_file:
            self._parsed = xmltodict.parse(xml_file.read())
        return self._parsed


def xml_files_iter() -> Generator[Civ4XmlFile, None, None]:
    """
    Generator yielding every XML file that isn't a Schema or Text type.
    BTS and Warlords files take precendence over vanilla.
    Example:
        if both <BTS path>/CIV4BuildingInfos.xml, <Vanilla path>/CIV4BuildingInfos.xml
            only yield the BTS one
    """

    # TODO replace the ugliness with a glob** of some kind
    game_dir = get_game_dir()
    vanilla_xml = game_dir / "Assets" / "XML"
    warlords_xml = game_dir / "Warlords" / "Assets" / "XML"
    bts_xml = game_dir / "Beyond the Sword" / "Assets" / "XML"

    seen = set()
    for xml_dir in [bts_xml, warlords_xml, vanilla_xml]:
        if not xml_dir.exists():
            continue
        for file_or_dir in xml_dir.iterdir():
            if file_or_dir.is_dir():
                for file in file_or_dir.iterdir():
                    if (
                        "Schema" not in file.name
                        and "Text" not in file.name
                        and file.name not in seen
                    ):
                        seen.add(file.name)
                        yield Civ4XmlFile(file)
            else:
                if (
                    "Schema" not in file_or_dir.name
                    and "Text" not in file_or_dir.name
                    and file_or_dir.name not in seen
                ):
                    seen.add(file_or_dir.name)
                    yield Civ4XmlFile(file_or_dir)


def write_out_enum(e) -> None:
    """Writes to stdout, use > to save to file"""
    data = {
        "enum_name": e.__name__,
        "members": [{"name": m, "value": e[m].value} for m in e.__members__],
    }
    template = """
class {{ enum_name }}(Enum):
    {%- for m in members %}
    {{ m.name }} = {{ m.value }}
    {%- endfor -%}
{{ '\n' }}
"""

    j2_template = Template(template)
    print(j2_template.render(data))


def make_enums() -> None:
    """Writes to stdout, use > to save to file"""
    print("from enum import Enum")
    print()
    for xml_file in xml_files_iter():
        try:
            xml_file.read()
        except UnicodeDecodeError:
            continue
        try:
            write_out_enum(xml_file.to_enum())
        except:
            continue


if __name__ == "__main__":
    make_enums()
