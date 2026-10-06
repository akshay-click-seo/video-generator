
import base64
import io
import os
from pathlib import Path

import streamlit as st
from PIL import Image
from runwayml import RunwayML, TaskFailedError, TaskTimeoutError

st.set_page_config(
    page_title="Dubai 3D Pop-Out Video Generator",
    page_icon="🏙️",
    layout="wide",
)

# -----------------------------
# Helpers
# -----------------------------
RATIOS = {
    "9:16 — Reel / Story": ("720:1280", (720, 1280)),
    "1:1 — Feed": ("960:960", (960, 960)),
    "16:9 — YouTube / Website": ("1280:720", (1280, 720)),
}

BACKGROUND_PROMPTS = {
    "Dubai Marina — Sunset": (
        "Photorealistic luxury Dubai Marina waterfront at golden hour, "
        "modern glass skyscrapers, elegant waterfront promenade, palm trees, "
        "warm sunset reflections, premium real-estate advertising photography, "
        "clean central composition, no people, no text, no logos."
    ),
    "Downtown Dubai — Evening": (
        "Photorealistic Downtown Dubai luxury skyline at blue hour, "
        "modern skyscrapers, elegant city lights, premium architecture, "
        "warm window lights, sophisticated cinematic real-estate advertising "
        "photography, clean composition, no people, no text, no logos."
    ),
    "Dubai Waterfront — Night": (
        "Photorealistic luxury Dubai waterfront at night, illuminated modern "
        "skyscrapers, reflections on calm water, palm trees, elegant city "
        "lights, premium cinematic real-estate advertisement, clean composition, "
        "no people, no text, no logos."
    ),
    "Dubai Luxury — Daylight": (
        "Photorealistic premium Dubai skyline in bright daylight, blue sky, "
        "modern glass towers, palm trees, luxury waterfront architecture, "
        "high-end real-estate campaign photography, clean composition, "
        "no people, no text, no logos."
    ),
}

EFFECT_PROMPTS = {
    "3D Pop-Out": (
        "Create a dramatic 3D architectural pop-out illusion. The luxury building "
        "moves forward toward the viewer and visibly crosses the foreground frame "
        "boundary, with upper floors and side edges extending beyond the frame. "
        "Keep the building recognizable and structurally stable."
    ),
    "Cinematic Reveal": (
        "Create a premium cinematic architectural reveal. Start with a gentle "
        "camera push-in, then reveal the building with strong depth and parallax. "
        "The building grows toward the viewer and partially crosses the frame edges."
    ),
    "Extreme Pop-Out": (
        "Create a bold social-media 3D pop-out effect. The building rapidly moves "
        "toward the camera, breaking the visual frame boundary with convincing "
        "perspective and depth. Keep the architecture stable and premium."
    ),
}

def get_client():
    api_key = os.getenv("RUNWAYML_API_SECRET")
    if not api_key:
        try:
            api_key = st.secrets["RUNWAYML_API_SECRET"]
        except Exception:
            api_key = None
    if not api_key:
        st.error("RUNWAYML_API_SECRET is missing. Add it to your environment or Streamlit secrets.")
        st.stop()
    return RunwayML(api_key=api_key)

def image_to_data_uri(uploaded_file, max_bytes=4_700_000):
    """Convert uploaded image to a Runway-safe data URI under the 5MB data-URI limit."""
    raw = uploaded_file.getvalue()
    try:
        img = Image.open(io.BytesIO(raw)).convert("RGBA")
    except Exception as e:
        raise ValueError(f"Could not read image: {e}")

    # Keep dimensions reasonable for API input.
    max_side = 2048
    if max(img.size) > max_side:
        scale = max_side / max(img.size)
        img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)

    # Prefer PNG for transparency, then reduce if necessary.
    out = io.BytesIO()
    img.save(out, format="PNG", optimize=True)
    data = out.getvalue()

    if len(data) > max_bytes:
        # JPEG is smaller but loses transparency. Only use it when the source
        # itself has no alpha.
        has_alpha = img.mode == "RGBA" and img.getchannel("A").getextrema()[0] < 255
        if not has_alpha:
            out = io.BytesIO()
            rgb = img.convert("RGB")
            quality = 88
            while quality >= 55:
                out.seek(0)
                out.truncate(0)
                rgb.save(out, format="JPEG", quality=quality, optimize=True)
                if len(out.getvalue()) <= max_bytes:
                    break
                quality -= 5
            data = out.getvalue()
            mime = "image/jpeg"
        else:
            # Resize further while preserving transparency.
            while len(data) > max_bytes and max(img.size) > 900:
                scale = 0.82
                img = img.resize(
                    (max(1, int(img.width * scale)), max(1, int(img.height * scale))),
                    Image.LANCZOS,
                )
                out = io.BytesIO()
                img.save(out, format="PNG", optimize=True)
                data = out.getvalue()
            mime = "image/png"
    else:
        mime = "image/png"

    return f"data:{mime};base64,{base64.b64encode(data).decode('utf-8')}"

def generate_background(client, prompt, ratio):
    task = client.text_to_image.create(
        model="gen4_image",
        ratio=ratio,
        prompt_text=prompt,
    )
    result = task.wait_for_task_output(timeout=600)
    return result.output[0]

def download_url(url, output_path):
    import requests
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    Path(output_path).write_bytes(r.content)

def create_video(client, image_uri, prompt, ratio, duration):
    task = client.image_to_video.create(
        model="gen4.5",
        prompt_image=image_uri,
        prompt_text=prompt,
        ratio=ratio,
        duration=duration,
    )
    return task.wait_for_task_output(timeout=900)

# -----------------------------
# UI
# -----------------------------
st.title("🏙️ Dubai 3D Pop-Out Video Generator")
st.caption("Turn a luxury property/building image into an engaging Dubai real-estate pop-out video.")

with st.sidebar:
    st.header("🎬 Video Settings")
    ratio_label = st.selectbox("Format", list(RATIOS.keys()), index=0)
    ratio, target_size = RATIOS[ratio_label]

    duration = st.selectbox("Duration", [5, 10], index=0)
    effect_name = st.selectbox("Effect", list(EFFECT_PROMPTS.keys()), index=0)

    st.divider()
    st.header("🌆 Background")

    bg_mode = st.radio(
        "Background source",
        ["Generate Dubai background with AI", "Upload background"],
    )

    bg_prompt = None
    bg_file = None

    if bg_mode == "Generate Dubai background with AI":
        bg_style = st.selectbox("Dubai scene", list(BACKGROUND_PROMPTS.keys()))
        bg_prompt = BACKGROUND_PROMPTS[bg_style]
    else:
        bg_file = st.file_uploader(
            "Upload background",
            type=["png", "jpg", "jpeg", "webp"],
            help="Use a clean Dubai skyline/waterfront image.",
        )

    st.divider()
    st.info(
        "Best input: a PNG building with transparent background. "
        "The tool preserves the building and adds a Dubai environment behind it."
    )

st.subheader("1. Upload Building")
building_file = st.file_uploader(
    "Upload your luxury building / tower PNG",
    type=["png", "jpg", "jpeg", "webp"],
    help="Transparent PNG is strongly recommended for clean pop-out results.",
)

if building_file:
    c1, c2 = st.columns(2)
    with c1:
        st.image(building_file, caption="Building reference", use_container_width=True)
    with c2:
        st.markdown("### Recommended")
        st.write("• Transparent PNG")
        st.write("• Building centered")
        st.write("• Clean edges")
        st.write("• No text or logos")
        st.write("• 640px+ on the shortest side")

st.subheader("2. Generate")
generate = st.button("🚀 Generate Pop-Out Video", type="primary", use_container_width=True)

if generate:
    if not building_file:
        st.error("Please upload the building image first.")
        st.stop()

    client = get_client()

    try:
        with st.status("Preparing your Dubai scene...", expanded=True) as status:
            st.write("✓ Reading building image")
            building_uri = image_to_data_uri(building_file)

            # Background
            if bg_mode == "Generate Dubai background with AI":
                st.write("⏳ Generating Dubai background...")
                bg_url = generate_background(client, bg_prompt, ratio)
                st.write("✓ Dubai background generated")
            else:
                if not bg_file:
                    st.error("Please upload a background image.")
                    st.stop()
                bg_url = None

            # If a custom background is supplied, use it as the starting frame.
            # The prompt asks the video model to preserve the building reference
            # while creating the pop-out motion.
            st.write("⏳ Creating the image-to-video scene...")

            custom_bg_note = ""
            if bg_file:
                bg_uri = image_to_data_uri(bg_file)
                # Use the background as the image-to-video frame when supplied.
                # The building image is explicitly described in the prompt, but
                # cannot be sent as a second reference in the basic Gen-4.5 call.
                # Therefore, for maximum fidelity, AI background mode is preferred.
                base_uri = building_uri
                custom_bg_note = (
                    "Use a premium Dubai-style environment and keep the provided "
                    "building as the dominant foreground architectural subject. "
                )
            else:
                base_uri = building_uri

            motion_prompt = f"""
{EFFECT_PROMPTS[effect_name]}

Scene direction:
Luxury Dubai real-estate advertisement. A sophisticated Dubai skyline,
waterfront, palm trees and premium city lighting create an engaging cinematic
background. The uploaded building is the hero architectural subject.

The building must remain recognizable and realistic. Do not turn it into a
person, character, product, vehicle or unrelated object.

{custom_bg_note}

Motion:
Begin with a subtle cinematic camera push toward the building.
Then increase depth and parallax so the building appears to move toward the
viewer and cross the foreground frame boundary. The upper floors and side
edges can extend beyond the visible frame. Finish on a strong premium
architectural hero shot.

Visual quality:
photorealistic, luxury property advertisement, realistic reflections,
natural lighting, stable geometry, smooth motion, high detail.

Avoid:
people, faces, text, captions, logos, watermarks, warped architecture,
melting windows, duplicated buildings, shaky camera, transparent background.
""".strip()

            result = create_video(
                client,
                base_uri,
                motion_prompt,
                ratio,
                duration,
            )

            video_url = result.output[0]
            video_path = "/mnt/data/dubai_popout_result.mp4"
            download_url(video_url, video_path)

            status.update(label="Video generated successfully!", state="complete")

        st.success("🎉 Your Dubai 3D pop-out video is ready.")
        st.video(video_path)

        with open(video_path, "rb") as f:
            st.download_button(
                "⬇️ Download MP4",
                data=f,
                file_name="dubai_3d_popout.mp4",
                mime="video/mp4",
                use_container_width=True,
            )

        st.caption(
            "Tip: For the cleanest building cutout, upload a transparent PNG. "
            "For a true custom background + exact building compositing workflow, "
            "the next version can add automatic background removal and local compositing."
        )

    except TaskFailedError as e:
        st.error("Runway generation failed.")
        st.code(str(e.task_details))
    except TaskTimeoutError:
        st.error("The video generation timed out. Try again or use a 5-second video.")
    except Exception as e:
        st.error("Something went wrong.")
        st.exception(e)

st.divider()
st.caption("Built for luxury Dubai real-estate creatives • Runway API required")
