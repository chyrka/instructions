# Omniverse Set Up — AWS G5 deck

Slides for the **Omniverse Set-Up-demo.pptx** template, extended from the Azure-only
flow to AWS G5 (NVIDIA A10G). Built in the template's visual style: green bokeh section
dividers with a white bottom-left title, and white content slides with a centered bold
title, page number, NVIDIA mark and green edge bar in the footer.

| File | Purpose |
|------|---------|
| `OMNIVERSE_SETUP_AWS_G5.pptx` | Generated deck (27 slides, speaker notes included) |
| `OMNIVERSE_SETUP_AWS_G5.pdf` | PDF export for quick review |
| `OMNIVERSE_SETUP_AWS_G5.md` | Content source (slide text + speaker notes) |
| `build_deck.py` | Layout / generator script (`python-pptx`) |
| `assets/` | Section background, footer mark, AWS console screenshot |

## Rebuild

```bash
pip install python-pptx Pillow
python3 build_deck.py
```

## Merging into the original template

The original PPTX was not available, so the deck is a standalone file. To bring the new
slides into `Omniverse Set-Up-demo.pptx`:

1. Open both files in PowerPoint.
2. In the generated deck, select the slides you need in the thumbnail pane and copy.
3. In the template, right-click between slides → **Paste** → choose **Use Destination Theme**
   (keeps the template master) or **Keep Source Formatting** (keeps the exact look here).
4. Page numbers are live `slidenum` fields, so they renumber automatically.

## Slide map (generated deck → Markdown source)

| # | Slide | Source | New for AWS? |
|---|-------|--------|--------------|
| 1 | Title | Slide 1 | |
| 2 | Agenda | Slide 2 | |
| 3 | Requesting quota increase (AWS) | Slide 3 | yes |
| 4 | Requesting quota increase — Azure parallel | Slide 3 | |
| 5 | Section: Launch virtual machine | Slide 4 | |
| 6 | Launch Azure virtual machine | Slide 5 | |
| 7 | Launch Azure VM — AWS mapping | Slide 6 | yes |
| 8 | Launch AWS instance (console screenshot) | Slide 7 | yes |
| 9 | Launch AWS instance — G5 family | Slide 7 | yes |
| 10 | Launch AWS instance — EC2 console checklist | Slide 7 | yes |
| 11 | Launch AWS instance — Security Group | Slide 8 | yes |
| 12 | Launch AWS instance — drivers on G5 | Slide 8 | yes |
| 13 | Launch VM with NVIDIA GPU driver | Slide 9 | |
| 14 | NVIDIA GPU driver | Slide 10 | |
| 15 | Install NVIDIA driver (verify with `nvidia-smi`) | Slide 11 | |
| 16 | Section: Install CUDA Toolkit | Slide 12 | |
| 17 | Install CUDA Toolkit | Slide 13 | |
| 18 | Install CUDA Toolkit — verify | Slide 14 | |
| 19 | Section: Omniverse Kit | Slide 15 | |
| 20 | Launch Omniverse Kit | Slide 16 | |
| 21 | Launch Omniverse Kit — first-run wizard | Slide 17 | |
| 22 | Launch Omniverse Kit — UI loaded | Slide 18 | |
| 23 | Section: References | Slide 19 | |
| 24 | References | Slide 20 | |
| 25 | Thank you | Slide 21 | |
| 26 | Appendix — running this in production | Ops appendix | yes |
| 27 | Appendix — first-run validation checklist | Ops appendix | yes |
