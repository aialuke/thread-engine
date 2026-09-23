# thread-engine

Local factory for Hidden Settings X threads. Drafts are the product. Posting is gated.

## Cycle

1. `grok`
2. `/plan` then `/draft-thread smart-tv`
3. Edit the markdown
4. Take the real screenshots listed in `images.md`
5. `touch drafts/<slug>/APPROVED`
6. Only then consider posting (manual, or a later script)

A human creates `APPROVED`. The agent never writes that file.

## Commands

`python3 scripts/draft.py smart-tv` prints `grok -p "/draft-thread smart-tv"`. Run `/plan` in that session first. The script does not start grok.

`python3 scripts/post_thread.py drafts/2026-09-22-smart-tv` writes `POST.txt` and prints that run sheet once `APPROVED` exists. Until then it prints `human gate` and exits 2. The numbered cards are the posts. `thread.md` is not the payload.

`python3 scripts/post_thread.py drafts/2026-09-22-smart-tv --copy 1` copies the first card to the clipboard. Paste that into X. When the card has an image, Finder shows that file. The script does not call the X API.
