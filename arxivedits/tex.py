import os
import logging


from arxivedits import data, detex, source, util


def is_detexed(arxivid: str, version: int) -> bool:
    return os.path.isfile(data.text_path(arxivid, version))


def detex_all(again: bool = False) -> None:

    done = util.log_how_many(is_detexed, "detexed")

    if done and not again:
        return

    logging.info("Detexing files.")

    for arxivid, version in data.get_all_files():

        if not source.is_extracted(arxivid, version):
            continue

        if is_detexed(arxivid, version) and not again:
            continue  # already detexed

        outputfilepath = data.text_path(arxivid, version)
        latexfilepath = data.latex_path(arxivid, version)

        detex.detex_file(latexfilepath, outputfilepath)

    util.log_how_many(is_detexed, "detexed")


def main() -> None:
    """
    Takes .tex files and converts them to text.
    """
    detex_all()


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
        r"""So, $\hat x_{j_1 \cdots j_N} = \hat x_{2-j_1 \cdots 2-j_N}$.
Thus, we can assume that $x_{i_1i_2\cdots i_n}=x_{(2-i_1)(2-i_2)\cdots (2-i_N)}$.
\hfill $\Box$\medskip

By the above proposition and the discussion  in Section 2, we see that
the system $A_\alpha^{\otimes N} \bx =  0$ has a nontrivial nonnegative
solution if and only if the system $C_{\alpha,N}\mathbf{y}=0$
has a nontrivial nonnegative solution $\by$.""",
    ]

    for s in teststrings:
        print(s)
        print()
        print(detex.opendetex.detex(s))
        print("---")


if __name__ == "__main__":
    # main()
    demo()
