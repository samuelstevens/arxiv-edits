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
import csv

# External
import requests
import magic  # type: ignore

# internal
from structures import ArxivID  # type: ignore
from data import connection
import data


INCLUDEPATTERN = re.compile(
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


def is_downloaded(arxivid: str, version: int) -> bool:
    """
    Check if a document is downloaded.
    """
    return os.path.isfile(data.source_path(arxivid, version))


def is_extracted(arxivid, version: int) -> bool:
    """
    Checks if a document was extracted.
    """
    return os.path.isfile(data.latex_path(arxivid, version))


def add_folder_to_dict(dirpath, dictionary):
    """
    Opens a folder and recursively adds all .tex to the dictionary.
    """
    for filename in os.listdir(dirpath):
        filepath = os.path.join(dirpath, filename).lower()

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
        m = INCLUDEPATTERN.match(line)
        if m:
            includepath = os.path.join(tmpdir, m.group(1))

            # normalizes paths like ./sub/something.txt
            includepath = str(pathlib.Path(includepath)).lower()
            _, ext = os.path.splitext(includepath)

            if not ext:
                if os.path.isfile(includepath + ".tex"):
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


def download_source_files(arxivid: ArxivID, version_count: int,) -> None:
    """
    Makes {version_count} network requests, one for each source file, and writes them to {output_directory}
    """

    arxividpath = arxivid.replace("/", "-")

    for version in range(1, version_count + 1):
        url = f"https://arxiv.org/e-print/{arxivid}v{version}"
        filepath = data.source_path(arxividpath, version)

        if not os.path.isfile(filepath):
            try:
                download_file(url, filepath)
            except requests.exceptions.HTTPError as err:
                print(err)
                print(f"Cannot download source for {arxivid}v{version}")

            time.sleep(30)  # respect the server

        url = f"https://arxiv.org/pdf/{arxivid}v{version}"
        filepath = data.pdf_path(arxividpath, version)

        if not os.path.isfile(filepath):
            try:
                download_file(url, filepath)
            except requests.exceptions.HTTPError as err:
                print(err)
                print(f"Cannot download source for {arxivid}v{version}")
            print(f"downloaded pdf for {filepath}")
            time.sleep(5)  # respect the server


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
    # arxiv_id_pairs = get_ids()

    with open("data/sample-only-multiversion.csv") as csvfile:
        reader = csv.reader(csvfile)

        for arxivid, version_count in reader:
            download_source_files(arxivid, int(version_count))

    # for arxivid, version_count in data.get_local_files(maximum_only=True):
    #     download_source_files(arxivid, version_count)

    # for arxiv_id, version_count in arxiv_id_pairs:
    #     download_source_files(arxiv_id, version_count)


def extract_file(sourcefilepath: str, outfilepath: str) -> Optional[Exception]:
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
    Extracts the a .tex file from every .gz file to its directory.
    """

    for arxivid, version in data.get_local_files():
        sourcefilepath = data.source_path(arxivid, version)
        latexpath = data.latex_path(arxivid, version)
        sourcecopypath = data.source_path(arxivid, version)

        if not os.path.isfile(sourcecopypath):
            shutil.copyfile(sourcefilepath, sourcecopypath)

        if os.path.isfile(latexpath) and not extract_again:
            continue

        err = extract_file(sourcefilepath, latexpath)
        if err:
            print(err)


def main():
    download_all()
    extract_all()


if __name__ == "__main__":
    main()
    # extract_file(data.source_path("1410.3634", 2), data.latex_path("1410.3634", 2))

