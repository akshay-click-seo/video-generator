
import io
from pathlib import Path
import numpy as np
import streamlit as st
from PIL import Image, ImageOps, ImageFilter
import imageio.v2 as imageio

st.set_page_config(page_title="Dubai 3D Pop-Out Generator", page_icon="🏙️", layout="wide")

RATIOS = {
    "9:16 — Reel": (720, 1280),
    "1:1 — Feed": (900, 900),
    "16:9 — Landscape": (1280, 720),
}

BG_COLORS = {
    "Dubai Blue Hour": ((15, 31, 58), (78, 105, 145)),
    "Dubai Sunset": ((39, 24, 53), (226, 132, 69)),
    "Dubai Night": ((7, 14, 29), (32, 60, 103)),
    "Luxury Gold": ((24, 25, 31), (121, 91, 45)),
}

def gradient_bg(size, top, bottom):
    w, h = size
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    for y in range(h):
        t = y / max(1, h - 1)
        arr[y, :, :] = [int(top[i] * (1-t) + bottom[i] * t) for i in range(3)]
    return Image.fromarray(arr, "RGB")

def add_skyline(bg, seed=7):
    rng = np.random.default_rng(seed)
    w, h = bg.size
    draw = __import__("PIL").ImageDraw.Draw(bg, "RGBA")
    base = int(h * 0.73)
    x = -20
    while x < w:
        bw = int(rng.integers(max(25, w//35), max(45, w//12)))
        bh = int(rng.integers(h*0.08, h*0.30))
        y = base - bh
        draw.rounded_rectangle((x, y, x+bw, base+20), radius=5,
                               fill=(18, 25, 39, 220))
        # windows
        for wx in range(x+7, x+bw-5, 11):
            for wy in range(y+9, base-4, 16):
                if rng.random() > .35:
                    draw.rectangle((wx, wy, wx+3, wy+5), fill=(238, 193, 91, 145))
        x += bw + int(rng.integers(5, 14))
    # distant spire / landmark
    cx = int(w*.72)
    peak = int(h*.28)
    draw.polygon([(cx-14, base), (cx+14, base), (cx+3, peak), (cx, peak-80), (cx-3, peak)], fill=(13,22,37,235))
    draw.line((cx, peak-80, cx, peak-125), fill=(220,220,220,160), width=2)
    # water reflection
    for yy in range(base+25, h):
        alpha = max(0, int(65 - (yy-base)*0.7))
        draw.line((0, yy, w, yy), fill=(110,145,180,alpha), width=1)
    return bg

def make_background(name, size):
    top, bottom = BG_COLORS[name]
    bg = gradient_bg(size, top, bottom)
    return add_skyline(bg)

def fit_canvas(img, size):
    # Preserve transparent alpha if present.
    return ImageOps.contain(img, size, Image.Resampling.LANCZOS)

def paste_building(bg, building, scale, x_offset, y_offset):
    b = building.copy().convert("RGBA")
    target_w = max(10, int(bg.width * scale))
    target_h = int(b.height * target_w / b.width)
    b = b.resize((target_w, target_h), Image.Resampling.LANCZOS)
    x = int((bg.width - target_w)/2 + x_offset)
    y = int(bg.height - target_h + y_offset)
    bg.alpha_composite(b, (x, y))
    return bg

def remove_simple_background(img):
    # Lightweight local fallback. Works best on transparent PNGs.
    if img.mode in ("RGBA", "LA"):
        return img.convert("RGBA")
    return img.convert("RGBA")

def create_frame(building, size, bg_name, t, effect):
    bg = make_background(bg_name, size).convert("RGBA")

    # Slow camera move + dramatic growth.
    if effect == "3D Pop-Out":
        if t < .42:
            p = t / .42
            scale = .48 + .16 * p
            xoff = 0
            yoff = 0
        else:
            p = (t-.42)/.58
            scale = .64 + .72 * (p**1.65)
            xoff = 0
            yoff = -int(size[1]*.07*p)
    elif effect == "Extreme Pop-Out":
        scale = .48 + 1.45*(t**1.45)
        xoff = int(size[0]*.10*np.sin(t*4.0))
        yoff = -int(size[1]*.10*t)
    else:
        scale = .45 + .80*t
        xoff = 0
        yoff = -int(size[1]*.05*t)

    # Add a soft shadow to help sell depth.
    b = remove_simple_background(building)
    if b.getbbox():
        shadow = Image.new("RGBA", b.size, (0,0,0,0))
        alpha = b.getchannel("A").filter(ImageFilter.GaussianBlur(18))
        shadow.putalpha(alpha.point(lambda a: int(a*.42)))
        sh = shadow.resize((max(10,int(shadow.width*scale)), max(10,int(shadow.height*scale))), Image.Resampling.LANCZOS)
        sx = int((bg.width-sh.width)/2 + xoff + size[0]*.025)
        sy = int(bg.height-sh.height + yoff + size[1]*.015)
        bg.alpha_composite(sh, (sx, sy))

    paste_building(bg, b, scale, xoff, yoff)
    return bg.convert("RGB")

st.title("🏙️ Dubai 3D Pop-Out Video Generator")
st.caption("100% local effect generator — no Runway API, no credits, no paid video API.")

with st.sidebar:
    st.header("Video Settings")
    ratio_name = st.selectbox("Format", list(RATIOS.keys()))
    size = RATIOS[ratio_name]
    fps = st.selectbox("FPS", [24, 30], index=1)
    duration = st.selectbox("Duration", [5, 6, 8], index=1)
    bg_name = st.selectbox("Dubai Background", list(BG_COLORS.keys()))
    effect = st.selectbox("Effect", ["3D Pop-Out", "Cinematic Reveal", "Extreme Pop-Out"])
    seed = st.number_input("Background variation", 1, 9999, 7)

st.subheader("1. Upload Building")
building_file = st.file_uploader(
    "Upload a building PNG/JPG/WebP",
    type=["png","jpg","jpeg","webp"],
    help="Transparent PNG gives the cleanest result."
)

if building_file:
    building = Image.open(building_file).convert("RGBA")
    st.image(building, caption="Building", width=360)

    st.subheader("2. Preview")
    preview = create_frame(building, size, bg_name, 0.72, effect)
    st.image(preview, caption="Pop-out preview", use_container_width=True)

    if st.button("🎬 Generate MP4", type="primary", use_container_width=True):
        out = "/mnt/data/dubai_popout_free.mp4"
        frames = []
        total = fps * duration
        progress = st.progress(0)
        status = st.empty()

        writer = imageio.get_writer(
            out,
            fps=fps,
            codec="libx264",
            quality=7,
            pixelformat="yuv420p",
        )
        try:
            for i in range(total):
                t = i / max(1, total-1)
                frame = create_frame(building, size, bg_name, t, effect)
                writer.append_data(np.asarray(frame))
                if i % max(1, total//30) == 0:
                    progress.progress((i+1)/total)
                    status.write(f"Rendering frame {i+1}/{total}…")
        finally:
            writer.close()

        progress.progress(1.0)
        status.success("Video ready!")
        st.video(out)
        with open(out, "rb") as f:
            st.download_button(
                "⬇️ Download MP4",
                f,
                file_name="dubai_3d_popout.mp4",
                mime="video/mp4",
                use_container_width=True,
            )
else:
    st.info("Upload your building image to start.")
