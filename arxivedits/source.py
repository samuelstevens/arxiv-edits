"""
Downloads source files from arxiv.org and extracts the largest .tex file.
"""
# Builtin
from typing import List, Tuple, Optional, Dict, cast, BinaryIO
import tarfile
import gzip
import os
import shutil
import time
import re
import random
import logging
import pathlib
import enum

# External
import requests
import magic

# internal
from arxivedits.structures import ArxivID, Result
from arxivedits import util, data


class FileType(enum.Enum):
    GZIP = enum.auto()
    PDF = enum.auto()
    TEX = enum.auto()
    EPS = enum.auto()
    TAR = enum.auto()
    TEXT = enum.auto()
    IMAGE = enum.auto()
    POSTSCRIPT = enum.auto()

    UNKNOWN = enum.auto()


TIMEOUT = 5


INCLUDEPATTERN = re.compile(
    r"^[^%]*\\(?:include|includeonly|input|@input|bibliography).*?[{ ](.*?)(?:\}| |\n|$)"
)

DOCUMENTPATTERN = re.compile(
    r"^\s*\\(?:documentclass(?:\[.*?\])?\{.+?\}|begin\{document\})"
)

TMP_DIR = "tmp"


def download_file(url: str, local_filename: str) -> str:
    """
    Downloads a file by streaming it. Taken from # https://stackoverflow.com/questions/16694907/download-large-file-in-python-with-requests
    """

    dirpath = os.path.dirname(local_filename)
    os.makedirs(dirpath, exist_ok=True)

    # NOTE the stream=True parameter below
    with requests.get(url, stream=True) as req:
        req.raise_for_status()
        with open(local_filename, "wb") as file:
            for chunk in req.iter_content(chunk_size=8192):
                if chunk:  # filter out keep-alive new chunks
                    file.write(chunk)

    return local_filename


def parse_filetype(mime: str, raw: str) -> FileType:
    # most precise
    if mime == "application/gzip":
        return FileType.GZIP
    if mime == "text/x-tex":
        return FileType.TEX
    if mime == "text/plain":
        return FileType.TEXT
    if mime == "application/x-tar":
        return FileType.TAR
    if mime == "application/pdf":
        return FileType.PDF
    if mime == "application/postscript":
        return FileType.POSTSCRIPT
    if "image" in mime:
        return FileType.IMAGE

    # least precise
    if "EPS" in raw:
        return FileType.EPS
    if "gzip" in raw and "gz" in raw:
        return FileType.GZIP

    logging.debug(f"Unknown filetype: {mime} {raw}")

    return FileType.UNKNOWN


def get_filetype(file: BinaryIO, ext: str) -> FileType:
    """
    returns the filetype of a file using magic (file utility on unix). Resets the file pointer to the start of the file.
    """
    try:
        file.seek(0)  # ensures that we read the first 1024 bytes
        buffer = file.read(4096)
        file.seek(0)  # resets the position to the start.
        result = parse_filetype(
            magic.from_buffer(buffer, mime=True), magic.from_buffer(buffer, mime=False),
        )
    except OSError:  # sometimes file.read throws an OSError if it looks like a gzip file but isn't
        result = FileType.UNKNOWN
    except RecursionError:
        print(file.name, ext)
        exit(1)

    return result


def is_downloaded(arxivid: str, version: int) -> bool:
    """
    Check if a document is downloaded.
    """

    return os.path.isfile(data.source_path(arxivid, version))


def is_extracted(arxivid: str, version: int) -> bool:
    """
    Checks if a document was extracted.
    """
    return os.path.isfile(data.latex_path(arxivid, version))


def add_folder_to_dict(dirpath: str, dictionary: Dict[str, List[str]]) -> None:
    """
    Opens a folder and recursively adds all .tex to the dictionary.
    """
    for filename in os.listdir(dirpath):
        filepath = os.path.join(dirpath, filename).lower()

        if os.path.isfile(filepath):
            # check if filemagic can determine type
            with open(filepath, "rb") as file:
                _, ext = os.path.splitext(filename)
                filetype = get_filetype(file, ext)

                if filetype != FileType.TEX:
                    continue

                contents = file.read()

            lines = contents.decode("utf-8", errors="ignore").split("\n")

            lines = [line for line in lines if not line.lstrip().startswith("%")]

            dictionary[filepath] = lines
        else:
            add_folder_to_dict(filepath, dictionary)


def get_lines(
    filename: str, openfiles: Dict[str, List[str]], closedfiles: Dict[str, List[str]]
) -> None:

    finallines = []

    if filename in openfiles:
        lines = openfiles[filename]
        del openfiles[filename]
    elif filename in closedfiles:
        lines = closedfiles[filename]
        del closedfiles[filename]
    else:
        logging.debug(openfiles.keys(), closedfiles.keys())
        logging.debug(f"{filename} not in openfiles or closedfiles.")
        closedfiles[filename] = []
        return

    for line in lines:
        m = INCLUDEPATTERN.match(line)
        if m:
            includepath = os.path.join(TMP_DIR, m.group(1))

            # normalizes paths like ./sub/something.txt
            includepath = str(pathlib.Path(includepath)).lower()
            _, ext = os.path.splitext(includepath)

            if not ext:
                if (
                    os.path.isfile(includepath + ".tex")
                    and filename != includepath + ".tex"
                ):
                    includepath = includepath + ".tex"

                # elif os.path.isfile(includepath + ".cls"):
                #     includepath = includepath + ".cls"

            _, ext = os.path.splitext(includepath)

            if ext not in [".pdf"]:
                get_lines(includepath, openfiles, closedfiles)
                finallines.extend(closedfiles[includepath])
            else:
                finallines.append(line)
        else:
            finallines.append(line)

    closedfiles[filename] = finallines


def filter_filename(filename: str) -> bool:
    _, ext = os.path.splitext(filename)

    ext = ext[1:]  # remove "."

    return ext not in ["dtx", "sty", "bbl"]


def tex_from_tar(tar: tarfile.TarFile) -> Optional[str]:
    """
    Constructs a .tex file from tarfile contents.

    Removes all comments.
    """

    shutil.rmtree(TMP_DIR, ignore_errors=True)
    os.makedirs(TMP_DIR, exist_ok=True)

    tar.extractall(TMP_DIR)

    openfiles: Dict[str, List[str]] = {}
    closedfiles: Dict[str, List[str]] = {}

    add_folder_to_dict(TMP_DIR, openfiles)

    # do the imports.
    while openfiles:
        filepath = random.choice(list(openfiles))
        get_lines(filepath, openfiles, closedfiles)

    if not closedfiles:
        return None

    # filter empty documents
    old_keys = closedfiles.keys()

    closedfiles = {
        filename: lines
        for filename, lines in closedfiles.items()
        if sum([len(line) for line in lines]) > 0
    }

    if not closedfiles:
        begin = r"\begin{document}"
        documentclass = r"\documentclass{...}"
        logging.warning(
            f"Didn't parse {tar.name} because there was no content in any of the following files: {list(old_keys)}"
        )

        return None

    if len(closedfiles) == 1:
        bestfilename = util.get(closedfiles.keys())
        return "\n".join(closedfiles[bestfilename])

    # filter out files without a \documentclass
    old_keys = closedfiles.keys()

    closedfiles = {
        filename: lines
        for filename, lines in closedfiles.items()
        if any([DOCUMENTPATTERN.match(line) for line in lines])
    }

    if len(closedfiles) == 1:
        bestfilename = util.get(closedfiles.keys())
        return "\n".join(closedfiles[bestfilename])

    if not closedfiles:
        begin = r"\begin{document}"
        documentclass = r"\documentclass{...}"
        logging.warning(
            f"Didn't parse {tar.name} because there was no {documentclass} or {begin} in any of the following files: {list(old_keys)}"
        )

        return None

    # filter out bad file types
    old_keys = closedfiles.keys()

    closedfiles = {
        filename: lines
        for filename, lines in closedfiles.items()
        if filter_filename(filename)
    }

    if len(closedfiles) == 1:
        bestfilename = util.get(closedfiles.keys())
        return "\n".join(closedfiles[bestfilename])

    if not closedfiles:
        logging.warning(
            f"Didn't parse {tar.name} because there was no file that wasn't a .bbl, .sty or .dtx"
        )

        return None

    # now take the longest one in closedfiles
    filelengths = {
        filename: sum([len(line) for line in closedfiles[filename]])
        for filename in closedfiles
    }

    bestfilename = max(filelengths, key=lambda f: filelengths[f])

    return "\n".join(closedfiles[bestfilename])


def extract(filepath: str) -> Optional[str]:
    """
    Takes a directory and creates a .tex file and returns the contents.
    """

    if os.path.isdir(filepath):
        raise ValueError(f"{filepath} is a directory.")

    _, ext = os.path.splitext(filepath)

    with open(filepath, "rb") as file:
        while True:
            file.seek(0)
            filetype = get_filetype(file, ext)

            if filetype == FileType.GZIP:
                # print(f"Using gunzip to unzip {filepath}.")
                file = cast(BinaryIO, gzip.open(file, "rb"))

            elif filetype == FileType.PDF:
                logging.info("Cannot parse PDF files.")
                return None

            elif filetype == FileType.POSTSCRIPT:
                logging.info("Cannot parse POSTSCRIPT files.")
                return None

            elif filetype == FileType.TAR:
                with tarfile.open(fileobj=file, mode="r") as tar:
                    try:
                        return tex_from_tar(tar)
                    except EOFError:
                        logging.warning(f"{filepath} was not downloaded correctly.")
                        return None

            elif filetype == FileType.TEX or filetype == FileType.TEXT:
                # print(f"Reading directly from {filepath}")
                return file.read().decode("utf-8", errors="ignore")
            else:
                raise TypeError(f"{filetype} ({filepath}) not implemented yet.")


def download_source_files(
    arxivid: str, version_count: int, download_pdf: bool = False
) -> None:
    """
    Makes {version_count} network requests, one for each source file, and writes them to disk. If download_pdf is true, also downloads the .pdf file.
    """

    # arxivid = arxivid.replace("-", "/")  # make sure there are no dashes

    for version in range(1, version_count + 1):
        url = f"https://arxiv.org/e-print/{arxivid}v{version}"
        filepath = data.source_path(arxivid, version)

        if not os.path.isfile(filepath):
            try:
                download_file(url, filepath)
                logging.info(f"downloaded {filepath}")
            except requests.exceptions.HTTPError as err:
                logging.warning(err)
                logging.warning(f"Cannot download source for {arxivid}v{version}")

            time.sleep(TIMEOUT)  # respect the server

        if download_pdf:
            url = f"https://arxiv.org/pdf/{arxivid}v{version}"
            filepath = data.pdf_path(arxivid, version)

            if not os.path.isfile(filepath):
                try:
                    download_file(url, filepath)
                except requests.exceptions.HTTPError as err:
                    print(err)
                    print(f"Cannot download source for {arxivid}v{version}")
                print(f"downloaded pdf for {filepath}")
                time.sleep(TIMEOUT)  # respect the server


def get_ids(
    count: int = 1000, shuffled: bool = False, ALL: bool = False
) -> List[Tuple[ArxivID, int]]:
    """
    Gets <count> arxiv ids from the local database with multiple versions and returns them as tuple pairs. If ALL is true, ignores count and returns every id.
    """
    query = "SELECT arxiv_id, version_count FROM papers WHERE version_count > 1"

    con = data.connection()

    rows = con.execute(query).fetchall()

    result = list(rows)

    con.close()

    if not ALL:
        result = result[:count]

    if shuffled:
        random.shuffle(result)  # shuffles in place

    return result


def download_all() -> None:
    """
    Downloads all source files for all versions for all papers with 2+ versions.
    """

    done = util.log_how_many(is_downloaded, "downloaded")

    if done:
        return

    for arxivid, version_count in data.get_all_files(
        maximum_only=True
    ):  # download_source_files wants the total number of versions for each id
        download_source_files(arxivid, version_count)

    util.log_how_many(is_downloaded, "downloaded")


def extract_file(sourcefilepath: str, outfilepath: str) -> Result[None]:
    content: Optional[str] = None

    try:
        content = extract(sourcefilepath)
    except TypeError as err:
        return err

    if content:
        # removes not utf characters
        contentbytes = content.encode(encoding="utf-8", errors="ignore")
        with open(outfilepath, "wb") as file:
            file.write(contentbytes)

    return None


def extract_all(again: bool = False) -> None:
    """
    Extracts the .tex file from every .gz file to its directory.
    """

    done = util.log_how_many(is_extracted, "extracted")

    if done and not again:
        return

    logging.info("Extracting files.")

    for arxivid, version in data.get_all_files():
        if not is_downloaded(arxivid, version):
            continue

        sourcefilepath = data.source_path(arxivid, version)
        latexpath = data.latex_path(arxivid, version)

        if is_extracted(arxivid, version) and not again:
            continue  # skip if already extracted

        err = extract_file(sourcefilepath, latexpath)
        if err:
            logging.warning(f"Error extracting {sourcefilepath}: {err}")

    util.log_how_many(is_extracted, "extracted")


def main() -> None:
    download_all()

    extract_all()


if __name__ == "__main__":
    # main()
    extract_all(again=True)
