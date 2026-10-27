# [un]prompted II Planner

A free, unofficial session planner for [[un]prompted II](https://unpromptedcon.org/agenda-10-2026/), the AI security practitioner conference in San Francisco, 27 to 29 October 2026.

## Open the planner

**https://pfortuna.github.io/unprompted2-planner/**

Nothing to install and no account. Open the link on your laptop or phone and start planning.

## Your data never leaves your browser

This is the part that matters most, so plainly:

- **No backend.** There is no server-side code, no database and no account. The planner is one static HTML file.
- **No tracking.** No analytics, no cookies, no third-party scripts, no fonts or images loaded from anywhere else.
- **No network requests after the page loads.** Your interests, picks, watch-later list and workshop tickets are saved only in your browser's local storage, on your device. Nothing is sent to GitHub, to the author, or to anyone else.
- **You can check it.** Open your browser's developer tools, go to the Network tab, and use the planner: after the initial page load you will see no requests.

The only request is the one that loads the page itself from GitHub Pages, which, like any web host, may keep standard access logs (for example IP address and time). After that, the page talks to no one. The only way your plan leaves your device is if you choose to export it.

## What it does

- **Rates every session for you.** Every topic starts as Neutral, so you get ratings straight away. Mark topics as Must, Like or Skip, choose your role, formats you favor (original research, live demos, open-source releases, case studies), a level and keywords, or start from a profile such as "Agent builder" or "Security leader".
- **Explains each rating,** for example "+ Agent sandboxing (must see)" or "− Centers on the speaker's own product".
- **Shows three reasons to attend each session, chosen for you.** Each session has a set of factual highlights from its abstract; the planner shows the three that best match your interests, so the list changes as you change your preferences.
- **Suggests one pick per time slot** across the two stages. Override any pick, or leave a slot free.
- **Handles workshops.** Mark the workshops you hold a ticket for, and their two-hour blocks replace the talks they overlap.
- **Builds your plan.** Save a calendar file (.ics) with every pick, add talks one by one to Google Calendar, copy the plan as text, and keep a watch-later list for talks you cannot attend.
- **Speaker bios** with their other talks and the public sources each bio came from.
- **Works offline.** Fonts and data are embedded in the one file. Save the page to your device and it works on a plane.
- **Moves with you.** Export and Import (on the My plan tab) carry your plan between browsers or devices.

## How the recommendations work

Each session was tagged from its published title and abstract with up to four topics (most central first), format signals and a level. Every topic starts as Neutral, which rates a session "Maybe". A Must topic raises a session most, a Like topic raises it some, a Skip topic lowers it, and a session's first topic counts more than the rest. Role, format preferences, level and keywords adjust the score. Talks centered on the speaker's own commercial product are always rated lower.

The three reasons to attend are chosen the same way: each highlight is tagged with the topics, formats and audience it speaks to, and the ones closest to your preferences come first.

A rating means fit with what you told the planner, not talk quality. The tags were assigned with AI assistance and may be imperfect; corrections are welcome.

## Sources and content

Talk titles, speakers, affiliations, abstracts and workshop descriptions are reproduced from the [official agenda](https://unpromptedcon.org/agenda-10-2026/) and [workshops page](https://unpromptedcon.org/workshops/) as published on 24 October 2026, for attendees' convenience. That content belongs to the conference and its speakers and is not covered by this repository's license. The agenda is subject to change; the official site is the reference.

Speaker bios were compiled from public sources with AI assistance and appear only where the speaker's identity was confirmed by more than one source. Each bio lists its sources. If something about you is wrong, or you would like it removed, please open an issue.

This project is not affiliated with or endorsed by the [un]prompted organizers.

## Repository layout

```
index.html                  the planner, the file GitHub Pages serves (generated)
build/
  build.py                  regenerates index.html
  template.html             page markup, styles and logic
  planner-data.json         agenda, tags and bios
  fonts.css                 embedded web fonts
  fonts-licenses/           SIL Open Font License texts for the fonts
.nojekyll                   tells GitHub Pages to serve files as they are
```

## Making changes

`index.html` is generated, so edit the sources and rebuild:

1. Agenda fixes (a moved talk, a wrong tag, a bio correction): edit `build/planner-data.json`. Page behavior or design: edit `build/template.html`.
2. Run `python3 build/build.py` (Python 3, no dependencies).
3. Commit the source change together with the regenerated `index.html`.

Visitors' plans live in their browsers and reference session ids, slot times and the storage key `unprompted2-public-v1`. To keep everyone's saved plan working across updates:

- Never rename the storage key or change the id of an existing talk or workshop. To move a talk, change its time and keep its id; a pick that no longer fits its slot falls back to the suggestion while the rest of the plan stays.
- If the saved format ever has to change, bump `STATE_V` in `template.html` and migrate the stored object on load. The page never discards a plan it cannot read: it keeps a backup copy and stops saving for that visit.

To try it locally, run `python3 -m http.server 8765` in the repository folder and open http://127.0.0.1:8765/, or simply open `index.html` in a browser.

## Fonts

The page embeds [Bricolage Grotesque](https://github.com/ateliertriay/bricolage), [IBM Plex Sans and IBM Plex Mono](https://github.com/IBM/plex), all under the SIL Open Font License 1.1. The license texts are in `build/fonts-licenses/`.

## Author

Made by [Pedro Fortuna](https://www.linkedin.com/in/pedrofortuna/), CTO and co-founder of [Jscrambler](https://jscrambler.com).

## License

The code is released under the [MIT License](LICENSE).
