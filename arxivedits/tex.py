import csv
import os
import logging

from tqdm import tqdm

from arxivedits import data, source, detex


def main() -> None:
    """
    Takes .tex files and converts them to text.
    """
    logging.disable(logging.FATAL)
    for arxivid, version in tqdm(data.get_sample_files()):
        latexfilepath = data.latex_path(arxivid, version)

        if not os.path.isfile(latexfilepath):
            # print(f"{arxivid}-v{version} was not extracted to .tex")
            continue

        outputfilepath = data.text_path(arxivid, version)

        # if os.path.isfile(outputfilepath):
        #     continue  # already detexed

        # print(latexfilepath)
        detex.detex_file(latexfilepath, outputfilepath)
        # print(outputfilepath)

    logging.disable(logging.NOTSET)


def demo() -> None:
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


def redo() -> None:
    """
    Takes .tex files and converts them to text.
    """
    logging.disable(logging.FATAL)
    for arxivid, v1, v2 in data.ANNOTATED_IDS:
        latexfilepath = data.latex_path(arxivid, v1)

        if os.path.isfile(latexfilepath):
            outputfilepath = data.text_path(arxivid, v1, suffix="-new")
            # print(latexfilepath)
            detex.detex_file(latexfilepath, outputfilepath)
            print(f"code --diff {data.text_path(arxivid, v1)} {outputfilepath}")

        latexfilepath = data.latex_path(arxivid, v2)

        if os.path.isfile(latexfilepath):
            outputfilepath = data.text_path(arxivid, v2, suffix="-new")
            # print(latexfilepath)
            detex.detex_file(latexfilepath, outputfilepath)
            print(f"code --diff {data.text_path(arxivid, v2)} {outputfilepath}")

    logging.disable(logging.NOTSET)


if __name__ == "__main__":
    print(detex.detex_file)
    print(dir(detex))
    # main()
    # redo()
    # demo()
    # test()
