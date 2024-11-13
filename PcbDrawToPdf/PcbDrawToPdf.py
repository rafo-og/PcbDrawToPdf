#!/usr/bin/env python3

from __future__ import annotations

import os
import subprocess
from typing import Dict
from lxml import etree
from copy import deepcopy


class PcbDrawSvg:
    """
    A class to handle and manipulate SVG files for PCB drawings.

    Attributes:
        filepath (str): The file path of the SVG file.
        filename (str): The name of the SVG file.
        folder (str): The folder containing the SVG file.
        ext (str): The file extension of the SVG file.
        root (etree.Element): The root element of the SVG file.
        board (etree.Element): The board element of the SVG file.
        masks (Dict[str, etree.Element]): Dictionary to store mask elements.
    """

    filepath: str
    filepath_saved: str
    filename: str
    folder: str
    ext: str

    xml: etree.ElementTree
    root: etree.Element
    masks: Dict[str, etree.Element]

    ns = {
        "": "http://www.w3.org/2000/svg",
        "sodipodi": "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd",
        "xlink": "http://www.w3.org/1999/xlink",
    }

    def __init__(self) -> None:
        """
        Initializes the PcbDrawSvg object.
        """
        self.masks = {}

    def __store_metadata(self, filepath: str) -> None:
        """
        Stores metadata about the file.

        Args:
            filepath (str): The path to the file.
        """
        self.filepath = filepath
        self.folder = os.path.dirname(self.filepath)
        self.filename = os.path.basename(self.filepath)
        self.filename, self.ext = (
            os.path.splitext(self.filename)[0],
            os.path.splitext(self.filename)[-1],
        )
        self.filepath_saved = os.path.join(
            self.folder, self.filename + "_saved" + self.ext
        )

    def __inkscape_clean(self):
        cmd = [
            "C:/Program Files/Inkscape/bin/inkscape.exe",
            "--export-plain-svg",
            "--export-text-to-path",
            "--vacuum-defs",
            "-o",
            self.filepath_saved,
            self.filepath,
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE)

    def load(self, filepath: str) -> None:
        """
        Loads the SVG file and parses its content.

        Args:
            filepath (str): The path to the SVG file.
        """
        self.__store_metadata(filepath)
        self.__inkscape_clean()
        self.xml = etree.parse(self.filepath_saved)
        self.root = self.xml.getroot()

    def save(self, outfile: str = None):
        self.clean()
        etree.indent(self.xml, space="\t", level=0)
        if outfile is None:
            filepath = self.filepath_saved
        else:
            filepath = outfile
            os.remove(self.filepath_saved)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self.xml.write(filepath, xml_declaration=True, encoding="utf-8", method="xml")

    def convert(self):
        mask_group = etree.Element("g", attrib={"id": "masks"})
        self.root.insert(0, mask_group)
        # Move masks to a new group
        for mask in self.root.findall("defs/mask", self.ns):
            mask_name = mask.attrib["id"]
            self.masks[mask_name] = mask
            self.masks[mask_name].tag = "g"
            mask_group.append(self.masks[mask_name])
        # Remove attributes using the masks
        for elem in self.root.iterfind(".//*[@mask]", self.ns):
            elem.attrib["id"] = elem.attrib["id"] + "_" + elem.attrib["mask"]
            del elem.attrib["mask"]
        # Remove the defs section
        elem = self.root.find("./defs", self.ns)
        self.root.remove(elem)
        # Clean board container
        board = self.root.find("./g[@id='boardContainer']", self.ns)
        substrate = board.find("./g[@id='substrate_url(#hole-mask)']", self.ns)
        for child in substrate:
            board.append(child)
        board.remove(substrate)
        board.attrib["id"] = board.attrib["id"] + "_url(#hole-mask)"

    def clean(self):
        for parent in self.root.iterfind("./title/..", self.ns):
            for elem in self.root.iterfind("./title", self.ns):
                parent.remove(elem)
        for parent in self.root.iterfind("./desc/..", self.ns):
            for elem in self.root.iterfind("./desc", self.ns):
                parent.remove(elem)
