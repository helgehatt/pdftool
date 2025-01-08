import glob

import click
import pypdf


@click.group()
def cli():
    pass


def click_option_filename(func):
    return click.option(
        "-f",
        "--filename",
        type=click.Path(),
        help="Specify the path of the save as file.",
    )(func)


def click_option_dry_run(func):
    return click.option(
        "-n",
        "--dry-run",
        is_flag=True,
        default=False,
        help="Print what would happen without doing anything.",
    )(func)


@cli.command()
@click_option_filename
@click_option_dry_run
@click.option(
    "--sort",
    is_flag=True,
    default=False,
    help="Whether to sort files by name before merging.",
)
@click.argument("files", nargs=-1, type=click.Path())
def merge(filename: str, dry_run: bool, sort: bool, files: tuple[str]):
    class BadFilesParameter(click.BadParameter):
        def __init__(self, message: str):
            super().__init__(message, None, None, "'[FILES]...'")

    if not len(files):
        raise BadFilesParameter("Provide at least one argument.")

    files = [f for file in files for f in glob.glob(file)]

    if not len(files):
        raise BadFilesParameter("No existing files matched.")

    if sort:
        files = _sort_filenames(files)

    if filename is None:
        filename = _append_filename(files[0], "merged")

    if dry_run:
        click.echo(f"Merge the following files and save as '{filename}':")
        for f in files:
            click.echo(f)
        return

    merger = pypdf.PdfWriter()
    for f in files:
        merger.append(f)
    merger.write(filename)


@cli.command()
@click_option_filename
@click_option_dry_run
@click.argument("file", type=click.Path(exists=True))
@click.argument("angle", type=int, default=90)
def rotate(filename: str, dry_run: bool, file: str, angle: int):
    if filename is None:
        filename = _append_filename(file, "rotated")

    if dry_run:
        click.echo(f"Rotate '{file}' {angle} degrees and save as '{filename}'")
        return

    reader, writer = pypdf.PdfReader(file), pypdf.PdfWriter()
    for page in reader.pages:
        writer.addPage(page.rotateClockwise(angle))
    writer.write(filename)


class SelectionParamType(click.ParamType):
    name = "selection"

    def convert(self, value, param, ctx):
        # Convert "1,4-6,8" to [["1"], ["4", "6"], ["8"]]
        pairs = [arg.split("-") for arg in str(value).split(",")]
        # Convert [["1"], ["4", "6"], ["8"]] to [1, 4, 5, 6, 8]
        return [i for pair in pairs for i in range(int(pair[0]), int(pair[-1]) + 1)]


@cli.command()
@click_option_filename
@click_option_dry_run
@click.argument("file", type=click.Path(exists=True))
@click.argument("selection", type=SelectionParamType())
def select(filename: str, dry_run: bool, file: str, selection: list[int]):
    if filename is None:
        filename = _append_filename(file, "selected")

    if dry_run:
        click.echo(f"Select '{selection}' from '{file}' and save as '{filename}'")
        return

    reader, writer = pypdf.PdfReader(file), pypdf.PdfWriter()
    for i in filter(lambda x: x <= len(reader.pages), selection):
        writer.add_page(reader.pages[i - 1])
    writer.write(filename)


@cli.command()
@click_option_filename
@click_option_dry_run
@click.argument("file", type=click.Path(exists=True))
def split(filename: str, dry_run: bool, file: str):
    if filename is None:
        filename = file

    reader = pypdf.PdfReader(file)

    if dry_run:
        click.echo(f"Split '{file}' and save as:")
        for i in range(len(reader.pages)):
            click.echo(_append_filename(filename, i + 1))
        return

    for i in range(len(reader.pages)):
        writer = pypdf.PdfWriter()
        writer.add_page(reader.pages[i])
        writer.write(_append_filename(filename, i + 1))


def _append_filename(filename: str, text_to_append: str):
    name, ext = filename.rsplit(sep=".", maxsplit=1)
    return f"{name}-{text_to_append}.{ext}"


def _sort_filenames(filenames: list[str]):
    from natsort import os_sorted

    return os_sorted(filenames)


if __name__ == "__main__":
    cli()
