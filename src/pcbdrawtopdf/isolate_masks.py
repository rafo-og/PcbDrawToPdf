#!/usr/bin/env python3

from __future__ import annotations

import os
import subprocess
from typing import Dict
from lxml import etree
from copy import deepcopy

etree.register_namespace("xlink", "http://www.w3.org/1999/xlink")


class PcbDrawSvg:

    filepath: str
    filename: str
    folder: str
    ext: str

    root: etree.Element
    board: etree.Element

    masks: Dict[str, etree.Element]

    def __init__(self) -> None:
        self.masks = {}

    def store_metadata(self, filepath: str) -> None:
        self.filepath = filepath
        self.folder = os.path.dirname(self.filepath)
        self.filename = os.path.basename(self.filepath)
        self.filename, self.ext = (
            os.path.splitext(self.filename)[0],
            os.path.splitext(self.filename)[-1],
        )

    def to_inkscape_svg(self, filepath: str) -> None:
        subprocess.run(
            [
                "inkscape",
                "--export-overwrite",
                "--actions=export-do",
                filepath
            ]
        )

    def check_inkscape(self) -> None:
        if "svg" in self.root_orig.nsmap.keys():
            return True
        else:
            return False

    def load(self, filepath: str) -> None:
        self.store_metadata(filepath)
        self.root_orig = etree.parse(self.filepath).getroot()
        if not self.check_inkscape():
            self.to_inkscape_svg(filepath)
            self.root_orig = etree.parse(self.filepath).getroot()
        self.root = deepcopy(self.root_orig)
        self.get_board()

    def save_elem(self, element: etree.Element, outfile: str) -> None:
        tree = etree.ElementTree(element)
        tree.write(outfile, xml_declaration=True)

    def save(self, outfile: str) -> None:
        self.save_elem(self.root, outfile)

    def reset(self) -> None:
        self.root = deepcopy(self.root_orig)
        self.get_board()

    def get_id(self, id: str) -> etree.Element:
        elem = self.root.xpath(f'.//*[@id="{id}"]')[0]
        return elem

    def get_board(self) -> None:
        self.board = self.get_id("boardContainer")
        return self.board

    def get_tag(self, tag: str, ns: str = "svg") -> str:
        return "{" + self.root.nsmap[ns] + "}" + tag

    def rm_tag(
        self,
        elem: etree.Element,
        tag: str,
        ns: str = "svg",
        recursive: bool = False,
        remove_parent: bool = False,
    ) -> etree.Element:
        gtag = self.get_tag(tag, ns)
        if recursive:
            groups = elem.findall(f".//{gtag}")
        else:
            groups = elem.findall(f"./{gtag}")
        for group in groups:
            elem = group.getparent()
            parent = elem.getparent()
            if remove_parent and parent is not None:
                parent.remove(elem)
            else:
                elem.remove(group)
        return elem

    def rm_attr(self, elem: etree.Element, attr: str) -> etree.Element:
        xpath_attr = f".//*[@{attr}]"
        groups = elem.xpath(xpath_attr)
        for group in groups:
            group.attrib["id"] = group.attrib["id"] + "_" + group.attrib[attr]
            del group.attrib[attr]
        return elem

    def get_masks(self) -> None:
        self.get_mask("hole-mask")
        self.get_mask("pads-mask-silkscreen")
        self.get_mask("pads-mask")

    def get_mask(self, mask_name: str) -> None:
        gtag = self.get_tag("g")
        self.masks[mask_name] = deepcopy(self.get_id(mask_name))
        self.masks[mask_name].tag = gtag
        self.masks[mask_name].text = ''
        self.masks[mask_name].tail = ''

    def rm_ink_elem(self) -> None:
        self.rm_tag(self.root, "namedview", "sodipodi")
        self.rm_tag(self.root, "desc")

    def isolate_board(self) -> None:
        elem = self.get_id("componentContainer")
        self.root.remove(elem)
        elem = self.get_board()
        elem = self.rm_tag(elem, "g")
        elem = self.rm_tag(elem, "mask", recursive=True, remove_parent=True)
        self.rm_attr(self.root, "mask")

    def rm_masks(self) -> None:
        self.rm_attr(self.root, "mask")
        self.rm_tag(self.root, "mask", recursive=True)
        self.rm_ink_elem()

    def add_mask_patterns(self) -> None:
        self.rm_ink_elem()
        board = self.get_board()
        if len(board) == 0:
            raise Exception("The board hasn not elements.")
        for name, mask in self.masks.items():
            board.insert(-1, mask)

    def save_mask_files(self, outpath: str) -> None:
        for name, mask in self.masks.items():
            board = self.get_board()
            board.append(mask)
            filepath = os.path.join(outpath, self.filename + "_" + name + self.ext)
            self.save(filepath)
            board.remove(mask)


def main_convert():
    FILENAME = (
        "C:/VSCODE/THESIS_DISSERTATION/PcbDrawToPdf/test/ArduinoLearningKitStarter.svg"
    )
    OUTPUT = (
        "C:/VSCODE/THESIS_DISSERTATION/PcbDrawToPdf/test/"
        "ArduinoLearningKitStarter_exp_mask.svg"
    )
    svg = PcbDrawSvg()
    svg.load(FILENAME)
    svg.get_masks()
    svg.rm_masks()
    svg.add_mask_patterns()
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    svg.save(OUTPUT)


def main_extract_mask():
    FILENAME = (
        "C:/VSCODE/THESIS_DISSERTATION/PcbDrawToPdf/test/ArduinoLearningKitStarter.svg"
    )
    OUTPUT = "C:/VSCODE/THESIS_DISSERTATION/PcbDrawToPdf/tmp/"
    svg = PcbDrawSvg()
    svg.load(FILENAME)
    svg.get_masks()
    svg.isolate_board()
    svg.rm_masks()
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    svg.save_mask_files(OUTPUT)


if __name__ == "__main__":
    main_convert()
    main_extract_mask()
