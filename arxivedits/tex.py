import csv
import os


import arxivedits.data as data
import arxivedits.source as source
import arxivedits.detex as detex


def is_detexed(arxivid: str, version: int) -> bool:
    return os.path.isfile(data.text_path(arxivid, version))


def main():
    """
    Takes .tex files and converts them to text.
    """
    print(len(data.get_local_files()))

    for arxivid, version in data.get_local_files():
        latexfilepath = data.latex_path(arxivid, version)

        if not os.path.isfile(latexfilepath):
            # print(f"{arxivid}-v{version} was not extracted to .tex")
            continue

        outputfilepath = data.text_path(arxivid, version)
        print(latexfilepath)
        detex.detex_file(latexfilepath, outputfilepath)
        print(outputfilepath)

        # Commented the below code out because it was producing extra files that took up too much space in Dropbox

        # outputfilepath = data.clean_latex_path(arxivid, version)
        # with open(latexfilepath, "r") as infile:
        #     with open(outputfilepath, "w") as outfile:
        #         outfile.write(clean(infile.read()))

        # outputfilepath = os.path.join(
        #     data.extrafiles_path(arxivid, version), f"{arxivid}-v{version}-chenhao.txt"
        # )
        # if not os.path.isfile(outputfilepath):
        #     simpleLatexToText(latexfilepath, outputfilepath, sectioned=True)

        # outputfilepath = os.path.join(
        #     data.extrafiles_path(arxivid, version), f"{arxivid}-v{version}-pandoc.md"
        # )
        # if not os.path.isfile(outputfilepath):
        #     pandoc_file(latexfilepath, outputfilepath)


def demo():
    teststrings = [
        r"""
        \begin{document}
        \title{hello}

        \begin{abstract}
        This is my abstract (1).

        \begin{table}
            This is my table (1).
        \end{table}
        
        This is my abstract (2).
        \end{abstract}

        This is my document (1).

        \begin{equation}
            This is my equation (1).
        \end{equation}

        \begin{table*}
            This is my table* (1).
        \end{table*}

        This is my document (2).
        \end{document}""",
        r"\begin{document} \begin{abstract} This is my abstract (1). \end{abstract} \end{document}",
        r"""
        Despite ELBDM particles in the excited state are with a relativistic temperature, almost all particles are in the ground state and described by a single non-relativistic wave function.

        \subsection{Basic Analysis}

        The Lagrangian of non-relativistic scalar field in the comoving
        frame is
        """,
        r"""
        In the early stage([MATH]), the stability condition is
        governed by the kinetic energy term, where
        [MATH] and $dt \leq {{(6 \pi)}^{-1}} (\eta
        a^2)$. At the late time, the gravitational potential becomes ever
        deeper, and therefore [MATH] is controlled by the potential energy,
        where [MATH] is the greatest value of potential in the real
        space.
        """,
        r"""
        We prepare the initial conditions with CMBFAST \citep{cmbfast96} at $z=1000$ with $\Lambda$CDM cosmology.  Such initial conditions differ from that of \citet{hu00},
        where the Compton length of ELBDM already has imprints on the power spectrum
        at $z=1000$.  We choose this initial condition because only a few low-$k$ modes can grow for our choice of Jean's length and the details of initial power spectrum are irrelevant at the late time.
        """,
        r"Therefore, despite its overall similarity with the Anderson transition (see also Ref.\ \cite{suppl}), it remains to be seen if this transition can be classified as such.",
    ]

    for s in teststrings[-1:]:
        print(s)
        print(detex.latex.clean(s))


def script():
    with open(f"{data.DATA_DIR}/matched_sentences.csv") as csvfile:
        reader = csv.reader(csvfile)

        rows = list(reader)

    ids = [row[0] for row in rows]

    localfiles = {
        f"{arxivid}v{v}": (arxivid, v) for arxivid, v in data.get_local_files()
    }

    localfileids = set(localfiles.keys())

    localfiles_from_chenhao = localfileids.intersection(ids)

    localfiles = sorted([localfiles[key] for key in localfiles_from_chenhao])

    print(f"Can inspect {len(localfiles)} localfiles.")

    for arxivid, _ in localfiles:
        if not source.is_downloaded(arxivid, 1):
            source.download_source_files(arxivid, 1)

        if not source.is_extracted(arxivid, 1):
            source.extract_file(
                data.source_path(arxivid, 1), data.latex_path(arxivid, 1)
            )

        if not is_detexed(arxivid, 1):
            detex.detex_file(data.latex_path(arxivid, 1), data.text_path(arxivid, 1))

        if not source.is_downloaded(arxivid, 2):
            source.download_source_files(arxivid, 2)

        if not source.is_extracted(arxivid, 2):
            source.extract_file(
                data.source_path(arxivid, 2), data.latex_path(arxivid, 2)
            )

        if not is_detexed(arxivid, 2):
            detex.detex_file(data.latex_path(arxivid, 2), data.text_path(arxivid, 2))

        print(data.text_path(arxivid, 1))
        print(data.text_path(arxivid, 2))
        print()


if __name__ == "__main__":
    # script()
    main()
    # demo()
    # test()

