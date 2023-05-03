import re
import json
from pathlib import Path
from typing import Optional

from lxml import etree

tree = etree.parse("opm-flow-documentation-2021-04-rev-0.xml")
root = tree.getroot()

toc_sections = {
    "GLOBAL": (4, 2),
    "RUNSPEC": (5, 2),
    "GRID": (6, 3),
    "EDIT": (7, 3),
    "PROPS": (8, 3),
    "REGIONS": (9, 3),
    "SOLUTION": (10, 3),
    "SUMMARY": (11, 3),
    "SCHEDULE": (12, 3),
}

compiled_regex = {
    section: re.compile(f"^{chapter[0]}\.{chapter[1]}\.[0-9]+ ")
    for section, chapter in toc_sections.items()
}


def belongs_to_keyword_section(toc_entry: str) -> Optional[str]:
    for section, compiled_pattern in compiled_regex.items():
        if compiled_pattern.match(toc_entry):
            return section


keyword_links = {}
for child in root.findall(".//*{urn:oasis:names:tc:opendocument:xmlns:text:1.0}a"):
    section = belongs_to_keyword_section(child.text) if child.text else None
    if section:
        try:
            [_, keyword, _, short_description] = child.text.strip().split(maxsplit=3)
            link = child.attrib["{http://www.w3.org/1999/xlink}href"].lstrip("#")
            keyword_links[link] = {
                "keyword": keyword,
                "section": section,
                "short_description": short_description,
            }
        except ValueError:
            print(f"ERROR parsing following table of content entry: {child.text}")

for child in root.findall(
    ".//*{urn:oasis:names:tc:opendocument:xmlns:text:1.0}bookmark-start"
):
    link = child.attrib["{urn:oasis:names:tc:opendocument:xmlns:text:1.0}name"]

    if link in keyword_links:
        sibling = child.getparent().getnext()
        keyword_links[link]["long_description"] = "".join(
            [t for t in sibling.getnext().getnext().itertext()]
        )

Path("eclipse_keyword_documentation.json").write_text(
    json.dumps(list(keyword_links.values()), indent=4)
)
