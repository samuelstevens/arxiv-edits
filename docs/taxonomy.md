# Taxonomy of Edit Intention in Scientific Writing

## Contents

[Change](#changes)

[Current Working Example](#working-example)

[Categories](#categories)

[Problems I'm Looking to Solve](#problems-in-diyis-taxonomy-that-i-want-to-solve)

[Questions](#questions)

## Changes

* May 19, 2020: split Copy Editing into [Organizational](#organizational) and [Word Usage](#word-usage). Added [Dependent Update](#dependent-update).
  * Still need to check all existing labels for:
    * Copy Editing
* May 17, 2020: split Copy Editing into Copy Editing and [Correction](#correction). Merged Refactoring and Verification into [Reading Flow](#reading-flow). Changed Clarification into [Specify](#specify).
  * Still need to check all existing labels for
    * Clarification

## Working Example

## Categories

[Specify](#specify)

[Simplification](#simplification)

[Elaboration](#elaboration)

[Organizational](#organizational)

[Word Usage](#word-usage)

[Correction](#correction)

[Reading Flow](#reading-flow)

[Other](#other)

### Specify

Changes the generality/specificity of a claim or piece of evidence. This can be making a sentence more *or* less specific, but both are changing the size of the sentence's main point. Does not make a new claim or add additional evidence to support a claim.

#### Examples

When [MATH], it is still helpful to correct Pauli errors `corresponding to` [MATH] errors despite the fact that [MATH], [MATH] and these Pauli errors may occur independently.

When [MATH], it is still helpful to correct Pauli errors `according to detected` [MATH] errors despite the fact that [MATH], [MATH] and these Pauli errors may occur independently.

**Explanation:** the original sentence says it is helpful to correct the Pauli errors that correspond to [MATH] errors. The new sentence says is it helpful to correct the Pauli errors that correspond to *detected* [MATH] errors, which is more specific, and is thus *Specify*.

> This is also [Word Usage](#word-usage) because they also change *corresponding* to *according*.

---

In this case, first the total system (i.e., system of interest plus environment) is initially represented as [EQUATION] at [MATH], with [MATH] as in equation ([REF]).

Assuming that system and environment are initially decoupled, the (initial) total wave function accounting for both can be expressed as a factorized product of the initial wave function describing each subsystem, [EQUATION] with [MATH], as in Eq. ([REF]).

**Explanation:** This is Specify because it adds the assumption that "system and environment are initially decoupled". 

> It is also [Elaboration](#elaboration) because it adds further explanation about the total wave function and each subsystem.

> It is also [Correction](#correction) because it changes equation to Eq.

### Simplification

Removes information by getting rid of a claim or a piece of evidence.

#### Examples

`Nevertheless, sometimes it is possible` to devise `simple` models `which allow us` to understand how the coherence damping takes `place, in particular, in double-slit experiments [CITATION], which we are interesting in here`.

`This allows one` to devise `simple, phenomenological` models to understand `the way` how the coherence damping takes `place [CITATION]`.

**Explanation:** Removes explanation that they are focusing on double-slit experiments. This looks like [Specify](#specify) because it changes from understanding damping in double-slit to just understanding damping, but the sentence in v1 just says that they are explicitly interested in the double-slit, not that the model doesn't work outside double slit.

> Also Word Usage because it changes the phrasing.

---

Note that, in the coordinate representation and for an environment constituted by [MATH] particles, `equation` ([REF]) `should be obtained after integrating [MATH] over the 3[MATH] environment degrees of freedom, i.e.,` [EQUATION] `with [MATH], [MATH] being a 3-dimensional vector`.

Note that, in the coordinate representation and for an environment constituted by [MATH] particles, `Eq.` ([REF]) `becomes` [EQUATION].

**Explanation:** This is a Simplification because it removes the explanation for how the equation is obtained.

### Elaboration

Adds new content to a sentence, even if the content is simply to clarify existing information. If it changes the specificity of a claim or evidence by *changing the scope*, then it's [Specify](#specify)

#### Examples

`Then,` we can estimate the logical error rate `of the error rate` [MATH], which is given by [EQUATION] where [MATH], [MATH] and [MATH].

`Given fitting parameters [MATH], [MATH], [MATH] and [MATH],` we can estimate the logical error rate `for error rates` [MATH] `by replacing [MATH] with [MATH]`, which gives [EQUATION] where [MATH], [MATH] and [MATH].

**Explanation:** The author adds additional information that explains how they can estimate the error rate.

> In addition, the authors change "of the error rate" to "for error rates", which is [Word Usage](#word-usage).

---

Decoherence is the most widespread mechanism [CITATION] to explain the classical-like `behavior displayed by` quantum systems `under certain conditions [CITATION]`

`As is well known,` decoherence is `nowadays` the most widespread mechanism `used in the literature` [CITATION] to explain the `appearance of` classical-like `behaviors in` quantum systems `due to their dynamical interaction with an environment`

**Explanation:** this is an Elaboration because it adds more information; rather than only saying *under certain conditions*, it goes further and describes *dynamical interaction with an environment*.

> *As is well known* is [Word Usage](#word-usage) because it changes the style/tone of the sentence without changing the true meaning.

> Changing *displayed by* to *appearance of* is [Word Usage](#word-usage) because those phrases mean the same thing, so it changes the style/tone of the sentence without changing the meaning.

> *nowadays* and *used in the literature* are [Specify](#specify) because it changes the specificity of the claim.

---

Quantum contextuality implies that the physics associated with a certain system unavoidably depends on the quantum state chosen to describe it.

One of them is contextuality, the unavoidable dependence of the description of a system on the experimental (or contextual) setup, which strongly determines the wave function describing the quantum state of that system [CITATION].

*(diff is too much to highlight)*

**Explanation:** This is an Elaboration because it adds an explanation that the system depends on the *setup* rather than the quantum state, and that the setup determines the quantum state. 

> It is also Copy Editing because they rephrase that quantum contextuality is the dependence of a system on (blah) (and it is a sentence fusion).

### Word Usage

Changes language, tone or style without changing the claim, evidence or specifity of a sentence. Adding or removing words like "the" is a Copy Edit (unless v1 was grammatically incorrect) because it changes the style/tone of the sentence.

#### Examples

For a red octagon [Fig. [REF](b)], TC of eight MFs on the octagon is [MATH].

For a red octagon [`see` Fig. [REF](b)], TC of eight MFs on the octagon is [MATH].

**Explanation:** Adds *see* before "Fig. [REF](b)", which only changes the tone of the sentence (very slightly).

> **NOT** a [Reading Flow](#reading-flow) even though it has to do with a "Fig." because it doesn't change the reader's connection between the different sections of the paper.

---

`Note that in` the limit `of full quenching ([MATH],` [MATH]), `equation` ([REF]) becomes [EQUATION] where [MATH] and [MATH] are, respectively, the velocity field and `the` probability density associated with the `partial` wave [MATH], and [EQUATION].

`If we consider` the limit [MATH]), `Eq.` ([REF]) becomes [EQUATION] where [MATH] and [MATH] are, respectively, the velocity field and probability density associated with the wave [MATH], and [EQUATION].

**Explanation:** Removing "of full quenching" is Copy Editing because the [MATH] is identical and (I think) informative enough that removing "of full quenching" doesn't change the meaning or specificity of the sentence. Changing "Note that in" and "If we consider" is also Copy Editing.

> Also a [Correction](#correction) because `equation` becomes `Eq`.

---

Quantum information stored in distant MFs is expected to be immune to `any` local perturbations due to the environment.

Quantum information stored in distant MFs is expected to be immune to local perturbations due to the environment.

**Explanation:** Word usage because "any" is removed. 

> *Not* [Specify](#specify) because the generality of the claim doesn't change.

### Organizational

Moves, joins and splits sentences and clauses between around within the sentence or paragraph.

### Correction

Fixes spelling, grammar or formatting without changing the meaning or specifity of a sentence. 

#### Examples

Alternatively, one can choose to repeat the distillation circuit (the `entangled state` generation part) for once if a failure occurs.

Alternatively, one can choose to repeat the distillation circuit (the `entangled-state` generation part, `see Fig. [REF]`) for once if a failure occurs.

**Explanation:** The change from *entangled state* to *entangled-state* is a correction because it doesn't change the meaning, style or tone of the sentence.

> This is also [Reading Flow](#reading-flow) because they add *see Fig. [REF]*.

### Reading Flow

Makes or changes connections between different sections of the paper in order to help the reader connect the dots. This might be changing references to tables and figures, adding citations to other papers, updating a section title, or moving sentences around within the document. If an local edit's main focus is not to change the flow of reading, it is not a Reading Flow.

#### Examples

In the case [MATH], when a [MATH] error occurs, an [MATH] error and some Pauli errors always occur simultaneously `(Sec. [REF])`.

In the case [MATH], when a [MATH] error occurs, an [MATH] error and some Pauli errors always occur simultaneously `(see Appendix [REF])`.

**Explanation:** Here, it changes from a Section to an Appendix, and is evidence of changing the order of reading within the article.

---

Alternatively, one can choose to repeat the distillation circuit (the `entangled state` generation part) for once if a failure occurs.

Alternatively, one can choose to repeat the distillation circuit (the `entangled-state` generation part, `see Fig. [REF]`) for once if a failure occurs.

**Explanation:** They add *see Fig. [REF]* which is a reference to a figure, helps the reader understand that the figure is relevant to the current topic.

> This is also Copy Editing because they add a dash.

---

The two outcomes mentioned above are commonly related in standard quantum mechanics textbooks [CITATION] to the well-known wave-corpuscle duality.

In the literature it is common to associate the two contexts described above with either the duality principle *(with the two slits open simultaneously, the system behaves as a wave; with only one, as a corpuscle) or the uncertainty principle (determining the particle position is the same as to determine which slit the particle passed through, while letting it pass through both slits open allows us to determine its momentum).*

> The italics in v2 are aligned to a different sentence; this examples doesn't consider that part.

**Explanation:** By removing the citation, the authors communicate that it is not important to the reader, so the flow of reading is changed.

> This is also Copy Editing because of:
> * sentence fusion
> * the sentence is rephrased and *textbooks* are changed to *literature*;

--- 

(Negative Example)

Notice that despite `the fact that` there is no coherence `here,` trajectories do not cross the symmetry axis `separating` the `regions covered by each slit`.

Notice that despite there is no coherence `(in the sense that the interference terms of the reduced density matrix have been damped out),` trajectories do not cross the symmetry axis `between` the `two slits because they obey Eq. ([REF]), which contains information about the two slits open simultaneously`.

**Explanation:** It is **not** Reading Flow even though it adds a reference because the reference is contained within other information also added. 

---

(Negative Example)

*Quantum mechanics is characterized by different striking features or properties which puzzle and challenge our understanding,* contextuality being one of the most remarkable and fundamental ones.

One of them is contextuality, the unavoidable dependence of the description of a system on the experimental (or contextual) setup, which strongly determines the wave function describing the quantum state of that system [CITATION].

> The italics in v1 are aligned to a different sentence; this examples doesn't consider that part.

**Explanation:** It is **not** Reading Flow even though it adds a reference because the reference is contained within other information also added. 

### Other

Examples that don't fit anywhere else.

#### Examples

The `reason` to `use such an approach (instead` of `wave functions or density matrices) is because` trajectories `allow us` to follow the system dynamics and to understand the underlying physics at the same level that classical trajectories `help to understand the` classical `world`.

The `transition from one context` to `the other due to decoherence can be very well visualized in terms` of `quantum` trajectories `[CITATION], since they offer a clear interpretational advantage by making possible` to follow the system dynamics and to `(intuitively)` understand the underlying physics `of the process` at the same level that classical trajectories `do in` classical `mechanics`.

Here, the authors change the reason they present for using quantum trajectories. This is a *change to their argument*, which doesn't fit in any of the categories I have so far.

---

In the particular where [MATH], [MATH] being the coherence time, one obtains [EQUATION] which establishes a simple relationship between the degree of coherence and the coherence time.

For instance, if we consider [MATH], we find [EQUATION] where [MATH] is the coherence time, which is a function of different physical parameters (the system mass, temperature, etc.).

Is this...

* Elaboration because they add more information?
* Simplification because they remove the "relationship between the degree of coherence and the coherence time"
* Copy editing because these sentences probably mean the same thing to a physicist?
* A change to their argument or evidence?
* A change to the description of an thing?

---

The interference quenching is apparent in the double-slit experiment, where the elimination of interference fringes gives rise to a classical-like pattern where the classical addition rule of probabilities holds.

Here we have dealt with the problem of the damping or quenching of the interference fringes produced by decoherence in a two-slit experiment under the presence of an environment, which yields as a result a classical-like pattern.

**Notes:**
* Gets rid of the idea that "the classical addition rule of probabilities holds"
* Adds idea that interference fringes are produced by decoherence.
* Adds idea that the experiment occurs "under the presence of an environment"
* Changes from elimination of fringes to damping/quenching of fringes.

**Explanations** 
* Simplification because they remove the idea that the "the classical addition rule of probabilities" hold. 
* Elaboration because they add ideas that interference fringes are produced by decoherence and that the experiment occurs "under the presence of an environment". 
* Copy editing because they add some filler words "Here we have dealt"
* Something else because they change "elimination" to "damping", which is obviously weaker.

---

In Fig. [REF](b), we show the cost of qubits for encoding a logical qubit as a function of the `required` logical-qubit error rate.

In Fig. [REF](b), we show the cost of qubits for encoding a logical qubit as a function of the logical-qubit error rate.

**Notes**
* Removing "required" initially looks like a 'Specify'. However, it doesn't change the generality/specificity of their claim/evidence. Instead, it changes their evidence: 

...we show the cost as a function of the *required* rate.

vs.

...we show the cost as a function of the rate.

Is the function different? Is the input parameter different? Is it a fact update because they changed the function? Did they mistype the first time?

## Domain Knowledge Required

However, `with fermion-parity errors,` the outcome of the qubit-charge measurement may be incorrect.

However, `when [MATH] is finite,` the outcome of the qubit-charge measurement may be incorrect.

It's difficult to tell what the relationship between `with fermion-parity errors,` and `when [MATH] is finite,`

---

Therefore, `braiding` errors `that exchange fermions` between [MATH] and ancillary `MFs,` i.e. `change` the ancillary `charge,` can be detected.

Therefore, `charge-conserving` errors `exchanging TC` between [MATH] and ancillary `MFs [CITATION],` i.e. `changing` the ancillary `TC,` can be detected.

**Explanation:** Do "braiding" and "charge-conserving" mean the same thing? What about "fermions" and "TC"? If they are different names for the same concept, then this is a surface level change. If not, then the meaning of the sentence has changed.

---

`When [MATH] (no distillation)`, [MATH] and [MATH]; when `[MATH(2)]`, [MATH] can be obtained numerically by simulating the distillation circuit.

`Without the PP distillation`, [MATH] and [MATH]; when `the distillation is performed`, [MATH] can be obtained numerically by simulating the distillation circuit.

![](/docs/images/taxonomy/highlighted-explanation-v1.png)
(https://arxiv.org/pdf/1512.05089v1.pdf) The yellow is the relevant sentence. When combined with the information highlighted in blue, it's clear that these sentences are simply Copy Editing

![](/docs/images/taxonomy/highlighted-explanation-v2.png)
(https://arxiv.org/pdf/1512.05089v2.pdf)

When looking at the PDFs, and reading the previous sentence, it is clear that sentences mean the same thing. Without the PDFs, it's very difficult (impossible, in my opinion) to know that [MATH(2)] means "distillation is performed".

---

`Note that in` the limit `of full quenching ([MATH],` [MATH]), `equation` ([REF]) becomes [EQUATION] where [MATH] and [MATH] are, respectively, the velocity field and `the` probability density associated with the `partial` wave [MATH], and [EQUATION].

`If we consider` the limit [MATH]), `Eq.` ([REF]) becomes [EQUATION] where [MATH] and [MATH] are, respectively, the velocity field and probability density associated with the wave [MATH], and [EQUATION].

**Explanation:** Is the [MATH] in the tag informative enough such that removing "of full quenching" doesn't change the meaning of the sentence.

## Problems in Diyi's Taxonomy that I Want to Solve

1. Clarification vs Elaboration. Diyi's original descriptions make it sound like these two categories exist along the same axis (the axis of adding information), and that at some point it shifts from clarification to elaboration. I want all my categories to be orthogonal, with no thresholds.
2. Clarification vs Copy Editing. The name "clarification" means to me that if a sentence is rephrased to be more clear, then it is a "clarification". However, it is also copy editing because it is a rephrase without any new information.

## Questions

* Changing a plural to a singluar; is this a correction or a word usage?
* If a sentence is joined, the phrasing changes. Should that be a word usage?
* If a sentence changes to using a abbreviation, is that convention? Should that be changed to correction?