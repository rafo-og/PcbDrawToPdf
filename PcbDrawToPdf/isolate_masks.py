#!/usr/bin/env python3

from __future__ import annotations

import os
import subprocess
from typing import Dict
from lxml import etree
from copy import deepcopy

etree.register_namespace("xlink", "http://www.w3.org/1999/xlink")


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
    filename: str
    folder: str
    ext: str

    root: etree.Element
    board: etree.Element

    masks: Dict[str, etree.Element]

    def __init__(self) -> None:
        """
        Initializes the PcbDrawSvg object.
        """
        self.masks = {}

    def store_metadata(self, filepath: str) -> None:
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

    def to_inkscape_svg(self, filepath: str) -> None:
        """
        Converts the SVG file to an Inkscape-compatible SVG format.

        Args:
            filepath (str): The path to the SVG file.
        """
        subprocess.run(
            ["inkscape", "--export-overwrite", "--actions=export-do", filepath]
        )

    def check_inkscape(self) -> None:
        """
        Checks if the SVG file is compatible with Inkscape.

        Returns:
            bool: True if compatible, False otherwise.
        """
        if "svg" in self.root_orig.nsmap.keys():
            return True
        else:
            return False

    def load(self, filepath: str) -> None:
        """
        Loads the SVG file and parses its content.

        Args:
            filepath (str): The path to the SVG file.
        """
        self.store_metadata(filepath)
        self.root_orig = etree.parse(self.filepath).getroot()
        if not self.check_inkscape():
            self.to_inkscape_svg(filepath)
            self.root_orig = etree.parse(self.filepath).getroot()
        self.root = deepcopy(self.root_orig)
        self.clean()
        self.get_board()

    def save_elem(self, element: etree.Element, outfile: str) -> None:
        """
        Saves an element to an output file.

        Args:
            element (etree.Element): The element to save.
            outfile (str): The output file path.
        """
        tree = etree.ElementTree(element)
        tree.write(outfile, xml_declaration=True)

    def save(self, outfile: str) -> None:
        """
        Saves the current SVG content to an output file.

        Args:
            outfile (str): The output file path.
        """
        self.save_elem(self.root, outfile)

    def reset(self) -> None:
        """
        Resets the SVG content to the original state.
        """
        self.root = deepcopy(self.root_orig)
        self.get_board()

    def get_id(self, id: str) -> etree.Element:
        """
        Retrieves an element by its ID.

        Args:
            id (str): The ID of the element to retrieve.

        Returns:
            etree.Element: The element with the specified ID.
        """
        elem = self.root.xpath(f'.//*[@id="{id}"]')[0]
        return elem

    def get_board(self) -> None:
        """
        Retrieves the board element from the SVG.

        Returns:
            etree.Element: The board element.
        """
        self.board = self.get_id("boardContainer")
        return self.board

    def get_tag(self, tag: str, ns: str = "svg") -> str:
        """
        Constructs a namespaced tag.

        Args:
            tag (str): The tag name.
            ns (str): The namespace prefix.

        Returns:
            str: The namespaced tag.
        """
        return "{" + self.root.nsmap[ns] + "}" + tag

    def rm_tag(
        self,
        elem: etree.Element,
        tag: str,
        ns: str = "svg",
        recursive: bool = False,
        remove_parent: bool = False,
    ) -> etree.Element:
        """
        Removes elements with a specific tag.

        Args:
            elem (etree.Element): The element to search within.
            tag (str): The tag name to remove.
            ns (str): The namespace prefix.
            recursive (bool): Whether to remove elements recursively.
            remove_parent (bool): Whether to remove the parent element.

        Returns:
            etree.Element: The modified element.
        """
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
        """
        Removes attributes from elements.

        Args:
            elem (etree.Element): The element to search within.
            attr (str): The attribute name to remove.

        Returns:
            etree.Element: The modified element.
        """
        xpath_attr = f".//*[@{attr}]"
        groups = elem.xpath(xpath_attr)
        for group in groups:
            group.attrib["id"] = group.attrib["id"] + "_" + group.attrib[attr]
            del group.attrib[attr]
        return elem

    def rm_elem_by_attr_value(
        self, elem: etree.Element, attr: str, value: str
    ) -> etree.Element:
        """
        Removes attributes from elements.

        Args:
            elem (etree.Element): The element to search within.
            attr (str): The attribute name to remove.
            value (str): The attribute value to remove.

        Returns:
            etree.Element: The modified element.
        """
        xpath_attr = f".//*[@{attr}='{value}']"
        groups = elem.xpath(xpath_attr)
        for group in groups:
            group.getparent().remove(group)
        return elem

    def rm_elem_empty(self, elem: etree.Element):
        """
        Recursively remove empty elements from the specified XML element.

        This method traverses through the given XML element and its children.
        It removes any element that has no text content and only one attribute.

        Parameters:
        elem (etree.Element): The XML element to process.
        """
        for x in elem:
            if len(x) > 0:
                self.rm_elem_empty(x)
            else:
                if x.text is None and len(x.attrib) == 1:
                    x.getparent().remove(x)

    def rm_empty_groups(self, elem: etree.Element):
        """
        Remove empty group elements from the specified XML element.

        This method finds and removes all group elements ('g' tags) in the given
        XML element that have no children and only one attribute (which is 'id').

        Parameters:
        elem (etree.Element): The XML element to process.
        """
        tag = self.get_tag("g")
        groups = elem.findall(f".//{tag}")
        for group in groups:
            if (
                len(group) == 0
                and len(group.attrib) == 1
                and list(group.attrib.keys())[0] == "id"
            ):
                group.getparent().remove(group)

    def get_masks(self) -> None:
        """
        Retrieves and stores mask elements.
        """
        self.get_mask("hole-mask")
        self.get_mask("pads-mask-silkscreen")
        self.get_mask("pads-mask")

    def get_mask(self, mask_name: str) -> None:
        """
        Retrieves a specific mask element by name.

        Args:
            mask_name (str): The name of the mask to retrieve.
        """
        gtag = self.get_tag("g")
        self.masks[mask_name] = deepcopy(self.get_id(mask_name))
        self.masks[mask_name].tag = gtag
        self.masks[mask_name].text = ""
        self.masks[mask_name].tail = ""

    def indent_mask(self, group, indent):
        for elem in group:
            elem.tail = "\n" + indent * " "
            if len(elem):
                self.indent_mask(elem, indent + 2)
        group[-1].tail = "\n" + (indent - 2) * " "

    def rm_ink_elem(self) -> None:
        """
        Removes Inkscape-specific elements from the SVG.
        """
        self.rm_tag(self.root, "namedview", "sodipodi")
        self.rm_tag(self.root, "desc")

    def isolate_board(self) -> None:
        """
        Isolates the board element, removing other components.
        """
        elem = self.get_id("componentContainer")
        self.root.remove(elem)
        elem = self.get_board()
        elem = self.rm_tag(elem, "g")
        elem = self.rm_tag(elem, "mask", recursive=True, remove_parent=True)
        self.rm_attr(self.root, "mask")

    def rm_masks(self) -> None:
        """
        Removes mask elements from the SVG.
        """
        self.rm_attr(self.root, "mask")
        self.rm_tag(self.root, "mask", recursive=True)
        self.rm_ink_elem()

    def add_mask_patterns(self) -> None:
        """
        Adds stored mask patterns back to the board element.
        """
        board = self.get_board()
        board[-1].tail = board[-1].tail + "  "
        indent = len(board.tail.replace("\n", "")) + 2
        for mask in self.masks.values():
            mask.text = "\n" + (indent + 2) * " "
            mask.tail = "\n" + indent * " "
            self.indent_mask(mask, indent + 2)
        # Last element must have less indentation
        self.masks[list(self.masks.keys())[-1]].tail = "\n" + (indent - 2) * " "
        if len(board) == 0:
            raise Exception("The board hasn not elements.")
        for mask in self.masks.values():
            board.append(mask)

    def save_mask_files(self, outpath: str) -> None:
        """
        Saves mask elements as separate files.

        Args:
            outpath (str): The output directory for the mask files.
        """
        for name, mask in self.masks.items():
            board = self.get_board()
            board.append(mask)
            filepath = os.path.join(outpath, self.filename + "_" + name + self.ext)
            self.save(filepath)
            board.remove(mask)

    def clean(self):
        """
        Clean the root XML element by removing unnecessary elements and attributes.

        This method performs several cleaning operations on the root XML element:
        1. Removes empty group elements.
        2. Removes elements with a specific attribute value.
        3. Removes elements with specific tags (metadata and namedview).

        The cleaning process helps to simplify the XML structure and remove
        unnecessary data that might interfere with further processing.
        """
        self.rm_empty_groups(self.root)
        self.rm_elem_by_attr_value(self.root, "id", "highlightContainer")
        self.rm_tag(self.root, "metadata", recursive=True)
        self.rm_tag(self.root, "namedview", recursive=True)


def main_convert():
    """
    Main function to convert an SVG file and add mask patterns.
    """
    FILENAME = "test/ArduinoLearningKitStarter.svg"
    OUTPUT = "test/ArduinoLearningKitStarter_exp_mask.svg"
    svg = PcbDrawSvg()
    svg.load(FILENAME)
    svg.get_masks()
    svg.rm_masks()
    svg.add_mask_patterns()
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    svg.save(OUTPUT)


def main_extract_mask():
    """
    Main function to extract mask elements from an SVG file and save them separately.
    """
    FILENAME = "test/ArduinoLearningKitStarter.svg"
    OUTPUT = "tmp/"
    svg = PcbDrawSvg()
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    svg.load(FILENAME)
    svg.get_masks()
    svg.rm_masks()
    svg.save(os.path.join(OUTPUT, f"{svg.filename}_no_masked.svg"))
    svg.isolate_board()
    svg.save_mask_files(OUTPUT)


if __name__ == "__main__":
    main_convert()
    main_extract_mask()
