# Anti-slop checklist

This plugin produces two kinds of writing: the skill files themselves, and the client-facing reports the skills generate (the assessment and validation HTML). Both should read like a sharp data engineer wrote them, not like generic AI filler. Use this checklist when authoring or editing either.

The goal is not to ban words mechanically. It is to keep the writing direct, specific, and trustworthy — slop reads as careless, and careless is the opposite of what a data-engineering deliverable should signal.

## What to cut

- **Em-dashes used as a tic.** A stray em-dash is fine; a paragraph held together by three of them is a slop tell. Prefer a period or a colon.
- **The "this is not X, it's Y" cadence.** "This isn't just a pipeline, it's a platform." Say the thing plainly instead.
- **Filler verbs and adjectives:** *leverage, delve, robust, seamless, unlock, supercharge, powerful, cutting-edge, in today's fast-paced world, it's worth noting that.* Replace with the concrete action.
- **Choppy one-line drama.** Stacks of three-word sentences for effect. Combine them into real sentences.
- **Hedging throat-clearing:** "It's important to note", "As you can see", "Simply put". Delete and start with the point.
- **Restating the heading.** If a section is called "Security", don't open with "When it comes to security…".

## What to keep

- Concrete nouns and exact values: field names, status codes, env-var names, row counts.
- The reasoning behind an instruction. Explain *why* a step matters so the agent can adapt, rather than piling on `ALWAYS`/`NEVER`.
- Short where short is honest, longer where the idea needs room. Vary sentence length naturally.

## Quick self-check before committing

Read the file once out loud in your head. If a sentence could appear in any product's marketing copy unchanged, it's slop — rewrite it to say something only true of this artifact. If you can delete a sentence and lose no information, delete it.
