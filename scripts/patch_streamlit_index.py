"""
Helper script to patch Streamlit's static index.html with the instant splash preloader.
Ensures zero-delay, zero-flash loader presentation on website open or browser refresh.
"""
import os
import streamlit

LOADER_CSS = """
    <style>
      /* -----------------------------------------------------------------------
         INSTANT LIGHT GREEN & BLUE MIX 3D SPLASH PRELOADER (2 SECONDS SMOOTH FLOW)
         ----------------------------------------------------------------------- */
      .faslyn-loader-container {
          position: fixed;
          top: 0;
          left: 0;
          width: 100vw;
          height: 100vh;
          background: radial-gradient(circle at 45% 35%, #F0FDF4 0%, #E0F2FE 45%, #E6F7EE 75%, #DCEEFE 100%);
          z-index: 99999999;
          display: flex;
          align-items: center;
          justify-content: center;
          overflow: hidden;
          pointer-events: auto;
          will-change: opacity;
          animation: faslynContainerFlow 2.0s forwards;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      }

      .faslyn-loader-card {
          background: #FFFFFF;
          border: 1px solid rgba(220, 240, 230, 0.9);
          border-bottom: 4px solid #10B981;
          border-radius: 26px;
          padding: 36px 44px;
          box-shadow: 0 24px 60px -12px rgba(16, 114, 85, 0.16),
                      0 10px 25px -6px rgba(2, 132, 199, 0.12),
                      0 0 0 1px rgba(255, 255, 255, 0.9);
          display: flex;
          flex-direction: column;
          align-items: center;
          text-align: center;
          gap: 14px;
          max-width: 360px;
          width: 90%;
          box-sizing: border-box;
          will-change: transform, opacity;
          animation: faslynCardFlow 2.0s forwards;
      }

      .faslyn-spinner-wrapper {
          position: relative;
          width: 70px;
          height: 70px;
          display: flex;
          align-items: center;
          justify-content: center;
          margin-bottom: 4px;
      }

      .faslyn-spinner-ring {
          position: absolute;
          width: 100%;
          height: 100%;
          border-radius: 50%;
          border: 3.5px solid rgba(16, 185, 129, 0.16);
          border-top: 3.5px solid #10B981;
          border-right: 3.5px solid #0284C7;
          box-shadow: 0 4px 14px rgba(2, 132, 199, 0.18);
          animation: faslynSpin 1.0s linear infinite;
      }

      .faslyn-spinner-icon {
          font-size: 30px;
          animation: faslynPulse 1.4s ease-in-out infinite;
          display: flex;
          align-items: center;
          justify-content: center;
      }

      .faslyn-loader-brand {
          font-size: 1.65rem;
          font-weight: 800;
          color: #1B4D3E;
          letter-spacing: -0.5px;
          line-height: 1.1;
      }

      .faslyn-loader-subtitle {
          font-size: 0.84rem;
          font-weight: 600;
          color: #4B5563;
          line-height: 1.3;
      }

      .faslyn-loader-track {
          width: 190px;
          height: 6px;
          background: rgba(2, 132, 199, 0.12);
          border-radius: 9999px;
          overflow: hidden;
          margin-top: 4px;
      }

      .faslyn-loader-bar {
          height: 100%;
          background: linear-gradient(90deg, #10B981 0%, #0284C7 50%, #34D399 100%);
          border-radius: 9999px;
          animation: faslynProgressFill 1.35s cubic-bezier(0.2, 0.7, 0.3, 1) forwards;
      }

      .faslyn-loader-status {
          font-size: 0.75rem;
          font-weight: 600;
          color: #6B7280;
          letter-spacing: 0.2px;
      }

      @keyframes faslynProgressFill {
          0% { width: 0%; }
          25% { width: 35%; }
          65% { width: 75%; }
          90% { width: 95%; }
          100% { width: 100%; }
      }

      @keyframes faslynSpin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
      }

      @keyframes faslynPulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.12); }
      }

      @keyframes faslynCardFlow {
          0% {
              transform: scale(0.92);
              opacity: 0;
              animation-timing-function: cubic-bezier(0.16, 1, 0.3, 1);
          }
          18% {
              transform: scale(1);
              opacity: 1;
              animation-timing-function: linear;
          }
          67% {
              transform: scale(1);
              opacity: 1;
              animation-timing-function: cubic-bezier(0.25, 1, 0.5, 1);
          }
          100% {
              transform: scale(1.28);
              opacity: 0;
              visibility: hidden;
          }
      }

      @keyframes faslynContainerFlow {
          0% {
              opacity: 1;
              visibility: visible;
              pointer-events: auto;
              animation-timing-function: linear;
          }
          67% {
              opacity: 1;
              visibility: visible;
              pointer-events: auto;
              animation-timing-function: cubic-bezier(0.25, 1, 0.5, 1);
          }
          100% {
              opacity: 0;
              visibility: hidden;
              pointer-events: none;
          }
      }
    </style>
"""

LOADER_HTML = """
    <div id="faslyn-loader-overlay" class="faslyn-loader-container">
        <div class="faslyn-loader-card">
            <div class="faslyn-spinner-wrapper">
                <div class="faslyn-spinner-ring"></div>
                <div class="faslyn-spinner-icon">🌱</div>
            </div>
            <div class="faslyn-loader-brand">🌿 faslyn</div>
            <div class="faslyn-loader-subtitle">Smart Agriculture &bull; Stronger Communities</div>
            <div class="faslyn-loader-track">
                <div class="faslyn-loader-bar"></div>
            </div>
            <div class="faslyn-loader-status">Initializing agro-intelligence feeds...</div>
        </div>
    </div>
    <script>
      setTimeout(function() {
        var el = document.getElementById('faslyn-loader-overlay');
        if (el) { el.style.display = 'none'; }
      }, 2100);
    </script>
"""

def patch_streamlit_index():
    static_dir = os.path.join(os.path.dirname(streamlit.__file__), "static")
    index_path = os.path.join(static_dir, "index.html")
    if not os.path.exists(index_path):
        print(f"File not found: {index_path}")
        return False

    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()

    if "faslyn-loader-overlay" in content:
        print("index.html is already patched with faslyn preloader.")
        return True

    # Inject CSS before </head>
    if "</head>" in content:
        content = content.replace("</head>", f"{LOADER_CSS}\n  </head>")

    # Inject HTML before <div id="root"></div>
    root_div = '<div id="root"></div>'
    if root_div in content:
        content = content.replace(root_div, f"{LOADER_HTML}\n    {root_div}")

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Successfully patched {index_path} with instant faslyn preloader.")
    return True

if __name__ == "__main__":
    patch_streamlit_index()
