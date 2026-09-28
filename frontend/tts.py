"""
Client-Side Text-to-Speech
===========================
Injects a small <script> block that uses the browser's native
window.speechSynthesis API — zero server cost, works over laptop
speakers during a live presentation with no external audio service.
"""

import json

import streamlit as st


def speak_text(text: str, lang_code: str = "en-US") -> None:
    """Render an invisible component that speaks `text` aloud in the browser."""
    safe_text = json.dumps(text)
    safe_lang = json.dumps(lang_code)
    html_code = f"""
    <script>
    (function() {{
        try {{
            const synth = window.speechSynthesis;
            synth.cancel();
            const utter = new SpeechSynthesisUtterance({safe_text});
            utter.lang = {safe_lang};
            utter.rate = 0.95;
            utter.pitch = 1.0;
            synth.speak(utter);
        }} catch (e) {{
            console.error("Faslyn TTS failed:", e);
        }}
    }})();
    </script>
    """
    st.components.v1.html(html_code, height=0)
