# Markdown dev-editor

## Idea

### Markdown generator
> A dev tool where you can pick block elements and connect open APIs.
> You can change the style and the color palette. The palette could also be taken straight from the photo the user has on GitHub (their profile avatar).

## Features (to-do)

### Editor
- [ ] Block library: header/banner, about me, tech stack, GitHub stats, top languages, projects, socials, latest posts, contribution graph, quote, visitor counter
- [ ] Add, remove and reorder blocks with drag & drop
- [ ] Settings panel for each block (text, links, alignment, size)
- [ ] Live preview that looks like GitHub's rendering
- [ ] Switch between visual mode and raw Markdown mode
- [ ] Undo / redo
- [ ] Ready-made templates to start from

### Open API integrations
- [ ] GitHub API: profile, repos, stars, languages, contributions
- [ ] Latest blog posts from RSS / dev.to / Medium
- [ ] WakaTime coding stats
- [ ] Spotify / Last.fm "now playing"
- [ ] Generic "custom API" block: URL + field mapping to text
- [ ] Store API tokens safely and cache responses to stay under rate limits

### Style
- [ ] Theme presets (minimal, dark, retro, neon, ...)
- [ ] Badge style (flat, plastic, for-the-badge)
- [ ] Light/dark versions that follow the viewer's GitHub theme
- [ ] Layout options: one column, two columns, centered
- [ ] Note: GitHub strips CSS and JS from READMEs, so custom styles have to be built into generated SVG images and badges

### Color palette
- [ ] Manual palette editor (primary, accent, background, text)
- [ ] Palette presets
- [ ] Extract a palette from the user's GitHub avatar
- [ ] Contrast check (readable in light and dark mode)
- [ ] Apply the palette to all blocks, badges and SVG cards at once

### Export & publish
- [ ] Copy Markdown to clipboard
- [ ] Download `README.md`
- [ ] Sign in with GitHub and commit straight to the `<username>/<username>` profile repo
- [ ] Generate a GitHub Action that rebuilds the README on a schedule (for example, nightly)
- [ ] Save the setup as a config file so it can be edited again later

### Later
- [ ] Share templates with other users
- [ ] Animated SVG blocks
- [ ] Multi-language README support
