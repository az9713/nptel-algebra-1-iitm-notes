# Lecture-note production workflow

This independent edition follows all 46 entries in the supplied playlist for
Jaikrishnan J's **Algebra 1: Foundations**, IIT Palakkad. IIT Madras coordinates
the NPTEL offering; it is not the lecturer's institution. The repository name
retains the destination chosen by the project owner.

The playlist is shuffled in blocks. The authoritative order is the 45 lessons
in the official NPTEL course page's `courseOutline.units[].lessons[]`, with the
course introduction prepended. Both teaching order and original playlist
position are recorded in `source-manifest.json`. Reversing the playlist is not
an adequate ordering rule.

Production follows the `transcript-grounded-textbook`, `rigorous-explainer`,
`science-editor`, and book-planning portions of `stem-textbook` skills. The owner
explicitly authorized autonomous completion, public GitHub publication, and
GitHub Pages, including routine editorial repairs. All project work remains
inside the current project directory.

1. Preserve the playlist, official course outline, and best available English
   captions privately under `work/`. Record hashes, timing, language, and track
   labels. Publisher labels do not establish human authorship or accuracy.
2. Read complete Stanford CS229 and NPTEL mathematical-foundations exemplars.
   Calibrate explanatory depth, theorem hypotheses, examples, code contracts,
   source integration, worked solutions, and the offline reader.
3. Plan chapter dependencies and common notation before drafting. Read each
   assigned transcript sequentially. Preserve substantive topic changes and
   source distinctions in section ledgers. Timestamp links identify related
   discussion, rather than attributing original proofs and examples to NPTEL.
4. Write independent textbook exposition directly in chapter manuscripts.
   Define objects before use; prove central results under explicit hypotheses;
   develop concrete cases and counterexamples. Integrate inspected primary
   mathematical references beside relevant results.
5. Develop a complete representative chapter before expanding the edition.
   Review proofs and every worked solution, then check book-wide dependencies,
   notation, and boundaries. Editorial judgments and mechanical checks retain
   separate evidence records.
6. Reuse the shared NPTEL reader and bundled MathJax. Execute Python listings
   and compare their outputs. Check mathematics, links, timestamp bounds,
   desktop/mobile layouts, navigation, search, theme, solutions, and print.
7. Audit the public inventory; exclude raw captions, downloaded references,
   logs, and private reviews. Reproduce the edition from a clean Git export
   inside `work/`. Commit and push only the public deliverables, enable Pages,
   and verify the served edition.

Full-source text reading, editorial review, executable finite checks, browser
checks, clean-export reproduction, and live publication have different scopes.
No finite computation constitutes a proof of an infinite theorem. Comprehensive
audiovisual review, human expert certification, and formal proof verification
are not claimed. Evidence summaries must state the checks actually performed.
