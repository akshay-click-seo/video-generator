
# Dubai 3D Pop-Out Video Generator — FREE

This version removes Runway completely.

It creates a local cinematic 3D pop-out effect using:
- Python
- Streamlit
- Pillow
- NumPy
- ImageIO + FFmpeg

No Runway API key and no paid video API are required.

## Run locally

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Cloud

Upload these files to your GitHub repository:

```text
app.py
requirements.txt
```

Then set Main file path to:

```text
app.py
```

No Streamlit Secrets are needed.

## Important

This is a procedural 3D/parallax-style effect, not an AI video model.
For the strongest result, upload a clean transparent PNG of the building.

If FFmpeg is unavailable on a deployment environment, imageio-ffmpeg
bundles an FFmpeg executable and should normally handle MP4 creation.
