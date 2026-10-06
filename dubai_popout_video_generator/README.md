
# Dubai 3D Pop-Out Video Generator

A Streamlit app that turns a luxury building image into a cinematic Dubai real-estate pop-out video using the Runway API.

## 1. Requirements

- Python 3.8+
- A Runway Dev API key
- Internet connection

Runway's Python SDK supports Python 3.8+.

## 2. Install

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

If `python3` is unavailable, install Python 3.11/3.12 first.

## 3. Add your Runway API key

### macOS/Linux

```bash
export RUNWAYML_API_SECRET="YOUR_RUNWAY_API_KEY"
```

### Or Streamlit secrets

Create:

```text
.streamlit/secrets.toml
```

and add:

```toml
RUNWAYML_API_SECRET = "YOUR_RUNWAY_API_KEY"
```

Never upload your API key to GitHub.

## 4. Run

```bash
streamlit run app.py
```

Then open the local URL shown by Streamlit.

## 5. Best input

Use a transparent PNG of the building. The building should be:
- centered
- high resolution
- cleanly cut out
- without text or logos

## 6. Output formats

- 9:16 — Reels / Stories
- 1:1 — Feed
- 16:9 — YouTube / Website

## Important

The first version sends the building image as the video model's first-frame reference. The AI creates the cinematic environment and pop-out motion from the prompt.

For a more controlled production version, add a two-stage pipeline:
1. Generate/select the Dubai background.
2. Automatically composite the exact transparent building over it.
3. Send the final composite to image-to-video.

That version gives much stronger control over the exact placement of the building and background.
