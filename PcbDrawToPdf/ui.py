import click
import os
from .isolate_masks import PcbDrawSvg


@click.command()
@click.argument("input", type=click.Path(file_okay=True, dir_okay=False, exists=True))
@click.argument("output", type=click.Path(file_okay=True, dir_okay=False))
def convert_masks(input: str, output: str) -> None:
    svg = PcbDrawSvg()
    svg.load(input)
    svg.get_masks()
    svg.rm_masks()
    svg.add_mask_patterns()
    os.makedirs(os.path.dirname(output), exist_ok=True)
    svg.save(output)


@click.command()
@click.argument("input", type=click.Path(file_okay=True, dir_okay=False, exists=True))
@click.argument("output", type=click.Path(file_okay=False, dir_okay=True))
def extract_masks(input: str, output: str) -> None:
    svg = PcbDrawSvg()
    svg.load(input)
    svg.get_masks()
    svg.isolate_board()
    svg.rm_masks()
    os.makedirs(os.path.dirname(output), exist_ok=True)
    svg.save_mask_files(output)


@click.group()
@click.version_option("v0.0.1")
def run() -> None:
    """
    PcbDrawToPDF exports the masks employed by PcbDraw in order to apply masking on Adobe
    software and be able to save on PDF correctly.
    """
    pass


run.add_command(convert_masks)
run.add_command(extract_masks)

if __name__ == "__main__":
    run()
