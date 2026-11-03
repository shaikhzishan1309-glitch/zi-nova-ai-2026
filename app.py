import os
import io
import base64
import json
import requests
import tempfile
import subprocess
import math
import random
import re
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from PIL import Image, ImageOps
from dotenv import load_dotenv
from groq import Groq
from gtts import gTTS
from google import genai


# ============================================================
# 1. CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
LOGO_PATH = ASSETS_DIR / "zinova_ai_logo.png"

load_dotenv(BASE_DIR / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
IMAGE_MODEL = os.getenv("GEMINI_IMAGE_MODEL", "gemini-3-pro-image").strip()
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "").strip()
CLOUDFLARE_IMAGE_MODEL = "@cf/black-forest-labs/flux-1-schnell"
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "").strip()
POLLINATIONS_IMAGE_MODEL = os.getenv("POLLINATIONS_IMAGE_MODEL", "flux").strip()

TEXT_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "qwen/qwen3.8-27b")

MAX_IMAGE_MB = 10
MAX_AUDIO_MB = 25

st.set_page_config(
    page_title="Zi Nova AI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# 2. SESSION STATE
# ============================================================

DEFAULTS = {
    "page": "Home",
    "theme": "Midnight Dark",
    "messages": [],
    "web_on": True,
    "last_sources": [],
    "caption_result": None,
    "caption_sources": [],
    "generated_image": None,
    "reducer_result": None,
    "voice_result": None,
    "assistant_tab": "Chat Assistant",
    "chat_image": None,
    "chat_input_counter": 0
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# 3. THEMES
# ============================================================

THEMES = {
    "Midnight Dark": {
        "bg": "#070D18",
        "surface": "#101D30",
        "card": "#13243B",
        "text": "#F4F7FF",
        "muted": "#A9BCD5",
        "border": "#2B4565",
        "accent": "#32B9E9",
        "sidebar": "#081322"
    },
    "Professional Light": {
        "bg": "#F1F5F9",
        "surface": "#FFFFFF",
        "card": "#FFFFFF",
        "text": "#172033",
        "muted": "#64748B",
        "border": "#D8E1EC",
        "accent": "#087DB5",
        "sidebar": "#E6EDF5"
    },
    "Royal Purple": {
        "bg": "#100B1D",
        "surface": "#1C1530",
        "card": "#241B3B",
        "text": "#F5EFFF",
        "muted": "#C4B5FD",
        "border": "#493765",
        "accent": "#A78BFA",
        "sidebar": "#0B0715"
    },
    "Ocean Blue": {
        "bg": "#061522",
        "surface": "#0B2031",
        "card": "#102A40",
        "text": "#EFFAFF",
        "muted": "#A6C7D8",
        "border": "#28516B",
        "accent": "#38BDF8",
        "sidebar": "#04101C"
    }
}

T = THEMES[st.session_state.theme]


# ============================================================
# 4. GLOBAL CSS
# ============================================================

st.markdown(
    f"""
    <style>
    @import url(
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
    );

    html, body, [class*="css"] {{
        font-family: Inter, sans-serif;
    }}

    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"] {{
        background: {T["bg"]} !important;
        color: {T["text"]} !important;
    }}

    .block-container {{
        max-width: 1500px;
        padding-top: 1.5rem !important;
        padding-bottom: 3rem;
    }}

    header[data-testid="stHeader"] {{
        background: {T["bg"]} !important;
        border-bottom: 1px solid {T["border"]} !important;
    }}

    [data-testid="stToolbar"] {{
        background: transparent !important;
    }}

    [data-testid="stDecoration"] {{
        display: none !important;
    }}

    header[data-testid="stHeader"] button,
    header[data-testid="stHeader"] svg {{
        color: {T["text"]} !important;
        fill: {T["text"]} !important;
    }}

    /* SIDEBAR */

    [data-testid="stSidebar"] {{
        background: {T["sidebar"]} !important;
        border-right: 1px solid {T["border"]};
    }}

    [data-testid="stSidebar"] > div:first-child {{
        background: #05080F !important;
    }}

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {{
        color: #303544 !important;
        font-weight: 800 !important;
        letter-spacing: .3px;
    }}

    [data-testid="stSidebar"] [data-testid="stButton"] {{
        margin: 0 0 10px 0 !important;
    }}

    [data-testid="stSidebar"] [data-testid="stButton"] > button {{
        width: 100% !important;
        min-height: 51px !important;
        border-radius: 10px !important;
        border: 1px solid #42BDEB !important;
        background: linear-gradient(
            105deg,
            #278FCB 0%,
            #35B7E1 100%
        ) !important;
        color: #FFFFFF !important;
        font-size: 15px !important;
        font-weight: 700 !important;
        box-shadow: none !important;
        transition: filter .15s ease, transform .15s ease;
    }}

    [data-testid="stSidebar"] [data-testid="stButton"] > button:hover {{
        filter: brightness(1.08);
        border-color: #83DFFF !important;
        color: #FFFFFF !important;
        transform: translateY(-1px);
    }}

    [data-testid="stSidebar"] [data-testid="stButton"] > button:focus {{
        box-shadow: 0 0 0 2px rgba(53, 183, 225, .25) !important;
        color: #FFFFFF !important;
    }}

    /* HERO */

    .hero {{
        background:
            radial-gradient(
                ellipse at 50% 0%,
                rgba(35,145,220,.27),
                transparent 65%
            ),
            linear-gradient(145deg,#071a2b,#050b14);
        border: 1px solid #25445e;
        border-radius: 18px;
        padding: 58px 25px;
        text-align: center;
        margin-bottom: 28px;
    }}

    .eyebrow {{
        color: #55C6ED;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 3px;
        margin-bottom: 20px;
    }}

    .hero h1 {{
        color: #F5FAFF;
        font-size: clamp(34px,5vw,60px);
        font-weight: 800;
        letter-spacing: -2px;
        line-height: 1.15;
        margin-bottom: 18px;
    }}

    .hero h1 span {{
        background: linear-gradient(90deg,#D9F4FF,#67C8F1,#42A9E9);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }}

    .hero p {{
        color: #A8BFD0;
        font-size: 15px;
        line-height: 1.8;
        max-width: 680px;
        margin: auto;
    }}

    .section-heading {{
        color: {T["text"]};
        font-size: 22px;
        font-weight: 800;
        margin: 26px 0 16px;
    }}

    .feature-card {{
        background: {T["card"]};
        border: 1px solid {T["border"]};
        border-radius: 14px;
        padding: 22px;
        min-height: 145px;
        margin-bottom: 14px;
    }}

    .feature-card h3 {{
        color: {T["text"]};
        font-size: 17px;
        margin: 8px 0;
    }}

    .feature-card p {{
        color: {T["muted"]};
        font-size: 13px;
        line-height: 1.7;
    }}

    .feature-icon {{
        font-size: 27px;
    }}

    .brand {{
        text-align: center;
        font-size: 25px;
        font-weight: 800;
        padding: 18px 0;
        color: {T["text"]};
    }}

    .brand span {{
        color: {T["accent"]};
    }}

    .mode-card {{
        background: linear-gradient(145deg,#10243C,#142E4A);
        border: 1px solid #355575;
        border-radius: 16px;
        padding: 20px;
        min-height: 140px;
        margin-bottom: 15px;
    }}

    .mode-card h3 {{
        color: #FFFFFF;
        margin: 10px 0;
    }}

    .mode-card p {{
        color: #B5C8DC;
        font-size: 13px;
        line-height: 1.6;
    }}

    .stButton > button,
    .stDownloadButton > button {{
        background: linear-gradient(110deg,#1689C8,#32B9E9);
        color: white;
        border: 1px solid #39B9E9;
        border-radius: 9px;
        min-height: 42px;
        font-weight: 700;
    }}

    .stButton > button:hover,
    .stDownloadButton > button:hover {{
        border-color: #8BE0FF;
        color: white;
    }}

    .stTextInput input,
    .stTextArea textarea {{
        background: {T["surface"]} !important;
        color: {T["text"]} !important;
        border: 1px solid {T["border"]} !important;
    }}

    [data-testid="stFileUploader"] {{
        background: {T["surface"]};
        border: 1px dashed {T["border"]};
        border-radius: 12px;
        padding: 10px;
    }}

    [data-testid="stChatMessage"] {{
        background: {T["surface"]};
        border: 1px solid {T["border"]};
        border-radius: 14px;
        padding: 12px;
        margin-bottom: 10px;
    }}

    /* CHAT INPUT — FORCE READABLE TEXT IN ALL STREAMLIT THEMES */
    [data-testid="stChatInput"],
    [data-testid="stChatInput"] > div,
    [data-testid="stChatInput"] [data-baseweb="textarea"],
    [data-testid="stChatInput"] [data-baseweb="base-input"] {{
        background: {T["surface"]} !important;
        border: 1px solid {T["border"]} !important;
        border-radius: 16px !important;
        box-shadow: none !important;
    }}

    [data-testid="stChatInput"] textarea,
    [data-testid="stChatInput"] textarea[data-testid="stChatInputTextArea"] {{
        background: transparent !important;
        color: {T["text"]} !important;
        -webkit-text-fill-color: {T["text"]} !important;
        caret-color: {T["text"]} !important;
        opacity: 1 !important;
        border: 0 !important;
        box-shadow: none !important;
        outline: none !important;
        font-size: 15px !important;
        line-height: 1.5 !important;
    }}

    [data-testid="stChatInput"] textarea::placeholder,
    [data-testid="stChatInput"] textarea[data-testid="stChatInputTextArea"]::placeholder {{
        color: {T["muted"]} !important;
        -webkit-text-fill-color: {T["muted"]} !important;
        opacity: 1 !important;
    }}

    [data-testid="stChatInput"] button,
    [data-testid="stChatInput"] button svg {{
        color: {T["accent"]} !important;
        fill: {T["accent"]} !important;
    }}

    .footer {{
        text-align: center;
        color: {T["muted"]};
        font-size: 11px;
        letter-spacing: 1px;
        padding: 25px 5px;
        border-top: 1px solid {T["border"]};
        margin-top: 35px;
    }}

    /* STREAMLIT TABS: PREVENT LABELS FROM BEING CLIPPED */
    [data-testid="stTabs"] {{
        overflow: visible !important;
        margin-top: 10px !important;
    }}

    [data-testid="stTabs"] [data-baseweb="tab-list"] {{
        overflow: visible !important;
        min-height: 56px !important;
        align-items: center !important;
        padding-top: 6px !important;
        padding-bottom: 2px !important;
    }}

    [data-testid="stTabs"] [data-baseweb="tab"] {{
        height: auto !important;
        min-height: 44px !important;
        line-height: 1.4 !important;
        padding: 11px 14px !important;
        white-space: nowrap !important;
    }}

    /* CHATGPT STYLE CHAT ASSISTANT */

    .zi-chat-header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 4px 0 20px 0;
        border-bottom: 1px solid {T["border"]};
        margin-bottom: 24px;
    }}

    .zi-chat-brand {{
        display: flex;
        align-items: center;
        gap: 11px;
    }}

    .zi-chat-logo {{
        width: 44px;
        height: 44px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 13px;
        background: #173653;
        color: #55C9F3;
        font-size: 24px;
        font-weight: 800;
    }}

    .zi-chat-title {{
        color: {T["text"]};
        font-size: 19px;
        font-weight: 700;
        line-height: 1.3;
    }}

    .zi-chat-subtitle {{
        color: {T["muted"]};
        font-size: 13px;
        margin-top: 2px;
    }}

    .zi-online {{
        background: #D8F8E5;
        color: #16834A;
        border-radius: 20px;
        padding: 5px 12px;
        font-size: 12px;
        font-weight: 700;
    }}

    .zi-welcome {{
        text-align: center;
        padding: 22px 0 26px 0;
    }}

    .zi-welcome h2 {{
        color: {T["text"]};
        font-size: 27px;
        font-weight: 700;
        letter-spacing: -.5px;
        margin: 0 0 10px 0;
    }}

    .zi-welcome p {{
        color: {T["muted"]};
        font-size: 15px;
        margin: 0;
    }}

    .zi-suggestion {{
        min-height: 106px;
        background: {T["surface"]};
        border: 1px solid {T["border"]};
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 10px;
    }}

    .zi-suggestion-icon {{
        color: {T["accent"]};
        font-size: 20px;
        margin-bottom: 8px;
    }}

    .zi-suggestion-title {{
        color: {T["text"]};
        font-size: 15px;
        font-weight: 700;
        margin-bottom: 5px;
    }}

    .zi-suggestion-desc {{
        color: {T["muted"]};
        font-size: 13px;
        line-height: 1.5;
    }}

    .zi-composer-label {{
        color: {T["muted"]};
        font-size: 13px;
        padding: 2px 0 5px 0;
    }}

    .zi-composer-tools {{
        display: flex;
        align-items: center;
        gap: 20px;
        color: {T["muted"]};
        font-size: 13px;
        padding-top: 4px;
    }}

    .zi-chat-note {{
        color: {T["muted"]};
        text-align: center;
        font-size: 11px;
        padding: 10px 0 0 0;
    }}

    .zi-message-user {{
        background: {T["card"]};
        border: 1px solid {T["border"]};
        border-radius: 18px 18px 4px 18px;
        padding: 13px 17px;
        margin: 10px 0 14px auto;
        max-width: 85%;
        width: fit-content;
        color: {T["text"]};
    }}

    .zi-message-assistant {{
        color: {T["text"]};
        padding: 10px 2px 20px 2px;
        line-height: 1.75;
        width: 100%;
    }}

    .zi-chat-actions {{
        display: flex;
        justify-content: space-between;
        gap: 10px;
        align-items: center;
        margin: 10px 0 18px 0;
    }}

    @media(max-width:700px) {{
        .hero {{
            padding: 35px 15px;
        }}

        .hero h1 {{
            font-size: 35px;
        }}

        .zi-welcome h2 {{
            font-size: 23px;
        }}

        .zi-message-user {{
            max-width: 95%;
        }}
    }}
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 5. HTML AND COMMON HELPERS
# ============================================================

def render_html(markup):
    st.html(markup)


def go_to_page(page):
    st.session_state.page = page


def get_logo_html():
    if not LOGO_PATH.exists():
        return None

    try:
        encoded = base64.b64encode(
            LOGO_PATH.read_bytes()
        ).decode("utf-8")

        ext = LOGO_PATH.suffix.lower()
        mime = "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/png"

        return f"""
        <div style="text-align:center;padding:15px 0;">
            <img
                src="data:{mime};base64,{encoded}"
                style="width:145px;max-width:90%;height:auto;"
                alt="Zi Nova AI"
            />
        </div>
        """
    except Exception:
        return None


def require_api_key():
    if not GROQ_API_KEY:
        st.error("Groq API key not found. Check your .env file.")
        return False
    return True


@st.cache_resource(show_spinner=False)
def get_groq_client(api_key):
    return Groq(
        api_key=api_key,
        timeout=90,
        max_retries=2
    )


def image_to_data_url(uploaded_file):
    if len(uploaded_file.getvalue()) > MAX_IMAGE_MB * 1024 * 1024:
        raise ValueError(f"Image must be smaller than {MAX_IMAGE_MB} MB.")

    image = ImageOps.exif_transpose(
        Image.open(uploaded_file)
    ).convert("RGB")

    image.thumbnail((1600, 1600))

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=88, optimize=True)

    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return "data:image/jpeg;base64," + encoded


# ============================================================
# 6. GEMINI IMAGE GENERATION
# ============================================================

def require_gemini_key():
    if not GEMINI_API_KEY:
        st.error(
            "Gemini API key not found. Add GEMINI_API_KEY to your .env file "
            "or Streamlit Cloud Secrets."
        )
        return False
    return True


def generate_ai_image(prompt, aspect_ratio="1:1", image_size="1K", reference_image=None):
    """Generate a new image or edit a supplied reference image with Gemini."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is missing.")

    client = genai.Client(api_key=GEMINI_API_KEY)

    request_input = prompt.strip()

    if reference_image is not None:
        reference_image.seek(0)
        raw_image = reference_image.read()
        mime = getattr(reference_image, "type", None) or "image/png"
        request_input = [
            {
                "type": "image",
                "data": base64.b64encode(raw_image).decode("utf-8"),
                "mime_type": mime
            },
            {"type": "text", "text": prompt.strip()}
        ]

    interaction = client.interactions.create(
        model=IMAGE_MODEL,
        input=request_input,
        response_format={
            "type": "image",
            "mime_type": "image/png",
            "aspect_ratio": aspect_ratio,
            "image_size": image_size
        }
    )

    output_image = getattr(interaction, "output_image", None)
    image_data = getattr(output_image, "data", None) if output_image else None

    if not image_data:
        # Compatibility fallback: inspect model-output steps.
        for step in getattr(interaction, "steps", []) or []:
            if getattr(step, "type", None) == "model_output":
                for block in getattr(step, "content", []) or []:
                    if getattr(block, "type", None) == "image":
                        image_data = getattr(block, "data", None)
                        if image_data:
                            break
            if image_data:
                break

    if not image_data:
        message = getattr(interaction, "output_text", None)
        raise RuntimeError(
            "Gemini did not return an image. "
            + (f"Model response: {message}" if message else "Try a clearer prompt.")
        )

    return base64.b64decode(image_data)


def cloudflare_image_dimensions(aspect_ratio="1:1"):
    """Return conservative FLUX.1 Schnell dimensions while preserving the ratio."""
    dimensions = {
        "1:1": (1024, 1024),
        "16:9": (1024, 576),
        "9:16": (576, 1024),
        "4:3": (1024, 768),
        "3:4": (768, 1024),
        "3:2": (1024, 672),
        "2:3": (672, 1024),
        "5:4": (1024, 832),
        "4:5": (832, 1024),
        "21:9": (1024, 448),
    }
    return dimensions.get(aspect_ratio, (1024, 1024))


def normalize_image_to_png(image_bytes):
    """Decode provider output and re-encode it as a valid PNG for preview/download."""
    try:
        with Image.open(io.BytesIO(image_bytes)) as source:
            source.load()
            image = ImageOps.exif_transpose(source)
            if image.mode not in ("RGB", "RGBA"):
                image = image.convert("RGBA" if "transparency" in image.info else "RGB")
            output = io.BytesIO()
            image.save(output, format="PNG", optimize=True)
            return output.getvalue()
    except Exception as exc:
        raise RuntimeError(
            "The image provider returned data that Pillow could not decode. "
            "Try another provider or generate the image again."
        ) from exc


def generate_cloudflare_image(prompt, aspect_ratio="1:1"):
    """Generate an image using Cloudflare Workers AI FLUX.1 Schnell."""
    if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
        raise ValueError(
            "Cloudflare credentials missing. Add CLOUDFLARE_ACCOUNT_ID and "
            "CLOUDFLARE_API_TOKEN to your .env file."
        )

    endpoint = (
        "https://api.cloudflare.com/client/v4/accounts/"
        f"{CLOUDFLARE_ACCOUNT_ID}/ai/run/{CLOUDFLARE_IMAGE_MODEL}"
    )
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json",
    }
    # FLUX.1 Schnell Workers AI schema accepts the prompt here;
    # width/height are rejected by this endpoint, so ratio is described in the prompt.
    payload = {"prompt": prompt.strip()}

    try:
        response = requests.post(
            endpoint, headers=headers, json=payload, timeout=(15, 180)
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Cloudflare connection failed: {exc}") from exc

    if not response.ok:
        try:
            details = response.json()
        except ValueError:
            details = response.text[:800]
        raise RuntimeError(
            f"Cloudflare returned HTTP {response.status_code}: {details}"
        )

    content_type = response.headers.get("Content-Type", "")
    if content_type.startswith("image/"):
        image_bytes = response.content
    else:
        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError("Cloudflare returned an unreadable response.") from exc

        if not data.get("success", False):
            raise RuntimeError(f"Cloudflare image generation failed: {data.get('errors', data)}")

        encoded = (data.get("result") or {}).get("image")
        if not encoded:
            raise RuntimeError("Cloudflare response did not contain an image.")
        try:
            image_bytes = base64.b64decode(encoded)
        except Exception as exc:
            raise RuntimeError("Cloudflare returned invalid image data.") from exc

    # Validate the returned bytes before showing them in Streamlit.
    try:
        with Image.open(io.BytesIO(image_bytes)) as check:
            check.verify()
    except Exception as exc:
        raise RuntimeError("Cloudflare response was not a valid image.") from exc

    return image_bytes


def generate_pollinations_image(prompt, aspect_ratio="1:1"):
    """Generate an image through the Pollinations image API."""
    if not POLLINATIONS_API_KEY:
        raise ValueError(
            "Pollinations API key missing. Add POLLINATIONS_API_KEY to your .env file."
        )

    width, height = cloudflare_image_dimensions(aspect_ratio)
    endpoint = "https://gen.pollinations.ai/image/" + requests.utils.quote(
        prompt.strip(), safe=""
    )
    headers = {
        "Authorization": f"Bearer {POLLINATIONS_API_KEY}"
    }
    params = {
        "model": POLLINATIONS_IMAGE_MODEL,
        "width": width,
        "height": height,
    }

    try:
        response = requests.get(
            endpoint,
            headers=headers,
            params=params,
            timeout=(15, 180)
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Pollinations connection failed: {exc}") from exc

    if not response.ok:
        detail = response.text[:1000]
        if response.status_code == 401:
            detail = "Authentication failed. Check POLLINATIONS_API_KEY."
        elif response.status_code == 402:
            detail = (
                "Pollinations reports insufficient available Pollen. "
                "Check your Quest Pollen balance and key restrictions."
            )
        raise RuntimeError(
            f"Pollinations returned HTTP {response.status_code}: {detail}"
        )

    content_type = response.headers.get("Content-Type", "")
    if not content_type.startswith("image/"):
        raise RuntimeError(
            "Pollinations did not return an image. "
            f"Content-Type: {content_type or 'unknown'}; "
            f"Response: {response.text[:500]}"
        )

    image_bytes = response.content
    try:
        with Image.open(io.BytesIO(image_bytes)) as check:
            check.verify()
    except Exception as exc:
        raise RuntimeError("Pollinations returned invalid image data.") from exc

    return image_bytes




# ============================================================
# FREE 2D HINDI CARTOON STUDIO — PROCEDURAL ANIMATION
# ============================================================

def _draw_cartoon_character(draw, cx, ground_y, frame_no, character, talking):
    """Draw an original, simple Indian 2D cartoon character with moving limbs."""
    palette = {
        "Village Hero": {"shirt": "#E94B35", "shorts": "#2563EB", "skin": "#C98552", "hair": "#241A18"},
        "Smart Girl": {"shirt": "#E85D9E", "shorts": "#6D45B5", "skin": "#B9784C", "hair": "#241A18"},
        "Funny Friend": {"shirt": "#F0B323", "shorts": "#168B68", "skin": "#D49A6A", "hair": "#30221D"},
    }
    c = palette.get(character, palette["Village Hero"])
    phase = frame_no * 0.22
    bob = int(math.sin(phase * 2) * 4)
    swing = math.sin(phase) * 17
    cx = int(cx)
    gy = ground_y + bob
    # legs and simple running/walking cycle
    hip_y = gy - 62
    draw.line((cx-12, hip_y, cx-18+swing, gy), fill="#5A3828", width=12)
    draw.line((cx+12, hip_y, cx+18-swing, gy), fill="#5A3828", width=12)
    draw.ellipse((cx-30+swing, gy-5, cx-8+swing, gy+7), fill="#3B2B26")
    draw.ellipse((cx+8-swing, gy-5, cx+30-swing, gy+7), fill="#3B2B26")
    # torso
    draw.rounded_rectangle((cx-30, gy-125, cx+30, gy-55), radius=17, fill=c["shirt"], outline="#472A25", width=3)
    # arms swing independently
    arm = math.sin(phase + 1.1) * 20
    draw.line((cx-25, gy-112, cx-43-arm, gy-75), fill=c["skin"], width=12)
    draw.line((cx+25, gy-112, cx+43+arm, gy-75), fill=c["skin"], width=12)
    draw.ellipse((cx-50-arm, gy-83, cx-36-arm, gy-69), fill=c["skin"])
    draw.ellipse((cx+36+arm, gy-83, cx+50+arm, gy-69), fill=c["skin"])
    # neck and head
    draw.rectangle((cx-9, gy-145, cx+9, gy-119), fill=c["skin"])
    draw.ellipse((cx-39, gy-205, cx+39, gy-132), fill=c["skin"], outline="#472A25", width=3)
    # hair cap + side tufts
    draw.pieslice((cx-41, gy-212, cx+41, gy-150), 180, 360, fill=c["hair"], outline="#241A18")
    draw.ellipse((cx-39, gy-184, cx-25, gy-164), fill=c["hair"])
    draw.ellipse((cx+25, gy-184, cx+39, gy-164), fill=c["hair"])
    # eyes and brows
    draw.ellipse((cx-22, gy-178, cx-9, gy-161), fill="white")
    draw.ellipse((cx+9, gy-178, cx+22, gy-161), fill="white")
    draw.ellipse((cx-17, gy-173, cx-11, gy-164), fill="#211B1B")
    draw.ellipse((cx+11, gy-173, cx+17, gy-164), fill="#211B1B")
    draw.arc((cx-24, gy-188, cx-7, gy-176), 190, 345, fill="#241A18", width=3)
    draw.arc((cx+7, gy-188, cx+24, gy-176), 190, 345, fill="#241A18", width=3)
    # mouth switches while narration is active; deliberately simple 2D lip-sync
    if talking:
        draw.ellipse((cx-9, gy-157, cx+9, gy-143), fill="#67252A", outline="#472A25", width=2)
    else:
        draw.arc((cx-12, gy-161, cx+12, gy-146), 10, 170, fill="#67252A", width=3)
    # cheek highlights
    draw.ellipse((cx-29, gy-157, cx-19, gy-151), fill="#E99A8B")
    draw.ellipse((cx+19, gy-157, cx+29, gy-151), fill="#E99A8B")


def _draw_cartoon_background(draw, frame_no):
    draw.rectangle((0, 0, 640, 360), fill="#8ED8F2")
    # sun and clouds
    draw.ellipse((520, 28, 580, 88), fill="#FFD45C")
    for x, y in [(75, 65), (270, 42), (430, 105)]:
        draw.ellipse((x, y, x+55, y+24), fill="#FFFFFF")
        draw.ellipse((x+18, y-13, x+48, y+24), fill="#FFFFFF")
    # distant hills
    draw.ellipse((-100, 190, 300, 410), fill="#77C66E")
    draw.ellipse((210, 175, 690, 410), fill="#5DBB67")
    # village huts
    for x in (55, 455):
        draw.rectangle((x, 205, x+105, 285), fill="#F5D59A", outline="#7A4A2D", width=3)
        draw.polygon([(x-10, 208), (x+52, 158), (x+115, 208)], fill="#B95D3D", outline="#7A3B2A")
        draw.rectangle((x+40, 235, x+66, 285), fill="#845234")
    # ground
    draw.rectangle((0, 285, 640, 360), fill="#79B94D")
    draw.line((0, 285, 640, 285), fill="#4D963F", width=4)
    # small flowers
    for x in range(25, 640, 75):
        yy = 315 + int(math.sin(frame_no * .1 + x) * 3)
        draw.ellipse((x, yy, x+7, yy+7), fill="#FFE66D")


def generate_free_hindi_cartoon(script_text, character="Village Hero", voice="hi", fps=20):
    """Create a procedural 2D cartoon MP4 with gTTS and FFmpeg.

    This is lightweight 2D procedural animation, not neural or phoneme-accurate
    lip-sync. FFmpeg stderr is written to a temporary log so an early encoder
    exit produces its real diagnostic instead of an unhelpful Broken pipe.
    """
    if not script_text or not script_text.strip():
        raise ValueError("Hindi story/dialogue likho pehle.")
    if len(script_text) > 2500:
        raise ValueError(
            "Free preview limit: 2,500 characters per video. "
            "Script ko scenes mein divide karo."
        )
    try:
        import imageio_ffmpeg
    except ImportError as exc:
        raise RuntimeError(
            "imageio-ffmpeg missing hai. requirements.txt update karke redeploy karo."
        ) from exc

    with tempfile.TemporaryDirectory(prefix="zi_cartoon_") as workdir:
        audio_path = os.path.join(workdir, "hindi_voice.mp3")
        output_path = os.path.join(workdir, "zi_hindi_cartoon.mp4")
        stderr_path = os.path.join(workdir, "ffmpeg_error.log")

        try:
            gTTS(text=script_text, lang=voice, slow=False).save(audio_path)
        except Exception as exc:
            raise RuntimeError(
                f"Hindi voice generate nahi hui. Internet/TTS connection check karo: {exc}"
            ) from exc

        if not os.path.isfile(audio_path) or os.path.getsize(audio_path) == 0:
            raise RuntimeError("Hindi TTS ne empty audio file return ki.")

        words = max(1, len(script_text.split()))
        # Render enough video for the estimated narration. Do not use FFmpeg
        # -shortest: it can stop reading raw frames as soon as short audio ends,
        # while Python is still writing frames, causing [Errno 32] Broken pipe.
        frame_count = min(3600, max(240, int((words / 1.15 + 12) * fps)))

        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        command = [
            ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
            "-f", "rawvideo", "-vcodec", "rawvideo",
            "-pix_fmt", "rgb24", "-s", "640x360", "-r", str(fps), "-i", "-",
            "-i", audio_path,
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "25",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart", output_path
        ]

        with open(stderr_path, "wb") as stderr_file:
            try:
                proc = subprocess.Popen(
                    command,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=stderr_file,
                    bufsize=0
                )
            except OSError as exc:
                raise RuntimeError(f"FFmpeg process start nahi hua: {exc}") from exc

            try:
                for frame_no in range(frame_count):
                    if proc.poll() is not None:
                        break

                    frame = Image.new("RGB", (640, 360))
                    from PIL import ImageDraw
                    draw = ImageDraw.Draw(frame)
                    _draw_cartoon_background(draw, frame_no)

                    cx = 320 + math.sin(frame_no * 0.035) * 28
                    # Procedural mouth movement; approximate, not phoneme sync.
                    speaking = (frame_no % 8) < 5
                    _draw_cartoon_character(
                        draw, cx, 286, frame_no, character, speaking
                    )
                    draw.rounded_rectangle(
                        (12, 12, 260, 42), radius=10, fill="#17324D"
                    )
                    draw.text(
                        (24, 20), "ZEE NOVA • HINDI CARTOON", fill="white"
                    )

                    try:
                        proc.stdin.write(frame.tobytes())
                    except (BrokenPipeError, OSError):
                        # FFmpeg has exited; collect its diagnostic below.
                        break

                if proc.stdin and not proc.stdin.closed:
                    try:
                        proc.stdin.close()
                    except (BrokenPipeError, OSError):
                        pass

                return_code = proc.wait(timeout=180)
            except Exception:
                if proc.poll() is None:
                    proc.kill()
                proc.wait()
                raise

        with open(stderr_path, "rb") as log_file:
            ffmpeg_error = log_file.read().decode("utf-8", "ignore").strip()

        if return_code != 0:
            details = ffmpeg_error[-1800:] or "FFmpeg exited without diagnostic output."
            raise RuntimeError(
                f"FFmpeg export failed (exit code {return_code}). Details: {details}"
            )

        if not os.path.isfile(output_path) or os.path.getsize(output_path) < 1024:
            details = ffmpeg_error[-1200:] or "Output MP4 was not created."
            raise RuntimeError(f"Video export failed. Details: {details}")

        with open(output_path, "rb") as video_file:
            video_bytes = video_file.read()

        if not video_bytes:
            raise RuntimeError("Video export empty aaya. Dobara try karo.")

        return video_bytes


# ============================================================
# 6. WEB SEARCH
# ============================================================


def render_puter_image_generator(prompt, aspect_ratio="1:1"):
    """Render Puter.js image generation in a browser iframe.

    Puter.js is browser-authenticated (user-pays); no Puter API key is stored
    in the Streamlit server or .env file. Generated images can be previewed
    and downloaded in this iframe. They are not transferred into Python's
    st.session_state.
    """
    safe_prompt = json.dumps(prompt)
    safe_ratio = json.dumps(aspect_ratio)

    component_html = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<script src="https://js.puter.com/v2/"></script>
<style>
*{box-sizing:border-box}body{margin:0;padding:14px;font-family:system-ui,-apple-system,Segoe UI,sans-serif;background:#0b1220;color:#e5e7eb}
.panel{border:1px solid #263449;border-radius:14px;padding:16px;background:#111c2e;margin-bottom:12px}
.row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}label{display:block;font-size:13px;color:#aebbd0;margin-bottom:6px}
textarea,select{width:100%;border:1px solid #35465f;border-radius:9px;background:#0b1424;color:#f8fafc;padding:10px;font:inherit}
textarea{min-height:90px;resize:vertical}.field{flex:1;min-width:220px}
button,.download{border:0;border-radius:9px;padding:10px 14px;background:#635bff;color:white;font-weight:650;cursor:pointer;text-decoration:none;display:inline-block}
button:disabled{opacity:.5;cursor:not-allowed}.secondary{background:#263449}.muted{color:#9aa9bf;font-size:12px}
#status{font-size:13px;color:#aebbd0;margin-top:10px;white-space:pre-wrap}.ok{color:#86efac!important}.bad{color:#fca5a5!important}
#preview{display:none;width:100%;max-height:650px;object-fit:contain;background:#080d16;border-radius:10px;margin-top:12px}
#download{display:none;margin-top:10px}.stats{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.stat{background:#0b1424;border-radius:9px;padding:9px;font-size:12px}.stat b{display:block;color:#fff;margin-top:4px;overflow-wrap:anywhere}
@media(max-width:600px){.stats{grid-template-columns:1fr 1fr}}
</style>
</head>
<body>
<div class="panel">
  <div class="row" style="justify-content:space-between">
    <strong>✦ Puter.js Image Studio</strong><span id="authState" class="muted">Checking sign-in…</span>
  </div>
  <div class="row" style="margin-top:12px">
    <button id="signOut" class="secondary" type="button" style="display:none">Disconnect Puter account</button>
  </div>
</div>
<div class="panel">
  <label for="prompt">Image prompt</label>
  <textarea id="prompt"></textarea>
  <div class="row" style="margin-top:12px">
    <div class="field">
      <label for="model">Image model</label>
      <select id="model">
        <option value="default">GPT Image 2 — Low quality</option>
        <option value="gemini-3.1-flash-image">Gemini 3.1 Flash Image</option>
        <option value="grok-imagine-image">Grok Imagine Image</option>
        <option value="@cf/black-forest-labs/flux-1-schnell">FLUX.1 Schnell (Cloudflare)</option>
      </select>
    </div>
    <div style="align-self:end"><button id="generate" type="button">Generate image</button></div>
  </div>
  <p class="muted">No Puter API key is required. On first use, Puter.js may ask the visitor to authorize their own account. Later use normally reuses that browser session. Model availability, allowance and charges are controlled by Puter.</p>
  <div id="status" role="status">Ready.</div>
</div>
<div class="panel">
  <div class="row" style="justify-content:space-between"><strong>Generated image</strong><a id="download" class="download" download="zi_nova_puter_image.png">Download PNG</a></div>
  <img id="preview" alt="Generated image preview">
</div>
<div class="panel">
  <strong>Account usage verification</strong>
  <div class="stats" style="margin-top:10px">
    <div class="stat">Monthly allowance<b id="allowance">—</b></div>
    <div class="stat">Remaining<b id="remaining">—</b></div>
    <div class="stat">Last image cost<b id="cost">—</b></div>
  </div>
  <p class="muted">A displayed $0.0000 per image is not proof of unlimited free use. Check the allowance and account usage regularly.</p>
  <button id="refresh" class="secondary" type="button">Refresh usage</button>
</div>
<script>
const INITIAL_PROMPT = __PROMPT__;
const RATIO = __RATIO__;
const el = id => document.getElementById(id);
const fmt = value => '$' + Number(value || 0).toFixed(4);
let beforeUsage = null;
function setStatus(message, cls=''){el('status').textContent=message;el('status').className=cls;}
async function signedInUser(){
  try { if (!puter.auth.isSignedIn()) return null; return await puter.auth.getUser(); }
  catch(e){ return null; }
}
async function readUsage(){
  try{
    if(!puter.auth.isSignedIn()) return null;
    const usage=await puter.auth.getMonthlyUsage();
    return usage && usage.allowanceInfo ? usage.allowanceInfo : null;
  }catch(e){return null;}
}
async function refreshAuth(){
  const user=await signedInUser();
  el('authState').textContent=user ? ('Connected: '+user.username) : 'Connects automatically on first use';
  el('signOut').style.display=user?'inline-block':'none';
  el('generate').disabled=false;
  await refreshUsage();
}
async function refreshUsage(){
  const info=await readUsage();
  if(!info){el('allowance').textContent='Unavailable';el('remaining').textContent='Unavailable';return;}
  el('allowance').textContent=fmt(info.monthUsageAllowance);
  el('remaining').textContent=fmt(info.remaining);
}
el('signOut').addEventListener('click',async()=>{try{await puter.auth.signOut();await refreshAuth();}catch(e){setStatus('Disconnect failed: '+e.message,'bad');}});
el('refresh').addEventListener('click',refreshUsage);
el('prompt').value=INITIAL_PROMPT;
el('generate').addEventListener('click',async()=>{
  const prompt=el('prompt').value.trim();
  if(!prompt){setStatus('Enter an image prompt.','bad');return;}
  // Puter.js automatically starts its own authorization flow on the first
  // cloud/AI request. Because this runs inside a click handler, popup auth
  // is allowed by the browser. Existing sessions are reused automatically.
  const model=el('model').value;
  const options=model==='default'?{quality:'low'}:{model:model};
  if(model==='gemini-3.1-flash-image') options.quality='512';
  // Ratio is added to the natural-language prompt because txt2img options
  // in the supplied working test project do not expose a ratio parameter.
  const finalPrompt=prompt+' Compose the image in a '+RATIO+' aspect ratio.';
  const button=el('generate');button.disabled=true;
  el('preview').style.display='none';el('download').style.display='none';
  el('cost').textContent='Checking…';
  beforeUsage=await readUsage();
  const started=performance.now();setStatus('Generating with '+(model==='default'?'GPT Image 2 (low)':model)+'…');
  try{
    const image=await puter.ai.txt2img(finalPrompt,{...options,test_mode:false});
    if(!image) throw new Error('Puter returned no image.');

    // Puter may return an image element backed by a temporary blob URL.
    // Convert it to a self-contained data URL before preview/download so the
    // image does not depend on a short-lived iframe-local object URL.
    async function imageToDataUrl(result){
      let source = typeof result === 'string' ? result : (result.src || result.url || '');
      if (result instanceof HTMLImageElement && result.complete && result.naturalWidth > 0) {
        try {
          const canvas = document.createElement('canvas');
          canvas.width = result.naturalWidth;
          canvas.height = result.naturalHeight;
          canvas.getContext('2d').drawImage(result, 0, 0);
          return canvas.toDataURL('image/png');
        } catch (canvasError) {
          // Cross-origin images may block canvas export; try fetching the source below.
        }
      }
      if (!source) throw new Error('Puter returned an image without a usable source.');
      if (source.startsWith('data:image/')) return source;

      const response = await fetch(source);
      if (!response.ok) throw new Error('Could not retrieve the generated image (HTTP '+response.status+').');
      const blob = await response.blob();
      if (!blob.type.startsWith('image/')) throw new Error('Puter returned a non-image file.');
      return await new Promise((resolve,reject)=>{
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = () => reject(new Error('Could not decode the generated image.'));
        reader.readAsDataURL(blob);
      });
    }

    await refreshAuth();
    const dataUrl = await imageToDataUrl(image);
    const preview=el('preview');
    await new Promise((resolve,reject)=>{
      preview.onload=resolve;
      preview.onerror=()=>reject(new Error('Image data was returned but the browser could not render the preview.'));
      preview.src=dataUrl;
    });
    preview.style.display='block';
    el('download').href=dataUrl;
    el('download').style.display='inline-block';
    const after=await readUsage();
    if(beforeUsage&&after){const spent=Number(beforeUsage.remaining||0)-Number(after.remaining||0);el('cost').textContent=spent>0?fmt(spent):'< display precision';}
    else el('cost').textContent='Unavailable';
    setStatus('Image generated successfully in '+((performance.now()-started)/1000).toFixed(1)+' seconds. Dimensions: '+preview.naturalWidth+' × '+preview.naturalHeight+'.','ok');
    await refreshUsage();
  }catch(e){setStatus('Generation failed: '+(e.message||String(e)),'bad');el('cost').textContent='Not available';await refreshUsage();}
  finally{button.disabled=false;}
});
if(typeof window.puter==='undefined'){
  setStatus('Puter.js did not load. Check internet access or browser blocking.','bad');
  el('generate').disabled=true;
}else{refreshAuth();}
</script>
</body>
</html>"""
    component_html = component_html.replace("__PROMPT__", safe_prompt).replace("__RATIO__", safe_ratio)
    components.html(component_html, height=900, scrolling=True)


def search_web(query):
    try:
        from ddgs import DDGS

        results = DDGS().text(query, max_results=5)
        sources = []

        for result in results:
            url = result.get("href", "")
            if url:
                sources.append({
                    "title": result.get("title", url),
                    "url": url,
                    "snippet": result.get("body", "")
                })

        return sources

    except Exception:
        return []


def render_sources(sources):
    if not sources:
        return

    st.markdown("### Research Sources")

    for i, source in enumerate(sources, start=1):
        st.markdown(
            f"{i}. [{source['title']}]({source['url']})"
        )
        if source.get("snippet"):
            st.caption(source["snippet"])


# ============================================================
# 7. TEXT AI
# ============================================================

def generate_text(prompt, history=None):
    client = get_groq_client(GROQ_API_KEY)

    messages = [{
        "role": "system",
        "content": (
            "You are Zi, the intelligent assistant inside Zi Nova AI. "
            "Answer accurately, clearly and directly. "
            "Do not invent facts, sources or actions. "
            "If uncertain, say so. "
            "When the user requests a website or runnable frontend, provide "
            "complete runnable HTML in a fenced ```html code block; put "
            "additional styles in a fenced ```css block and browser JavaScript "
            "in a fenced ```javascript block. Keep explanations outside code blocks."
        )
    }]

    if history:
        for message in history[-12:]:
            messages.append({
                "role": message["role"],
                "content": message["content"]
            })

    messages.append({
        "role": "user",
        "content": prompt
    })

    response = client.chat.completions.create(
        model=TEXT_MODEL,
        messages=messages,
        temperature=0.5,
        max_completion_tokens=1800
    )

    return response.choices[0].message.content or "No response generated."


# ============================================================
# 8. VISION AI
# ============================================================

def generate_vision_response(image_url, prompt):
    client = get_groq_client(GROQ_API_KEY)

    response = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": image_url}
                }
            ]
        }],
        temperature=0.3,
        max_completion_tokens=1500
    )

    return response.choices[0].message.content or "Image analysis failed."


# ============================================================
# 9. VOICE FUNCTIONS
# ============================================================

def transcribe_audio(uploaded_audio):
    client = get_groq_client(GROQ_API_KEY)
    audio_bytes = uploaded_audio.getvalue()

    if not audio_bytes:
        raise ValueError("Audio file is empty.")

    if len(audio_bytes) > MAX_AUDIO_MB * 1024 * 1024:
        raise ValueError(f"Audio must be smaller than {MAX_AUDIO_MB} MB.")

    extension = Path(
        getattr(uploaded_audio, "name", "recording.wav")
    ).suffix.lower()

    mime_types = {
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".m4a": "audio/mp4",
        ".mp4": "audio/mp4",
        ".ogg": "audio/ogg",
        ".webm": "audio/webm",
        ".flac": "audio/flac"
    }

    mime = mime_types.get(extension, "audio/wav")
    filename = "recording" + (extension or ".wav")

    result = client.audio.transcriptions.create(
        file=(filename, audio_bytes, mime),
        model="whisper-large-v3-turbo",
        response_format="text"
    )

    if isinstance(result, str):
        return result.strip()

    return getattr(result, "text", str(result)).strip()


def generate_speech(text, language="English"):
    language_codes = {
        "English": "en",
        "Hindi": "hi",
        "Arabic": "ar",
        "French": "fr",
        "Spanish": "es"
    }

    buffer = io.BytesIO()

    tts = gTTS(
        text=text,
        lang=language_codes.get(language, "en"),
        slow=False
    )

    tts.write_to_fp(buffer)
    buffer.seek(0)

    return buffer.getvalue()


# ============================================================
# 10. CAPTION ENGINE
# ============================================================

def generate_smart_captions(
    uploaded_file,
    style,
    platform,
    extra_context,
    use_search
):
    image_url = image_to_data_url(uploaded_file)

    analysis = generate_vision_response(
        image_url,
        (
            "Analyze this image. Describe only visible objects, "
            "actions, colours, composition, setting and mood. "
            "Do not identify people or guess private information."
        )
    )

    sources = search_web(analysis[:250]) if use_search else []

    research = "\n\n".join(
        f"{s['title']}\n{s['url']}\n{s['snippet']}"
        for s in sources
    )

    prompt = f"""
You are Zi Nova AI's professional caption generator.

IMAGE ANALYSIS:
{analysis}

OPTIONAL RESEARCH:
{research or "No external research available."}

USER PREFERENCES:
Style: {style}
Platform: {platform}
Additional context: {extra_context or "None"}

Generate five different captions:
1. Professional caption
2. Creative caption
3. Short caption
4. SEO-friendly caption
5. Marketing/social media caption

Rules:
- Use visible image evidence.
- Do not invent brands, locations or events.
- Do not identify people.
- Avoid irrelevant hashtags.
- Make captions natural and publication-ready.
- Do not guarantee engagement.
"""

    captions = generate_text(prompt)
    return analysis, captions, sources


# ============================================================
# 11. CHAT ASSISTANT HELPERS
# ============================================================

_CODE_FENCE_RE = re.compile(
    r"```(?P<lang>[\w+#.-]*)[ \t]*\n(?P<code>.*?)```",
    re.DOTALL
)


def _build_live_preview_document(html_code, css_code="", js_code=""):
    """Build a self-contained HTML document for the isolated preview iframe."""
    document = (html_code or "").strip()

    if not document:
        document = "<!doctype html><html><head><meta charset='utf-8'></head><body></body></html>"

    if not re.search(r"<\s*html[\s>]|<!doctype\s+html", document, re.I):
        document = (
            "<!doctype html><html><head><meta charset='utf-8'></head>"
            "<body>" + document + "</body></html>"
        )

    if css_code.strip():
        style_tag = "<style>\n" + css_code + "\n</style>"
        if re.search(r"</head\s*>", document, re.I):
            document = re.sub(
                r"</head\s*>",
                lambda match: style_tag + match.group(0),
                document,
                count=1,
                flags=re.I
            )
        else:
            document = style_tag + document

    if js_code.strip():
        script_tag = "<script>\n" + js_code + "\n</script>"
        if re.search(r"</body\s*>", document, re.I):
            document = re.sub(
                r"</body\s*>",
                lambda match: script_tag + match.group(0),
                document,
                count=1,
                flags=re.I
            )
        else:
            document += script_tag

    return document


def render_assistant_message(content, message_index):
    """Render normal Markdown and add Preview/Code tabs for HTML responses."""
    content = str(content or "")
    blocks = list(_CODE_FENCE_RE.finditer(content))

    html_blocks = []
    css_blocks = []
    js_blocks = []
    for match in blocks:
        language = (match.group("lang") or "").lower()
        code = match.group("code").strip("\n")
        if language in {"html", "htm", "xhtml"} or (
            not language and re.search(r"<!doctype\s+html|<\s*html[\s>]|<\s*body[\s>]|<\s*div[\s>]", code, re.I)
        ):
            html_blocks.append(code)
        elif language == "css":
            css_blocks.append(code)
        elif language in {"js", "javascript"}:
            js_blocks.append(code)

    if not html_blocks:
        st.markdown(content, unsafe_allow_html=False)
        return

    # Render prose before/between/after code fences, excluding code blocks handled below.
    cursor = 0
    for match in blocks:
        preceding = content[cursor:match.start()].strip()
        if preceding:
            st.markdown(preceding, unsafe_allow_html=False)

        language = (match.group("lang") or "").lower()
        code = match.group("code").strip("\n")
        if language not in {"html", "htm", "xhtml", "css", "js", "javascript"}:
            st.code(code, language=language or None)

        cursor = match.end()
    trailing = content[cursor:].strip()
    if trailing:
        st.markdown(trailing, unsafe_allow_html=False)

    full_source = "\n\n".join(html_blocks)
    if css_blocks:
        full_source += "\n\n/* Additional CSS */\n" + "\n\n".join(css_blocks)
    if js_blocks:
        full_source += "\n\n// Additional JavaScript\n" + "\n\n".join(js_blocks)

    preview_document = _build_live_preview_document(
        "\n\n".join(html_blocks),
        "\n\n".join(css_blocks),
        "\n\n".join(js_blocks)
    )

    preview_tab, code_tab = st.tabs(["◉ Preview", "</> Code"])
    with preview_tab:
        st.caption("Live preview runs in an isolated browser frame. External services and server-side code are not executed.")
        components.html(
            preview_document,
            height=620,
            scrolling=True
        )
    with code_tab:
        st.code(full_source, language="html")



def start_new_chat():
    st.session_state.messages = []
    st.session_state.last_sources = []
    st.session_state.chat_image = None
    st.session_state.chat_input_counter += 1


def run_chat_prompt(prompt, image_file=None):
    if not prompt.strip() and image_file is None:
        return

    if image_file is not None:
        try:
            image_url = image_to_data_url(image_file)

            image_prompt = prompt.strip() or (
                "Describe and analyze this image in detail."
            )

            answer = generate_vision_response(
                image_url,
                image_prompt
            )

            user_content = image_prompt + "\n[Image attached]"

            st.session_state.messages.append({
                "role": "user",
                "content": user_content
            })

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer
            })

            st.session_state.last_sources = []

        except Exception as error:
            st.error(f"Image analysis failed: {error}")

        return

    sources = []
    final_prompt = prompt

    if st.session_state.web_on:
        sources = search_web(prompt)

        if sources:
            research = "\n\n".join(
                f"Title: {item['title']}\n"
                f"URL: {item['url']}\n"
                f"Summary: {item['snippet']}"
                for item in sources
            )

            final_prompt = (
                prompt
                + "\n\nUse the following web research when relevant. "
                "Distinguish sourced facts from uncertainty:\n"
                + research
            )

    history = st.session_state.messages[-12:]

    answer = generate_text(
        final_prompt,
        history
    )

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })

    st.session_state.last_sources = sources


# ============================================================
# 12. SIDEBAR
# ============================================================

with st.sidebar:

    logo_html = get_logo_html()

    if logo_html:
        render_html(logo_html)
    else:
        render_html(
            '<div class="brand">Zi <span>Nova AI</span></div>'
        )

    st.divider()
    st.markdown("### WORKSPACE")

    navigation_items = [
        ("⌂  Home", "Home"),
        ("✦  Caption Studio", "Caption Studio"),
        ("◈  Zi AI Assistant", "Zi AI Assistant"),
        ("▧  AI Image Size Reducer", "AI Image Size Reducer"),
        ("⚡  Zi Activator Pro", "Zi Activator Pro"),
        ("ⓘ  About Project", "About Project")
    ]

    for button_label, page_name in navigation_items:
        if st.button(
            button_label,
            key=f"sidebar_nav_{page_name.lower().replace(' ', '_')}",
            use_container_width=True
        ):
            if st.session_state.page != page_name:
                st.session_state.page = page_name
                st.rerun()

    st.divider()
    st.markdown("### PREFERENCES")

    selected_theme = st.selectbox(
        "Website theme",
        list(THEMES.keys()),
        index=list(THEMES.keys()).index(st.session_state.theme)
    )

    if selected_theme != st.session_state.theme:
        st.session_state.theme = selected_theme
        st.rerun()

    st.divider()

    st.caption("Zi Nova AI · An Intelligence Platform")


# ============================================================
# 13. HOME PAGE
# ============================================================

if st.session_state.page == "Home":

    render_html("""
    <div class="hero">
        <div class="eyebrow">
            INTRODUCING THE NEXT GENERATION OF AI
        </div>
        <h1>
            One Platform.<br>
            <span>Infinite Intelligence.</span>
        </h1>
        <p>
            Meet Zi Nova AI — an intelligence platform
            designed to bring creative tools, AI assistance
            and smart workflows together in one workspace.
        </p>
    </div>
    """)

    render_html(
        '<div class="section-heading">Your AI Workspaces</div>'
    )

    col1, col2 = st.columns(2, gap="large")

    with col1:
        render_html("""
        <div class="feature-card">
            <div class="feature-icon">✦</div>
            <h3>Smart Caption Studio</h3>
            <p>Analyze images and create polished social media captions.</p>
        </div>
        """)

        if st.button("Open Caption Studio", use_container_width=True):
            go_to_page("Caption Studio")
            st.rerun()

        render_html("""
        <div class="feature-card">
            <div class="feature-icon">🎙️</div>
            <h3>AI Voice Assistant</h3>
            <p>Use voice recordings to ask Zi questions and hear responses.</p>
        </div>
        """)

        if st.button("Open Voice Assistant", use_container_width=True):
            go_to_page("Zi AI Assistant")
            st.session_state.assistant_tab = "AI Voice Assistant"
            st.rerun()

    with col2:
        render_html("""
        <div class="feature-card">
            <div class="feature-icon">◈</div>
            <h3>Chat Assistant</h3>
            <p>Ask questions, research topics and analyze images.</p>
        </div>
        """)

        if st.button("Open Chat Assistant", use_container_width=True):
            go_to_page("Zi AI Assistant")
            st.session_state.assistant_tab = "Chat Assistant"
            st.rerun()

        render_html("""
        <div class="feature-card">
            <div class="feature-icon">▧</div>
            <h3>AI Image Size Reducer</h3>
            <p>Resize and compress images with configurable quality.</p>
        </div>
        """)

        if st.button("Open Image Reducer", use_container_width=True):
            go_to_page("AI Image Size Reducer")
            st.rerun()

    render_html(
        '<div class="section-heading">Platform Capabilities</div>'
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        render_html("""
        <div class="feature-card">
            <div class="feature-icon">🖼️</div>
            <h3>Visual AI</h3>
            <p>Image understanding with your configured vision model.</p>
        </div>
        """)

    with c2:
        render_html("""
        <div class="feature-card">
            <div class="feature-icon">⌁</div>
            <h3>Smart Conversations</h3>
            <p>Text-based conversations with session chat history.</p>
        </div>
        """)

    with c3:
        render_html("""
        <div class="feature-card">
            <div class="feature-icon">🔊</div>
            <h3>Voice Tools</h3>
            <p>Audio transcription and generated spoken responses.</p>
        </div>
        """)


# ============================================================
# 14. CAPTION STUDIO
# ============================================================

elif st.session_state.page == "Caption Studio":

    st.title("✦ Smart Caption Studio")
    st.caption("Visual AI + Deep Search + Intelligent Caption Generation")

    if not require_api_key():
        st.stop()

    uploaded_image = st.file_uploader(
        "Upload an image",
        type=["jpg", "jpeg", "png", "webp"],
        key="caption_image"
    )

    col1, col2 = st.columns(2)

    with col1:
        style = st.selectbox(
            "Caption style",
            [
                "Professional", "Creative", "Minimal",
                "Luxury", "Funny", "Inspirational", "Marketing"
            ]
        )

    with col2:
        platform = st.selectbox(
            "Target platform",
            ["Instagram", "Facebook", "LinkedIn", "YouTube", "X", "General"]
        )

    extra_context = st.text_area(
        "Additional context (optional)",
        placeholder="Describe your product, audience or campaign..."
    )

    use_search = st.checkbox(
        "Use optional web search",
        value=False
    )

    if uploaded_image:
        st.image(
            uploaded_image,
            caption="Uploaded image",
            use_container_width=True
        )

    if st.button(
        "✦ Generate Captions",
        type="primary",
        use_container_width=True
    ):

        if uploaded_image is None:
            st.warning("Upload an image first.")
        else:
            try:
                with st.spinner("Zi is analyzing your image..."):
                    analysis, captions, sources = generate_smart_captions(
                        uploaded_image,
                        style,
                        platform,
                        extra_context,
                        use_search
                    )

                st.session_state.caption_result = {
                    "analysis": analysis,
                    "captions": captions
                }
                st.session_state.caption_sources = sources

            except Exception as error:
                st.error(f"Caption generation failed: {error}")

    if st.session_state.caption_result:
        result = st.session_state.caption_result

        st.divider()
        st.subheader("Image Analysis")
        st.write(result["analysis"])

        st.subheader("Generated Captions")
        st.markdown(result["captions"])

        st.download_button(
            "Download Captions",
            data=result["captions"],
            file_name="zi_nova_ai_captions.txt",
            mime="text/plain",
            use_container_width=True
        )

        render_sources(st.session_state.caption_sources)


# ============================================================
# 15. ZI AI ASSISTANT
# ============================================================

elif st.session_state.page == "Zi AI Assistant":

    if not require_api_key():
        st.warning("Groq API key ke bina Chat, Voice aur AI Image features unavailable rahenge.")

    chat_tab, voice_tab, image_tab = st.tabs([
        "◈ Chat Assistant",
        "🎙️ AI Voice Assistant",
        "🎨 AI Image Generation"
    ])

    # --------------------------------------------------------
    # 16A. CHAT ASSISTANT — CHATGPT STYLE
    # --------------------------------------------------------

    with chat_tab:

        # HEADER

        render_html("""
        <div class="zi-chat-header">
            <div class="zi-chat-brand">
                <div class="zi-chat-logo">✦</div>
                <div>
                    <div class="zi-chat-title">Zi AI</div>
                    <div class="zi-chat-subtitle">Intelligent Assistant</div>
                </div>
            </div>
            <div class="zi-online">Online</div>
        </div>
        """)

        # NEW CHAT CONTROL

        action_col1, action_col2 = st.columns([5, 1])

        with action_col2:
            if st.button(
                "＋ New Chat",
                key="zi_new_chat",
                use_container_width=True
            ):
                start_new_chat()
                st.rerun()

        # WELCOME SCREEN

        if not st.session_state.messages:

            render_html("""
            <div class="zi-welcome">
                <h2>How can I help you today?</h2>
                <p>
                    Ask anything. Research, create, analyze and solve problems with Zi.
                </p>
            </div>
            """)

            # SUGGESTION CARDS

            card1, card2 = st.columns(2, gap="small")

            with card1:

                render_html("""
                <div class="zi-suggestion">
                    <div class="zi-suggestion-icon">♧</div>
                    <div class="zi-suggestion-title">Explain something</div>
                    <div class="zi-suggestion-desc">
                        Understand complex topics simply.
                    </div>
                </div>
                """)

                if st.button(
                    "Explain something",
                    key="zi_suggest_explain",
                    use_container_width=True
                ):
                    st.session_state.zi_pending_prompt = (
                        "Explain a complex topic to me in simple language."
                    )
                    st.rerun()

            with card2:

                render_html("""
                <div class="zi-suggestion">
                    <div class="zi-suggestion-icon">&lt;/&gt;</div>
                    <div class="zi-suggestion-title">Write code</div>
                    <div class="zi-suggestion-desc">
                        Build and debug applications.
                    </div>
                </div>
                """)

                if st.button(
                    "Write code",
                    key="zi_suggest_code",
                    use_container_width=True
                ):
                    st.session_state.zi_pending_prompt = (
                        "Help me write and explain code."
                    )
                    st.rerun()

            card3, card4 = st.columns(2, gap="small")

            with card3:

                render_html("""
                <div class="zi-suggestion">
                    <div class="zi-suggestion-icon">⌕</div>
                    <div class="zi-suggestion-title">Research</div>
                    <div class="zi-suggestion-desc">
                        Explore topics with web search.
                    </div>
                </div>
                """)

                if st.button(
                    "Research",
                    key="zi_suggest_research",
                    use_container_width=True
                ):
                    st.session_state.zi_pending_prompt = (
                        "Research an interesting topic and explain the findings."
                    )
                    st.rerun()

            with card4:

                render_html("""
                <div class="zi-suggestion">
                    <div class="zi-suggestion-icon">▧</div>
                    <div class="zi-suggestion-title">Analyze images</div>
                    <div class="zi-suggestion-desc">
                        Upload images for AI analysis.
                    </div>
                </div>
                """)

                if st.button(
                    "Analyze images",
                    key="zi_suggest_images",
                    use_container_width=True
                ):
                    st.session_state.zi_pending_prompt = (
                        "I want to upload an image for analysis."
                    )
                    st.rerun()

        # CONVERSATION HISTORY

        else:

            for message_index, message in enumerate(st.session_state.messages):

                if message["role"] == "user":

                    with st.chat_message("user"):
                        st.markdown(message["content"])

                else:

                    with st.chat_message("assistant"):
                        render_assistant_message(
                            message["content"],
                            message_index
                        )

            if st.session_state.last_sources:
                render_sources(st.session_state.last_sources)

        # WEB SEARCH CONTROL

        web_col1, web_col2 = st.columns([4, 1])

        with web_col1:
            st.toggle(
                "Web search",
                key="web_on",
                help="Search the web for relevant information."
            )

        with web_col2:

            if st.button(
                "Clear chat",
                key="zi_clear_chat",
                use_container_width=True
            ):
                start_new_chat()
                st.rerun()

        # IMAGE ATTACHMENT

        with st.expander(
            "📎 Attach image",
            expanded=bool(st.session_state.chat_image)
        ):

            uploaded_chat_image = st.file_uploader(
                "Upload an image for analysis",
                type=["jpg", "jpeg", "png", "webp"],
                key="zi_chat_image_upload"
            )

            if uploaded_chat_image:
                st.session_state.chat_image = uploaded_chat_image

                st.image(
                    uploaded_chat_image,
                    caption="Attached image",
                    width=240
                )

                if st.button(
                    "Remove image",
                    key="zi_remove_chat_image"
                ):
                    st.session_state.chat_image = None
                    st.rerun()

        # CHAT INPUT

        pending_prompt = st.session_state.pop(
            "zi_pending_prompt",
            None
        )

        prompt = st.chat_input(
            "Message Zi...",
            key=f"zi_chat_input_{st.session_state.chat_input_counter}"
        )

        if pending_prompt:
            prompt = pending_prompt

        if prompt:

            if not require_api_key():
                st.stop()

            try:

                with st.spinner("Zi is thinking..."):

                    image_to_analyze = st.session_state.chat_image

                    run_chat_prompt(
                        prompt,
                        image_to_analyze
                    )

                    st.session_state.chat_image = None

                st.rerun()

            except Exception as error:
                st.error(f"Zi AI error: {error}")

        render_html("""
        <div class="zi-chat-note">
            Zi can make mistakes. Verify important information.
        </div>
        """)

        st.markdown(
            " ",
            unsafe_allow_html=False
        )

    # --------------------------------------------------------
    # 16B. AI VOICE ASSISTANT
    # --------------------------------------------------------

    with voice_tab:

        st.subheader("AI Voice Assistant")

        st.caption(
            "Upload your voice recording. Zi will transcribe, "
            "understand and respond to your request."
        )

        render_html("""
        <div class="mode-card">
            <div class="feature-icon">🎙️</div>
            <h3>Talk to Zi</h3>
            <p>
                Convert your spoken request into text,
                generate an AI answer and listen to Zi's response.
            </p>
        </div>
        """)

        voice_language = st.selectbox(
            "Voice response language",
            ["English", "Hindi", "Arabic", "French", "Spanish"],
            key="voice_language"
        )

        audio_input = st.file_uploader(
            "Upload your voice recording",
            type=[
                "wav", "mp3", "m4a", "mp4",
                "ogg", "webm", "flac"
            ],
            key="voice_audio_upload"
        )

        if audio_input:
            st.audio(audio_input)

        if st.button(
            "🎙️ Process Voice Command",
            key="process_voice_command",
            type="primary",
            use_container_width=True,
            disabled=audio_input is None
        ):

            try:
                with st.spinner("Step 1/3: Understanding your voice..."):
                    spoken_question = transcribe_audio(audio_input)

                if not spoken_question:
                    st.warning("No speech detected. Please try again.")

                else:
                    st.markdown("### Your Spoken Command")
                    st.info(spoken_question)

                    with st.spinner("Step 2/3: Zi is thinking..."):
                        voice_answer = generate_text(
                            spoken_question,
                            st.session_state.messages
                        )

                    st.markdown("### Zi's Response")
                    st.write(voice_answer)

                    st.session_state.messages.extend([
                        {
                            "role": "user",
                            "content": spoken_question
                        },
                        {
                            "role": "assistant",
                            "content": voice_answer
                        }
                    ])

                    with st.spinner("Step 3/3: Generating voice..."):
                        audio_bytes = generate_speech(
                            voice_answer,
                            voice_language
                        )

                    st.success("Zi's voice response is ready.")

                    st.markdown("### Listen to Zi")

                    st.audio(
                        audio_bytes,
                        format="audio/mp3"
                    )

                    st.download_button(
                        "Download Voice Response",
                        data=audio_bytes,
                        file_name="zi_voice_response.mp3",
                        mime="audio/mpeg",
                        use_container_width=True
                    )

                    st.session_state.voice_result = {
                        "question": spoken_question,
                        "answer": voice_answer
                    }

            except Exception as error:
                st.error(f"Voice Assistant error: {error}")

        st.divider()

        st.markdown("### Voice Assistant Capabilities")

        v1, v2 = st.columns(2)

        with v1:
            render_html("""
            <div class="feature-card">
                <div class="feature-icon">🎧</div>
                <h3>Speech Recognition</h3>
                <p>Audio transcription using Groq Whisper.</p>
            </div>
            """)

        with v2:
            render_html("""
            <div class="feature-card">
                <div class="feature-icon">🔊</div>
                <h3>AI Voice Response</h3>
                <p>Spoken responses using Google Text-to-Speech.</p>
            </div>
            """)


    # --------------------------------------------------------
    # 15C. AI IMAGE GENERATION
    # --------------------------------------------------------

    with image_tab:

        st.title("🎨 AI Image Generator")
        st.caption(
            "Free-first setup: Cloudflare Workers AI is selected by default when configured. "
            "Puter.js is an optional user-account route; Pollinations and Gemini remain available "
            "only when configured and may consume account credits or incur charges."
        )

        available_providers = []
        if CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN:
            available_providers.append("Free — Cloudflare FLUX.1 Schnell")
        available_providers.append("Puter.js — Multi-model")
        if POLLINATIONS_API_KEY:
            available_providers.append("Pollinations — FLUX")
        if GEMINI_API_KEY:
            available_providers.append("Premium — Google Gemini")

        st.warning(
            "Public free access is not unlimited: Cloudflare Workers AI currently has a shared "
            "10,000-Neuron daily free allocation per Cloudflare account. All visitors to this "
            "deployment consume that same pool. When it is exhausted, generation stops until reset."
        )

        st.markdown("### Choose generation provider")
        selected_provider = st.selectbox(
            "Image generation mode",
            available_providers,
            key="zi_image_provider_free_first"
        )

        st.markdown("### Describe the image you want")
        image_prompt = st.text_area(
            "Image prompt",
            placeholder=(
                "Example: A cinematic photorealistic futuristic Mumbai skyline at sunset, "
                "dramatic golden light, detailed architecture, premium editorial photography."
            ),
            height=130,
            key="zi_image_prompt"
        )

        gen_col1, gen_col2, gen_col3 = st.columns(3)

        with gen_col1:
            image_style = st.selectbox(
                "Style",
                [
                    "Photorealistic", "Cinematic", "Editorial photography",
                    "Fashion photography", "Product photography",
                    "Architecture / interior design", "Digital art",
                    "Fantasy concept art", "Anime / manga", "3D render",
                    "Illustration", "Watercolor / painting", "Minimalist",
                    "Vector / flat design", "Logo / brand identity",
                    "Poster / advertisement", "Game asset / character design",
                    "Infographic / diagram", "Custom"
                ],
                key="zi_image_style"
            )

        with gen_col2:
            aspect_ratio = st.selectbox(
                "Aspect ratio",
                ["1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3", "5:4", "4:5", "21:9"],
                key="zi_image_ratio"
            )

        with gen_col3:
            if selected_provider == "Premium — Google Gemini":
                image_size = st.selectbox(
                    "Image resolution", ["1K", "2K", "4K"], index=0,
                    key="zi_image_size"
                )
            else:
                image_size = "1K"
                st.selectbox(
                    "Image resolution", ["1K / provider default"],
                    key="zi_image_size_cloudflare"
                )

        reference_image = st.file_uploader(
            "Optional: upload a reference image to edit (Gemini Premium only)",
            type=["jpg", "jpeg", "png", "webp"],
            key="zi_image_reference",
            help="Reference-image editing is available only with the configured Gemini provider."
        )

        if reference_image:
            st.image(reference_image, caption="Reference image", width=260)
            if selected_provider != "Premium — Google Gemini":
                st.info(
                    "Reference-image editing is supported only by the configured Gemini provider. "
                    "The reference image will not be sent to Puter, Cloudflare or Pollinations."
                )

        style_instruction = (
            "" if image_style == "Custom" else f" Visual style: {image_style}."
        )
        final_image_prompt = (
            image_prompt.strip()
            + style_instruction
            + f" Compose the image for an aspect ratio of {aspect_ratio}."
            + " Create a polished, professional, high-quality result with strong composition, "
              "coherent details, appropriate lighting and clean visual hierarchy. Follow "
              "the requested subject and use case closely. Avoid unwanted text, watermarks "
              "and logos unless the prompt explicitly requests them."
        )

        if selected_provider == "Puter.js — Multi-model":
            st.info(
                "Puter.js runs inside this panel. First-time visitors may be asked to authorize "
                "their own Puter account on the first generation; returning visitors normally "
                "reuse their browser session. No Puter API key is stored by Zi Nova AI. "
                "Images can be previewed and downloaded here, but are not copied into Streamlit's Python session."
            )
            if not image_prompt.strip():
                st.caption("Enter a prompt above, then generate from the Puter.js panel below.")
            render_puter_image_generator(final_image_prompt, aspect_ratio=aspect_ratio)

        else:
            can_generate = bool(image_prompt.strip())
            if st.button(
                "✨ Generate AI Image",
                type="primary",
                use_container_width=True,
                disabled=not can_generate
            ):
                try:
                    if selected_provider == "Free — Cloudflare FLUX.1 Schnell":
                        if reference_image is not None:
                            st.warning(
                                "Reference-image editing is not supported by Cloudflare FLUX. "
                                "The reference image was not sent."
                            )
                        with st.spinner("Cloudflare FLUX.1 Schnell is creating your image..."):
                            image_bytes = generate_cloudflare_image(
                                final_image_prompt, aspect_ratio=aspect_ratio
                            )
                        provider_label = "Cloudflare FLUX.1 Schnell"
                        resolution_label = "1K"

                    elif selected_provider == "Pollinations — FLUX":
                        if reference_image is not None:
                            st.warning(
                                "Reference-image editing is not supported by this Pollinations "
                                "integration. The reference image was not sent."
                            )
                        with st.spinner("Pollinations FLUX is creating your image..."):
                            image_bytes = generate_pollinations_image(
                                final_image_prompt, aspect_ratio=aspect_ratio
                            )
                        provider_label = f"Pollinations ({POLLINATIONS_IMAGE_MODEL})"
                        resolution_label = f"{image_size} · {aspect_ratio}"

                    else:
                        with st.spinner("Gemini is creating your image..."):
                            image_bytes = generate_ai_image(
                                final_image_prompt,
                                aspect_ratio=aspect_ratio,
                                image_size=image_size,
                                reference_image=reference_image
                            )
                        provider_label = IMAGE_MODEL
                        resolution_label = image_size

                    # Normalize provider output to PNG so Streamlit preview and
                    # the .png download always receive matching, valid image data.
                    image_bytes = normalize_image_to_png(image_bytes)

                    st.session_state.generated_image = {
                        "bytes": image_bytes,
                        "prompt": final_image_prompt,
                        "ratio": aspect_ratio,
                        "size": resolution_label,
                        "provider": provider_label
                    }
                    st.success("Image generated successfully.")

                except Exception as error:
                    st.error(f"Image generation failed: {error}")

            if st.session_state.generated_image:
                result = st.session_state.generated_image
                st.divider()
                st.subheader("Your generated image")
                st.image(result["bytes"], use_container_width=True)
                st.caption(
                    f"Provider: {result.get('provider', IMAGE_MODEL)} · "
                    f"Aspect ratio: {result['ratio']} · Resolution: {result['size']}"
                )
                st.download_button(
                    "⬇️ Download PNG",
                    data=result["bytes"],
                    file_name="zi_nova_ai_generated.png",
                    mime="image/png",
                    use_container_width=True
                )
                with st.expander("View generation prompt"):
                    st.write(result["prompt"])




# ============================================================
# 16. AI IMAGE SIZE REDUCER
# ============================================================

elif st.session_state.page == "AI Image Size Reducer":

    st.title("▧ AI Image Size Reducer")

    st.caption(
        "Resize and compress images with configurable quality."
    )

    uploaded_image = st.file_uploader(
        "Upload an image",
        type=["jpg", "jpeg", "png", "webp"],
        key="reducer_image"
    )

    if uploaded_image:

        try:
            original_image = ImageOps.exif_transpose(
                Image.open(uploaded_image)
            )

            st.image(
                original_image,
                caption="Original image",
                use_container_width=True
            )

            original_size = len(uploaded_image.getvalue())

            st.info(
                f"Original size: {original_size / 1024:.2f} KB"
            )

            col1, col2 = st.columns(2)

            with col1:
                width = st.number_input(
                    "Output width",
                    min_value=100,
                    max_value=8000,
                    value=min(original_image.width, 1920)
                )

            with col2:
                height = st.number_input(
                    "Output height",
                    min_value=100,
                    max_value=8000,
                    value=min(original_image.height, 1080)
                )

            keep_aspect = st.checkbox(
                "Maintain aspect ratio",
                value=True
            )

            quality = st.slider(
                "Compression quality",
                10,
                100,
                80
            )

            output_format = st.selectbox(
                "Output format",
                ["JPEG", "PNG", "WEBP"]
            )

            if st.button(
                "Compress Image",
                use_container_width=True
            ):

                image = original_image.copy()

                if keep_aspect:
                    image.thumbnail((int(width), int(height)))
                else:
                    image = image.resize(
                        (int(width), int(height)),
                        Image.Resampling.LANCZOS
                    )

                if output_format == "JPEG":
                    image = image.convert("RGB")
                    extension = "jpg"
                    mime = "image/jpeg"

                elif output_format == "WEBP":
                    image = image.convert("RGB")
                    extension = "webp"
                    mime = "image/webp"

                else:
                    extension = "png"
                    mime = "image/png"

                output = io.BytesIO()

                if output_format == "JPEG":
                    image.save(
                        output,
                        format="JPEG",
                        quality=quality,
                        optimize=True
                    )

                elif output_format == "WEBP":
                    image.save(
                        output,
                        format="WEBP",
                        quality=quality,
                        method=6
                    )

                else:
                    image.save(
                        output,
                        format="PNG",
                        optimize=True
                    )

                compressed_bytes = output.getvalue()
                compressed_size = len(compressed_bytes)

                reduction = (
                    (original_size - compressed_size)
                    / original_size * 100
                ) if original_size else 0

                st.session_state.reducer_result = {
                    "bytes": compressed_bytes,
                    "format": extension,
                    "mime": mime,
                    "size": compressed_size,
                    "reduction": reduction,
                    "image": image
                }

            if st.session_state.reducer_result:

                result = st.session_state.reducer_result

                st.divider()
                st.subheader("Compressed Image")

                st.image(
                    result["image"],
                    use_container_width=True
                )

                st.metric(
                    "Compressed size",
                    f"{result['size'] / 1024:.2f} KB"
                )

                st.metric(
                    "Size change",
                    f"{result['reduction']:.2f}%"
                )

                st.download_button(
                    "Download Compressed Image",
                    data=result["bytes"],
                    file_name=f"zi_nova_compressed.{result['format']}",
                    mime=result["mime"],
                    use_container_width=True
                )

        except Exception as error:
            st.error(f"Image processing failed: {error}")


# ============================================================
# 17. ZI ACTIVATOR PRO
# ============================================================

elif st.session_state.page == "Zi Activator Pro":

    st.title("⚡ Zi Activator Pro")
    st.caption("Genuine Windows and Microsoft Office license enquiries")

    render_html("""
    <div class="hero">
        <div class="eyebrow">ZI NOVA AI • SOFTWARE LICENSE SERVICES</div>
        <h1>ZI <span>ACTIVATOR PRO</span></h1>
        <p>
            Explore genuine Windows and Microsoft Office license options
            at competitive prices. Select a product category to enquire.
        </p>
    </div>
    """)

    windows_tab, office_tab = st.tabs([
        "🪟 Windows Activation",
        "▦ Microsoft Office Activation"
    ])

    with windows_tab:

        st.subheader("🪟 Windows Activation")

        st.write(
            "Choose a Windows edition. License type, device eligibility, "
            "price and availability must be confirmed before purchase."
        )

        windows_product = st.selectbox(
            "Select Windows product",
            [
                "Windows 11 Home",
                "Windows 11 Pro",
                "Windows 10 Home",
                "Windows 10 Pro"
            ],
            key="zi_activator_windows_product"
        )

        windows_license_type = st.selectbox(
            "Preferred license type",
            [
                "Not sure / Need guidance",
                "Retail",
                "OEM",
                "Other authorized license"
            ],
            key="zi_activator_windows_license"
        )

        with st.form("zi_activator_windows_enquiry"):

            st.markdown("#### Customer enquiry")

            windows_customer_name = st.text_input("Full name")
            windows_customer_email = st.text_input("Email address")

            windows_customer_note = st.text_area(
                "Additional requirements (optional)",
                placeholder="Example: New PC, existing Windows installation, number of devices..."
            )

            windows_submit = st.form_submit_button(
                "Submit Windows Enquiry",
                use_container_width=True
            )

        if windows_submit:

            if not windows_customer_name.strip():
                st.warning("Please enter your name.")

            elif (
                "@" not in windows_customer_email
                or "." not in windows_customer_email
            ):
                st.warning("Please enter a valid email address.")

            else:
                st.info(
                    "The enquiry form is validated, but delivery is not connected yet. "
                    "Connect an email, WhatsApp or database backend before accepting live orders."
                )

                st.write("**Selected product:**", windows_product)
                st.write("**License preference:**", windows_license_type)

    with office_tab:

        st.subheader("▦ Microsoft Office Activation")

        st.write(
            "Choose a Microsoft Office product or Microsoft 365 plan. "
            "The exact license terms and eligible devices must be verified."
        )

        office_product = st.selectbox(
            "Select Microsoft product",
            [
                "Office Home",
                "Office Home & Business",
                "Office Professional",
                "Microsoft 365 Personal",
                "Microsoft 365 Family",
                "Microsoft 365 Business"
            ],
            key="zi_activator_office_product"
        )

        office_usage = st.selectbox(
            "Intended use",
            [
                "Personal",
                "Student",
                "Professional",
                "Business"
            ],
            key="zi_activator_office_usage"
        )

        with st.form("zi_activator_office_enquiry"):

            st.markdown("#### Customer enquiry")

            office_customer_name = st.text_input("Full name")
            office_customer_email = st.text_input("Email address")

            office_customer_note = st.text_area(
                "Additional requirements (optional)",
                placeholder="Example: Number of users or devices, preferred plan..."
            )

            office_submit = st.form_submit_button(
                "Submit Office Enquiry",
                use_container_width=True
            )

        if office_submit:

            if not office_customer_name.strip():
                st.warning("Please enter your name.")

            elif (
                "@" not in office_customer_email
                or "." not in office_customer_email
            ):
                st.warning("Please enter a valid email address.")

            else:
                st.info(
                    "The enquiry form is validated, but delivery is not connected yet. "
                    "Connect an email, WhatsApp or database backend before accepting live orders."
                )

                st.write("**Selected product:**", office_product)
                st.write("**Intended use:**", office_usage)

    st.divider()

    st.subheader("Zi Activator Pro — Service Standards")

    activator_col1, activator_col2, activator_col3 = st.columns(3)

    with activator_col1:

        render_html("""
        <div class="feature-card">
            <div class="feature-icon">🔐</div>
            <h3>Genuine Licenses</h3>
            <p>Offer only legitimate licenses from authorized sources.</p>
        </div>
        """)

    with activator_col2:

        render_html("""
        <div class="feature-card">
            <div class="feature-icon">💰</div>
            <h3>Clear Pricing</h3>
            <p>Confirm the product, license type, terms and price before payment.</p>
        </div>
        """)

    with activator_col3:

        render_html("""
        <div class="feature-card">
            <div class="feature-icon">🛠️</div>
            <h3>Customer Support</h3>
            <p>Provide legitimate installation and activation guidance.</p>
        </div>
        """)

    st.warning(
        "Zi Activator Pro must not distribute cracked software, unauthorized "
        "product keys, KMS bypasses or activation circumvention tools. "
        "Verify reseller authorization and license terms before selling."
    )


# ============================================================
# 18. ABOUT PROJECT
# ============================================================

elif st.session_state.page == "About Project":

    st.title("About Zi Nova AI")

    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=180)

    render_html("""
    <div class="feature-card">
        <h3>Zi Nova AI</h3>
        <p>An Intelligence Platform</p>
        <p>
            Zi Nova AI combines AI-powered image understanding,
            content generation, conversational assistance,
            voice transcription and spoken responses in one workspace.
        </p>
    </div>
    """)

    st.markdown("### Available Modules")

    st.write("- Smart Caption Studio")
    st.write("- AI Image Generation (inside Zi AI Assistant)")
    st.write("- Chat Assistant")
    st.write("- AI Voice Assistant")
    st.write("- Image Intelligence")
    st.write("- AI Image Size Reducer")
    st.write("- Zi Activator Pro (Windows and Microsoft Office enquiries)")
    st.write("- Optional public web search")

    st.markdown("### Technology Stack")

    st.write(f"**Text AI:** {TEXT_MODEL}")
    st.write(f"**Vision AI:** {VISION_MODEL}")
    st.write("**AI Provider:** Groq + Google Gemini")
    st.write("**Image Generation:** Cloudflare FLUX.1 Schnell + Pollinations FLUX + optional Gemini")
    st.write("**Speech Recognition:** Groq Whisper")
    st.write("**Voice Generation:** Google Text-to-Speech")
    st.write("**Web Search:** DuckDuckGo")
    st.write("**Image Processing:** Pillow")
    st.write("**Framework:** Streamlit")
    st.write("**Language:** Python")


# ============================================================
# 19. FOOTER
# ============================================================

render_html("""
<div class="footer">
    ✦ ZI NOVA AI
    <br><br>
    ONE PLATFORM. INFINITE INTELLIGENCE.
    <br>
    AN INTELLIGENCE PLATFORM
</div>
""")
