"""
Downloads source files from arxiv.org and extracts the largest .tex file.
"""
# Builtin
from typing import List, Tuple, Optional, Dict
import tarfile
import gzip
import os
import shutil
import time
import re
import random
import pathlib

# External
import requests
import magic  # type: ignore

# internal
from structures import ArxivID  # type: ignore
from data import connection, SOURCE_DIR, UNZIPPED_DIR, is_x

# latexcommands = [r'\\include', r'\\includeonly', r'\\input', r'\\@input']
commandpattern = re.compile(
    r"\\(?:include|includeonly|input|@input).*?[{ ](.*?)(?:\}| |\n|$)"
)
tmpdir = "tmp"


def download_file(url: str, local_filename: str) -> str:
    """
    Downloads a file by streaming it. Taken from # https://stackoverflow.com/questions/16694907/download-large-file-in-python-with-requests
    """

    # NOTE the stream=True parameter below
    with requests.get(url, stream=True) as req:
        req.raise_for_status()
        with open(local_filename, "wb") as file:
            for chunk in req.iter_content(chunk_size=8192):
                if chunk:  # filter out keep-alive new chunks
                    file.write(chunk)

    return local_filename


def get_filetype(file) -> str:
    """
    returns the filetype of a file using magic (file utility on unix). Resets the file pointer to the start of the file.
    """
    file.seek(0)  # ensures that we read the first 1024 bytes
    buffer = file.read(2048)
    file.seek(0)  # resets the position to the start.
    return magic.from_buffer(buffer, mime=False)


def is_downloaded(arxivid, versioncount) -> bool:
    """
    Check if a document is downloaded.
    """
    return is_x(arxivid, versioncount, SOURCE_DIR)


def is_extracted(arxivid, versioncount) -> bool:
    """
    Checks if a document was extracted.
    """
    return is_x(arxivid, versioncount, UNZIPPED_DIR)


def add_folder_to_dict(dirpath, dictionary):
    """
    Opens a folder and recursively adds all .tex to the dictionary.
    """
    for filename in os.listdir(dirpath):
        filepath = os.path.join(dirpath, filename)

        if os.path.isfile(filepath):
            _, ext = os.path.splitext(filename)

            if ext != ".tex":
                continue

            with open(filepath, "rb") as file:
                contents = file.read()

            lines = contents.decode("utf-8", errors="ignore").split("\n")

            dictionary[filepath] = lines
        else:
            add_folder_to_dict(filepath, dictionary)


def get_lines(filename, openfiles, closedfiles):

    finallines = []

    if filename in openfiles:
        lines = openfiles[filename]
        del openfiles[filename]
    elif filename in closedfiles:
        lines = closedfiles[filename]
        del closedfiles[filename]
    else:
        print(openfiles.keys(), closedfiles.keys())
        print(f"{filename} not in openfiles or closedfiles.")
        closedfiles[filename] = []
        return

    lines = [line for line in lines if not line.lstrip().startswith("%")]

    for line in lines:
        m = commandpattern.match(line)
        if m:
            print(m.group(1))
            includepath = os.path.join(tmpdir, m.group(1))

            # normalizes paths like ./sub/something.txt
            includepath = str(pathlib.Path(includepath))
            _, ext = os.path.splitext(includepath)

            if not ext:
                if os.path.isfile(includepath + ".tex"):
                    includepath = includepath + ".tex"

            _, ext = os.path.splitext(includepath)

            if ext == ".tex":
                get_lines(includepath, openfiles, closedfiles)
                finallines.extend(closedfiles[includepath])
            else:
                finallines.append(line)
        else:
            finallines.append(line)

    closedfiles[filename] = finallines


def tex_from_tar(tar: tarfile.TarFile) -> Optional[str]:
    """
    Constructs a .tex file from tarfile contents.

    Removes all comments.
    """

    shutil.rmtree(tmpdir)
    os.makedirs(tmpdir, exist_ok=True)

    tar.extractall(tmpdir)

    openfiles: Dict[str, List[str]] = {}
    closedfiles: Dict[str, List[str]] = {}

    add_folder_to_dict(tmpdir, openfiles)

    # do the imports.
    while openfiles:
        filepath = random.choice(list(openfiles))
        get_lines(filepath, openfiles, closedfiles)

    if not closedfiles:
        return None

    # now take the longest one in closedfiles
    filelengths = {
        filename: sum([len(line) for line in closedfiles[filename]])
        for filename in closedfiles
    }

    bestfilename = max(filelengths, key=lambda f: filelengths[f])

    return "\n".join(closedfiles[bestfilename])


def extract(filepath) -> Optional[str]:
    """
    Takes a directory and creates a .tex file and returns the contents.
    """

    if os.path.isdir(filepath):
        raise ValueError(f"{filepath} is a directory.")

    # now, filepath is not a directory
    with open(filepath, "rb") as file:
        while True:
            file.seek(0)
            filetype = get_filetype(file)

            if "gzip" in filetype:
                # print(f'Using gunzip to unzip {filepath}.')
                file = gzip.open(file, "rb")

            elif "pdf" in filetype:
                # print('Going to ignore PDF.')
                return None

            elif "tar" in filetype:
                # print(f'Using tar to extract from {filepath}')
                with tarfile.open(fileobj=file, mode="r") as tar:
                    return tex_from_tar(tar)

            elif "tex" in filetype:
                # print(f'Reading directly from {filename}')
                return file.read().decode("utf-8", errors="ignore")

            else:
                raise TypeError(f"{filetype} ({filepath}) not implemented yet.")


def download_source_files(
    arxiv_id: ArxivID, version_count: int, output_directory: str = SOURCE_DIR
) -> None:
    """
    Makes {version_count} network requests, one for each source file, and writest them to {output_directory}
    """

    arxividpath = arxiv_id.replace("/", "-")

    for version in range(1, version_count + 1):
        url = f"https://arxiv.org/e-print/{arxiv_id}v{version}"
        filename = os.path.join(output_directory, f"{arxividpath}-v{version}")

        if not os.path.isdir(output_directory):
            os.makedirs(output_directory)

        if not os.path.isfile(filename):
            try:
                download_file(url, filename)
            except requests.exceptions.HTTPError as err:
                print(err)
                print(f"Cannot download source for {arxiv_id}v{version}")

            time.sleep(30)  # respect the server


def get_ids() -> List[Tuple[ArxivID, int]]:
    """
    Gets 1000 arxiv ids from the local database with multiple versions and returns them as tuple pairs
    """
    query = "SELECT arxiv_id, version_count FROM papers WHERE version_count > 1"

    rows = connection().execute(query).fetchall()

    return rows[:1000]  # return only the first 1000


def download_all():
    """
    Downloads all source files for all versions for all papers with 2+ versions.
    """
    arxiv_id_pairs = get_ids()

    for arxiv_id, version_count in arxiv_id_pairs:
        download_source_files(arxiv_id, version_count)


def extract_file(sourcefilepath: str, outfilepath) -> Optional[Exception]:
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


def extract_all(extract_again: bool = True):
    """
    Extracts the a .tex file from every file in SOURCE_DIR to UNZIPPED_DIR
    """

    os.makedirs(UNZIPPED_DIR, exist_ok=True)

    for filename in os.listdir(SOURCE_DIR):
        unzippedfilepath = os.path.join(UNZIPPED_DIR, filename)
        sourcefilepath = os.path.join(SOURCE_DIR, filename)

        if os.path.isfile(unzippedfilepath) and not extract_again:
            continue

        err = extract_file(sourcefilepath, unzippedfilepath)
        if err:
            print(err)


if __name__ == "__main__":
    # download_all()
    # extract_all()
    err = extract_file(
        "data/unzipped/hep-th-9912274-v2", "data/unzipped/hep-th-9912274-v2"
    )
