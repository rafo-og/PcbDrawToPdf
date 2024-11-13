import click
from .PcbDrawToPdf import PcbDrawSvg


@click.command()
@click.argument("input", type=click.Path(file_okay=True, dir_okay=False, exists=True))
@click.argument("output", type=click.Path(file_okay=True, dir_okay=False))
def convert_masks(input: str, output: str) -> None:
    svg = PcbDrawSvg()
    svg.load(input)
    svg.convert()
    svg.save(output)


@click.group()
@click.version_option("v1.0.0")
def run() -> None:
    """
    PcbDrawToPDF exports the masks employed by PcbDraw in order to apply masking on Adobe
    software and be able to save on PDF correctly.
    """
    pass


run.add_command(convert_masks)

if __name__ == "__main__":
    run()
