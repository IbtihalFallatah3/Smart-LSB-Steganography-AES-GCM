import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
import base64
from io import BytesIO
import streamlit as st
from PIL import Image
import numpy as np
import cv2

from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes

st.set_page_config(page_title="IMAGE STEGANOGRAPHY", page_icon="🛡️", layout="centered")

# Style
def inject_style():
    st.markdown("""
    <style>
    html, body {
        background:
          radial-gradient(1000px 500px at 20% 5%, #e8f1ff, transparent 45%),
          radial-gradient(1000px 500px at 80% 0%, #dff8ff, transparent 55%),
          linear-gradient(180deg, #f7fbff 0%, #eaf3ff 50%, #eefaff 100%) !important;
        color: #0b1220;
    }
    [data-testid="stAppViewContainer"] {
        background:
          radial-gradient(1000px 500px at 20% 5%, #e8f1ff, transparent 45%),
          radial-gradient(1000px 500px at 80% 0%, #dff8ff, transparent 55%),
          linear-gradient(180deg, #f7fbff 0%, #eaf3ff 50%, #eefaff 100%) !important;
        background-attachment: fixed;
    }

    .hero { text-align:center; margin:5vh 0 2vh 0; color:#0b1220; line-height:1.0; }
    .hero .line { display:block; font-weight:900; }
    .hero .line-1, .hero .line-2 { font-size:clamp(52px,7.5vw,96px); }

    [data-baseweb="tab"] {
        border-radius: 12px !important;
        background: #eef3ff !important;
        color: #2f3a4a !important; font-weight: 700;
        box-shadow: inset 0 0 0 1px #dbe6ff;
    }
    [data-baseweb="tab"]:nth-child(1)[aria-selected="true"] {
        background: #ffe5e9 !important; color: #e11d48 !important;
        box-shadow: inset 0 0 0 2px #fecdd3;
    }
    [data-baseweb="tab"]:nth-child(2)[aria-selected="true"] {
        background: #fff1da !important; color: #d97706 !important;
        box-shadow: inset 0 0 0 2px #fde68a;
    }

    /* File uploader (bright) */
    [data-testid="stFileUploaderDropzone"] {
        background:#fff !important; border:2px dashed #7aa2ff !important;
        border-radius:14px !important; color:#1a1f2b !important; padding:1.2rem !important;
        box-shadow:0 4px 12px rgba(0,0,0,0.05);
    }
    [data-testid="stFileUploaderDropzone"] p { color:#2f3a4a !important; font-weight:600 !important; }
    [data-testid="stFileUploaderDropzone"] button {
        background: linear-gradient(90deg, #6C63FF, #00BFA6) !important;
        color:#fff !important; border:none !important; border-radius:8px !important;
    }
    [data-testid="stFileUploaderFileName"] {
        color:#0b1220 !important; background:#fff !important; border-radius:8px; padding:4px 8px;
        box-shadow:0 1px 4px rgba(0,0,0,0.1);
    }

    /* Inputs: white bg + dark text */
    label { color:#0b1220 !important; font-weight:700 !important; }
    .stTextInput > div > div, div[data-baseweb="input"] {
        background:#fff !important; border:1.6px solid #cfe0ff !important;
        border-radius:12px !important; box-shadow:0 1px 4px rgba(0,0,0,.06);
    }
    .stTextInput input, div[data-baseweb="input"] input { color:#0b1220 !important; background:#fff !important; }
    .stTextArea > div > div {
        background:#fff !important; border:1.6px solid #cfe0ff !important;
        border-radius:12px !important; box-shadow:0 1px 4px rgba(0,0,0,.06);
    }
    .stTextArea textarea { color:#0b1220 !important; background:#fff !important; }
    .stTextInput input::placeholder, .stTextArea textarea::placeholder { color:#4b5563 !important; opacity:1 !important; }
    .stTextInput svg { color:#475569 !important; }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #6C63FF, #00BFA6) !important;
        color:#fff !important; border:0 !important; border-radius:12px !important;
        padding:.7rem 1rem !important; box-shadow:0 8px 18px rgba(0,0,0,.08); font-weight:600 !important;
    }
    .stButton > button:hover { filter:brightness(.96); transform:translateY(-1px); }

    /* Password rule chips & meter */
    .rulegrid { display:flex; flex-wrap:wrap; gap:8px; margin:.4rem 0 .6rem; }
    .rulebtn { border-radius:999px; padding:6px 10px; font-weight:700; border:1px solid; font-size:.88rem; }
    .ok { color:#065f46; background:#d1fae5; border-color:#10b981; }
    .bad { color:#7f1d1d; background:#fee2e2; border-color:#ef4444; }
    .meter { width:100%; height:10px; border-radius:8px; background:#e6edf7; overflow:hidden; border:1px solid #d6e2f1; }
    .meter > span { height:100%; display:block; transition:width .25s ease; }

    /* RESULT CARD: force dark text */
    .result-card {
        background:#ffffff !important;
        color:#0b1220 !important;
        border:1.6px solid #cfe0ff !important;
        border-radius:12px !important;
        padding:12px !important;
        box-shadow:0 1px 6px rgba(0,0,0,.08);
        white-space:pre-wrap;
        word-break:break-word;
    }
    </style>
    """, unsafe_allow_html=True)

inject_style()

# Crypto
def derive_key(secret: str, salt: bytes) -> bytes:
    return PBKDF2(secret.encode(), salt, dkLen=32, count=200_000)

def aes_encrypt(plain: bytes, secret: str) -> bytes:
    salt, iv = get_random_bytes(16), get_random_bytes(12)
    key = derive_key(secret, salt)
    cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
    ct, tag = cipher.encrypt_and_digest(plain)
    return salt + iv + tag + ct 

def aes_decrypt(blob: bytes, secret: str) -> bytes:
    salt, iv, tag, ct = blob[:16], blob[16:28], blob[28:44], blob[44:]
    key = derive_key(secret, salt)
    cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
    return cipher.decrypt_and_verify(ct, tag)

# Stego
DELIM = "11111111111111111111111111111110"  

def to_bits(txt: str) -> str:
    b = txt.encode("utf-8")
    return "".join(f"{x:08b}" for x in b) + DELIM

def bits_to_text(bits: str) -> str:
    end = bits.find(DELIM)
    if end != -1:
        bits = bits[:end]
    if len(bits) % 8 != 0:
        bits = bits[: len(bits) - (len(bits) % 8)]
    if not bits:
        return ""
    data = bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))
    return data.decode("utf-8", errors="ignore")

def hide_bits(img: Image.Image, bits: str) -> Image.Image:
    out = img.convert("RGB").copy()
    px = out.load(); w, h = out.size; i = 0
    for y in range(h):
        for x in range(w):
            if i >= len(bits): return out
            r, g, b = px[x, y]
            if i < len(bits): r = (r & 0xFE) | int(bits[i]); i += 1
            if i < len(bits): g = (g & 0xFE) | int(bits[i]); i += 1
            if i < len(bits): b = (b & 0xFE) | int(bits[i]); i += 1
            px[x, y] = (r, g, b)
    return out

def extract_bits(img: Image.Image) -> str:
    px = img.convert("RGB").load(); w, h = img.size
    out_bits = []
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            out_bits.extend((str(r & 1), str(g & 1), str(b & 1)))
    return "".join(out_bits)

# Face detection and Quality
def detect_faces_pil(pil_img: Image.Image):
    try:
        gray = cv2.cvtColor(np.array(pil_img.convert("RGB")), cv2.COLOR_RGB2GRAY)
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        face_cascade = cv2.CascadeClassifier(cascade_path)
        if face_cascade.empty():
            return -1, []  
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))
        return len(faces), faces.tolist() if isinstance(faces, np.ndarray) else []
    except Exception:
        return -1, [] 

def assess_image_quality(pil_img: Image.Image):
    arr = np.array(pil_img.convert("RGB"))
    h, w = arr.shape[:2]
    min_dim = min(h, w)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)

    var_lap = float(cv2.Laplacian(gray, cv2.CV_64F).var())  # sharpness
    mean_brightness = float(gray.mean())

    reasons = []

    if min_dim < 64 or (h * w) < (64 * 64):
        return "Cannot be used", {"var_lap": var_lap, "brightness": mean_brightness, "w": w, "h": h}, ["Very small resolution"]

    if var_lap < 10: 
        return "Cannot be used", {"var_lap": var_lap, "brightness": mean_brightness, "w": w, "h": h}, ["Extremely blurry"]

    if var_lap < 60:
        rating = "Bad"; reasons.append("Blurry (low sharpness)")
    elif var_lap < 140:
        rating = "Medium"; reasons.append("Moderate sharpness")
    else:
        rating = "Good"; reasons.append("Sharp image")

    if mean_brightness < 40:
        reasons.append("Very dark")
        rating = "Bad" if rating == "Medium" else ("Medium" if rating == "Good" else rating)
    elif mean_brightness > 215:
        reasons.append("Overexposed")
        rating = "Bad" if rating == "Medium" else ("Medium" if rating == "Good" else rating)

    return rating, {"var_lap": var_lap, "brightness": mean_brightness, "w": w, "h": h}, reasons

# Password rules
SPECIALS = set("!@#$%^&*()_+-=[]{};':\",.<>/?`~\\|")

def check_secret_policy(s: str):
    s = (s or "").strip()
    return {
        "≥ 6 chars": len(s) >= 6,
        "Uppercase": any(c.isupper() for c in s),
        "Lowercase": any(c.islower() for c in s),
        "Digit": any(c.isdigit() for c in s),
        "Special": any(c in SPECIALS for c in s),
    }

def all_rules_ok(states: dict) -> bool:
    return all(states.values())

def strength_score(s: str):
    s = (s or "").strip()
    score = 0
    if len(s) >= 6: score += 20
    if len(s) >= 10: score += 20
    if any(c.islower() for c in s): score += 15
    if any(c.isupper() for c in s): score += 15
    if any(c.isdigit() for c in s): score += 15
    if any(c in SPECIALS for c in s): score += 15
    score = min(score, 100)
    if score < 40: return score, "Weak", "#ef4444"
    if score < 70: return score, "Medium", "#f59e0b"
    return score, "Strong", "#10b981"

def render_rules(states: dict):
    html = '<div class="rulegrid">'
    for name, ok in states.items():
        cls = "ok" if ok else "bad"
        icon = "✅" if ok else "⛔️"
        html += f'<span class="rulebtn {cls}">{icon}&nbsp;{name}</span>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

def render_meter(score:int,label:str,color:str):
    st.markdown(
        f"""
        <div class="meter"><span style="width:{score}%;background:{color};"></span></div>
        <div style="margin-top:6px;color:#415a77;font-size:0.9rem;"><b>{label}</b> ({score}%)</div>
        """,
        unsafe_allow_html=True,
    )

# UI 
st.markdown("""
<div class="hero">
  <span class="line line-1">IMAGE</span>
  <span class="line line-2">STEGANOGRAPHY</span>
</div>
""", unsafe_allow_html=True)

tabs = st.tabs(["🔒 Hide Message", "🗝️ Extract Message"])

with tabs[0]:
    up = st.file_uploader("Upload PNG image", type=["png"])
    if up:
        img = Image.open(up).convert("RGB")
        st.image(img, caption="Original Image", width="stretch")

        face_count, _ = detect_faces_pil(img)
        quality_label, quality_metrics, quality_reasons = assess_image_quality(img)

        col1, col2 = st.columns(2)
        with col1:
            if face_count == -1:
                st.warning("⚠️ Face detector unavailable in this environment.")
            elif face_count > 0:
                st.error(f"🚫 Faces detected: {face_count}. It is prohibited to use images with faces.")
            else:
                st.success("✅ No faces detected.")

        with col2:
            if quality_label == "Cannot be used":
                st.error("🧪 Image quality: Cannot be used")
            elif quality_label == "Bad":
                st.warning("🧪 Image quality: Bad")
            elif quality_label == "Medium":
                st.info("🧪 Image quality: Medium")
            else:
                st.success("🧪 Image quality: Good")


        secret = st.text_input(
            "Enter your secret key:",
            type="password",
            placeholder="At least 6 chars, mixed types…"
        )
        states = check_secret_policy(secret or "")
        with st.expander("Secret-Key Rules (must pass all)", expanded=True):
            render_rules(states)
        if secret:
            score, lbl, col = strength_score(secret)
            render_meter(score, lbl, col)

        msg = st.text_area("Message to hide:", placeholder="Type your secret message…")

        faces_ok = (face_count == 0) if face_count != -1 else True  
        quality_ok = (quality_label != "Cannot be used")

        can_encrypt = all_rules_ok(states) and bool(msg) and faces_ok and quality_ok
        btn = st.button("🕵️ Encrypt & Hide", disabled=not can_encrypt)

        if not faces_ok:
            st.stop()

        if not quality_ok:
            st.stop()

        if btn:
            try:
                enc = aes_encrypt((msg or "").encode("utf-8"), secret)
                b64 = base64.b64encode(enc).decode("utf-8")
                bits = to_bits(b64)
                capacity = img.size[0] * img.size[1] * 3
                if len(bits) > capacity:
                    st.error("Message is too large for this image.")
                else:
                    stego = hide_bits(img, bits)
                    buf = BytesIO()
                    stego.save(buf, format="PNG")
                    buf.seek(0)
                    st.success("✅ Hidden successfully!")
                    st.image(stego, caption="Stego Image", width="stretch")
                    st.download_button(
                        "⬇️ Download stego_image.png",
                        buf,
                        file_name="stego_image.png",
                        mime="image/png"
                    )
            except Exception as e:
                st.error(f"Error: {e}")

with tabs[1]:
    up2 = st.file_uploader("Upload Stego PNG", type=["png"], key="extract_up")
    if up2:
        img2 = Image.open(up2).convert("RGB")
        st.image(img2, caption="Stego Image", width="stretch")
        key2 = st.text_input(
            "Enter your secret key:",
            type="password",
            key="extract_key",
            placeholder="Use the same key you used to hide"
        )
        if st.button("🔍 Extract Message"):
            try:
                bits = extract_bits(img2)
                if DELIM not in bits:
                    st.error("No hidden message found.")
                else:
                    txt = bits_to_text(bits)  # base64 string
                    try:
                        blob = base64.b64decode(txt)
                        msg = aes_decrypt(blob, key2).decode("utf-8", errors="replace")
                        st.success("✅ Decrypted message:")
                        safe = (
                            msg.replace("&","&amp;")
                               .replace("<","&lt;")
                               .replace(">","&gt;")
                        )
                        st.markdown(f"<div class='result-card'>{safe}</div>", unsafe_allow_html=True)
                    except ValueError:
                        st.error("❌ Wrong key or corrupted image data (AES authentication failed).")
            except Exception as e:
                st.error(f"Error: {e}")
