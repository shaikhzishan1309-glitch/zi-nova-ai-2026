import os
import io
import base64
from pathlib import Path

import streamlit as st
from PIL import Image, ImageOps
from dotenv import load_dotenv
from groq import Groq
from gtts import gTTS


# ============================================================
# 1. CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
LOGO_PATH = ASSETS_DIR / "zinova_ai_logo.png"

load_dotenv(BASE_DIR / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

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
    "reducer_result": None,
    "voice_result": None
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

    /* TOP HEADER */

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

    /* WORKSPACE NAVIGATION */

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

    /* CARDS */

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

    /* ASSISTANT MODE CARDS */

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

    /* BUTTONS */

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

    /* INPUTS */

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

    [data-testid="stChatInput"] {{
        background: {T["surface"]} !important;
        border: 1px solid {T["border"]} !important;
        border-radius: 14px !important;
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

    @media(max-width:700px) {{
        .hero {{
            padding: 35px 15px;
        }}

        .hero h1 {{
            font-size: 35px;
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
# 6. WEB SEARCH
# ============================================================

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
            "If uncertain, say so."
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
# 11. SIDEBAR
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

    if GROQ_API_KEY:
        st.success("Groq API key detected")
    else:
        st.warning("Groq API key not configured")

    st.caption("Zi Nova AI · An Intelligence Platform")


# ============================================================
# 12. HOME PAGE
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
# 13. CAPTION STUDIO
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
# 14. ZI AI ASSISTANT
# ============================================================

elif st.session_state.page == "Zi AI Assistant":

    st.title("◈ Zi AI Assistant")
    st.caption("Choose how you want to interact with Zi.")

    if not require_api_key():
        st.stop()

    chat_tab, voice_tab = st.tabs([
        "◈ Chat Assistant",
        "🎙️ AI Voice Assistant"
    ])

    # --------------------------------------------------------
    # 14A. CHAT ASSISTANT
    # --------------------------------------------------------

    with chat_tab:

        st.subheader("Chat Assistant")

        st.caption(
            "Text conversations, web research and image intelligence."
        )

        st.toggle(
            "Enable web search",
            key="web_on"
        )

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        question = st.chat_input(
            "Message Zi...",
            key="zi_chat_input"
        )

        if question:

            st.session_state.messages.append({
                "role": "user",
                "content": question
            })

            try:
                with st.spinner("Zi is thinking..."):

                    sources = []

                    if st.session_state.web_on:
                        sources = search_web(question)

                    search_context = ""

                    if sources:
                        search_context = (
                            "\n\nWeb research results:\n"
                            + "\n".join(
                                f"{s['title']}: {s['url']} "
                                f"{s['snippet']}"
                                for s in sources
                            )
                        )

                    answer = generate_text(
                        question + search_context,
                        st.session_state.messages[:-1]
                    )

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer
                })

                st.session_state.last_sources = sources
                st.rerun()

            except Exception as error:
                st.error(f"Chat Assistant error: {error}")

        if st.session_state.last_sources:
            render_sources(st.session_state.last_sources)

        st.divider()

        st.subheader("Image Intelligence")

        chat_image = st.file_uploader(
            "Upload an image",
            type=["jpg", "jpeg", "png", "webp"],
            key="chat_image_upload"
        )

        image_question = st.text_input(
            "What should Zi look for?",
            value="Describe this image in detail.",
            key="chat_image_question"
        )

        if st.button(
            "Analyze Image",
            key="chat_analyze_button",
            use_container_width=True
        ):

            if chat_image is None:
                st.warning("Upload an image first.")
            else:
                try:
                    with st.spinner("Analyzing image..."):
                        image_url = image_to_data_url(chat_image)
                        image_answer = generate_vision_response(
                            image_url,
                            image_question
                        )

                    st.markdown("### Image Analysis")
                    st.write(image_answer)

                except Exception as error:
                    st.error(f"Image analysis failed: {error}")

        st.divider()

        if st.button(
            "Clear Chat History",
            key="clear_chat_button",
            use_container_width=True
        ):
            st.session_state.messages = []
            st.session_state.last_sources = []
            st.rerun()

    # --------------------------------------------------------
    # 14B. AI VOICE ASSISTANT
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
                # STEP 1: TRANSCRIPTION

                with st.spinner("Step 1/3: Understanding your voice..."):
                    spoken_question = transcribe_audio(audio_input)

                if not spoken_question:
                    st.warning("No speech detected. Please try again.")

                else:
                    st.markdown("### Your Spoken Command")
                    st.info(spoken_question)

                    # STEP 2: AI RESPONSE

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

                    # STEP 3: SPEECH GENERATION

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


# ============================================================
# 15. AI IMAGE SIZE REDUCER
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
# 16. ZI ACTIVATOR PRO
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

    # --------------------------------------------------------
    # WINDOWS ACTIVATION
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # MICROSOFT OFFICE ACTIVATION
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # SERVICE INFORMATION
    # --------------------------------------------------------

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
# 17. ABOUT PROJECT
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
    st.write("- Chat Assistant")
    st.write("- AI Voice Assistant")
    st.write("- Image Intelligence")
    st.write("- AI Image Size Reducer")
    st.write("- Zi Activator Pro (Windows and Microsoft Office enquiries)")
    st.write("- Optional public web search")

    st.markdown("### Technology Stack")

    st.write(f"**Text AI:** {TEXT_MODEL}")
    st.write(f"**Vision AI:** {VISION_MODEL}")
    st.write("**AI Provider:** Groq")
    st.write("**Speech Recognition:** Groq Whisper")
    st.write("**Voice Generation:** Google Text-to-Speech")
    st.write("**Web Search:** DuckDuckGo")
    st.write("**Image Processing:** Pillow")
    st.write("**Framework:** Streamlit")
    st.write("**Language:** Python")


# ============================================================
# 18. FOOTER
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