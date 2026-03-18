"""
PDF Analysis Streamlit App
Based on perform_automatic_pdf_analysis from pdfanalysis.py
"""

import streamlit as st
import numpy as np
import plotly.graph_objects as go
import os
import tempfile
import shutil

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PDF Structure Analyzer",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}

/* Dark scientific theme */
.stApp {
    background-color: #0d1117;
    color: #e6edf3;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #161b22;
    border-right: 1px solid #30363d;
}

/* Metric cards */
.metric-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 16px 20px;
    margin: 8px 0;
}

/* Section headers */
h1, h2, h3 {
    font-family: 'IBM Plex Mono', monospace !important;
    letter-spacing: -0.5px;
}

/* Step badge */
.step-badge {
    display: inline-block;
    background: #238636;
    color: white;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    padding: 2px 10px;
    border-radius: 12px;
    margin-bottom: 8px;
}

/* Status indicator */
.status-ok { color: #3fb950; }
.status-warn { color: #d29922; }
.status-info { color: #58a6ff; }

/* Result box */
.result-box {
    background: #0d1117;
    border: 1px solid #238636;
    border-left: 4px solid #3fb950;
    border-radius: 6px;
    padding: 16px 20px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.85rem;
}

/* Override Streamlit primary button */
.stButton > button {
    background-color: #238636;
    color: white;
    border: none;
    border-radius: 6px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.9rem;
    font-weight: 600;
    padding: 10px 28px;
    width: 100%;
    transition: background 0.2s;
}
.stButton > button:hover {
    background-color: #2ea043;
}

/* Number input */
.stNumberInput input {
    font-family: 'IBM Plex Mono', monospace;
    background: #0d1117;
    color: #e6edf3;
    border: 1px solid #30363d;
}

/* Expander */
.streamlit-expanderHeader {
    font-family: 'IBM Plex Mono', monospace;
    color: #58a6ff;
}

/* Info/warning/success boxes */
.stAlert {
    border-radius: 6px;
}

div[data-testid="stMetricValue"] {
    font-family: 'IBM Plex Mono', monospace;
    color: #3fb950;
}
</style>
""", unsafe_allow_html=True)

# ── Title ─────────────────────────────────────────────────────────────────────
st.markdown("# 🔬 PDF Structure Analyzer")
st.markdown("*Automated Pair Distribution Function analysis with structure screening*")
st.divider()

# ── Helper: load PDF data ─────────────────────────────────────────────────────
def load_gr_file(file_obj):
    """Load .gr file, try common skiprows values."""
    content = file_obj.read()
    file_obj.seek(0)
    lines = content.decode("utf-8", errors="replace").splitlines()
    # find first numeric line
    skip = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            try:
                parts = stripped.split()
                float(parts[0]); float(parts[1])
                skip = i
                break
            except (ValueError, IndexError):
                continue
    data = np.loadtxt(lines[skip:], dtype=float)
    return data[:, 0], data[:, 1], skip

# ── Helper: plot G(r) with plotly (no libstdc++ issues) ──────────────────────
def plot_gr(r, g, r_coh=None, title="G(r)"):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=r, y=g,
        mode="lines",
        line=dict(color="#58a6ff", width=1.2),
        name="G(r) exp",
    ))

    # Zero line
    fig.add_hline(y=0, line=dict(color="#30363d", width=1, dash="dash"))

    # r_coh marker
    if r_coh is not None:
        fig.add_vline(
            x=r_coh,
            line=dict(color="#f78166", width=1.6, dash="dash"),
            annotation_text=f"r_coh = {r_coh:.2f} Å",
            annotation_font_color="#f78166",
            annotation_position="top right",
        )

    fig.update_layout(
        title=dict(text=title, font=dict(color="#e6edf3", size=13)),
        paper_bgcolor="#0d1117",
        plot_bgcolor="#161b22",
        xaxis=dict(title="r (Å)", color="#8b949e", gridcolor="#21262d",
                   zerolinecolor="#30363d"),
        yaxis=dict(title="G(r)", color="#8b949e", gridcolor="#21262d",
                   zerolinecolor="#30363d"),
        legend=dict(bgcolor="#161b22", bordercolor="#30363d",
                    font=dict(color="#e6edf3")),
        margin=dict(l=50, r=20, t=40, b=40),
        height=300,
    )
    return fig

# ════════════════════════════════════════════════════════════════════════════════
# SIDEBAR — File inputs & parameters
# ════════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 📂 Input Files")

    gr_file = st.file_uploader("PDF data file (.gr)", type=["gr", "txt", "dat"],
                                help="Experimental G(r) data file")
    cif_file_up = st.file_uploader("Crystal structure (.cif)", type=["cif"],
                                    help="Reference crystal structure")

    st.divider()
    st.markdown("### 📁 Output Directory")
    output_dir = st.text_input("Save results to",
                                placeholder="/data/experiment/",
                                help="Dossier où seront créés les structures, fits et rapport PDF")
    if output_dir and not os.path.isdir(output_dir):
        st.error("⚠️ Directory not found")
    elif output_dir:
        st.success(f"✓ `{output_dir}`")

    st.divider()
    st.markdown("### ⚙️ Parameters")

    with st.expander("Structure Generation", expanded=True):
        tolerance_size = st.number_input("Size tolerance (Å)", value=3.0, step=0.5, min_value=0.5)
        n_spheres      = st.number_input("Number of sphere sizes", value=2, step=1, min_value=1, max_value=20)
        max_search     = st.number_input("Max search parameter", value=25, step=1, min_value=5)

    with st.expander("Fast Screening"):
        rbins_fast      = st.number_input("rbins (fast)", value=5, step=1, min_value=1)
        rmin            = st.number_input("rmin (Å)", value=2.0, step=0.1)
        rmax_fast       = st.number_input("rmax fast (Å)", value=15.0, step=1.0)
        threshold_fast  = st.number_input("Threshold % (fast)", value=5.0, step=1.0)

    with st.expander("Fine Refinement"):
        rbins_fine = st.number_input("rbins (fine)", value=1, step=1, min_value=1)

# ════════════════════════════════════════════════════════════════════════════════
# MAIN PANEL
# ════════════════════════════════════════════════════════════════════════════════

col_left, col_right = st.columns([1.1, 1], gap="large")

# ── LEFT: G(r) preview + r_coh ───────────────────────────────────────────────
with col_left:
    st.markdown('<div class="step-badge">STEP 1</div>', unsafe_allow_html=True)
    st.markdown("#### Load & Preview G(r)")

    r_data, g_data = None, None

    if gr_file is not None:
        try:
            r_data, g_data, skiprows = load_gr_file(gr_file)
            st.success(f"✓ Loaded **{gr_file.name}** — {len(r_data)} data points, "
                       f"r ∈ [{r_data.min():.2f}, {r_data.max():.2f}] Å")

            # Auto-detect r_coh as soon as both files are available
            cache_key = f"r_coh_{gr_file.name}_{cif_file_up.name if cif_file_up else ''}"
            if cif_file_up is not None and cache_key not in st.session_state:
                with st.spinner("🔍 Auto-detecting r_coh…"):
                    tmp_rcoh = tempfile.mkdtemp(prefix="rcoh_")
                    try:
                        from .structure_generator import StructureGenerator
                        gr_tmp  = os.path.join(tmp_rcoh, gr_file.name)
                        cif_tmp = os.path.join(tmp_rcoh, cif_file_up.name)
                        gr_file.seek(0);     open(gr_tmp,  "wb").write(gr_file.read())
                        cif_file_up.seek(0); open(cif_tmp, "wb").write(cif_file_up.read())
                        gen = StructureGenerator(
                            pdfpath=tmp_rcoh, cif_file=cif_tmp, auto_mode=True,
                            pdf_file=gr_tmp, derivative_sigma=3.0,
                            amplitude_sigma=2.0, window_size=20)
                        detected = gen.analyze_pdf_and_get_rmax()
                        st.session_state[cache_key] = detected
                        st.session_state["r_coh_detected"] = detected
                    except Exception as e:
                        st.warning(f"Auto-detection failed: {e}")
                    finally:
                        shutil.rmtree(tmp_rcoh, ignore_errors=True)
            elif cache_key in st.session_state:
                st.session_state["r_coh_detected"] = st.session_state[cache_key]

            if cif_file_up is None:
                st.info("💡 Upload the .cif file to enable automatic r_coh detection.")

        except Exception as e:
            st.error(f"Could not parse file: {e}")

    # r_coh widget — shown once file is loaded
    st.markdown("---")
    st.markdown('<div class="step-badge">STEP 2</div>', unsafe_allow_html=True)
    st.markdown("#### Coherence Length r_coh")

    r_coh_value = None
    detected = st.session_state.get("r_coh_detected")

    if detected is not None:
        warn = detected < 15
        st.markdown(f"**Auto-detected r_coh:** `{detected:.2f} Å`"
                    + ("  ⚠️ *seems small, check visually*" if warn else "  ✅"))
        r_coh_value = st.number_input(
            "r_coh (Å) — edit if needed", value=float(detected),
            min_value=1.0, max_value=200.0, step=0.5,
            help="Pre-filled from auto-detection; adjust if the fit looks wrong")
    else:
        r_coh_value = st.number_input(
            "r_coh (Å)", value=20.0, min_value=1.0, max_value=200.0, step=0.5,
            help="Will be auto-detected once both files are loaded, or enter manually")

    # Plot
    if r_data is not None:
        fig = plot_gr(r_data, g_data, r_coh=r_coh_value, title=gr_file.name)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown(
            "<div style='background:#161b22;border:1px dashed #30363d;border-radius:8px;"
            "height:220px;display:flex;align-items:center;justify-content:center;"
            "color:#8b949e;font-family:IBM Plex Mono,monospace;'>Upload a .gr file to preview G(r)</div>",
            unsafe_allow_html=True)

# ── RIGHT: Launch + Results ───────────────────────────────────────────────────
with col_right:
    st.markdown('<div class="step-badge">STEP 3</div>', unsafe_allow_html=True)
    st.markdown("#### Run Analysis")

    # Readiness checks
    ready_gr  = gr_file is not None and r_data is not None
    ready_cif = cif_file_up is not None
    ready_out = bool(output_dir) and os.path.isdir(output_dir)
    ready = ready_gr and ready_cif and ready_out

    col_chk1, col_chk2 = st.columns(2)
    with col_chk1:
        if ready_gr:
            st.markdown("✅ G(r) file loaded")
        else:
            st.markdown("⬜ G(r) file needed")
    with col_chk2:
        if ready_cif:
            st.markdown("✅ CIF file loaded")
        else:
            st.markdown("⬜ CIF file needed")

    st.markdown("")

    run_button = st.button("🚀 Launch Analysis", disabled=not ready, use_container_width=True)

    if not ready_out:
        st.warning("⚠️ Set a valid output directory in the sidebar")
    elif not ready:
        st.caption("Upload both files to enable the analysis.")

    st.divider()

    # ── Run analysis ──────────────────────────────────────────────────────────
    if run_button and ready:
        # Create a working subdirectory inside the chosen output directory
        tmp_dir  = tempfile.mkdtemp(prefix="pdf_app_", dir=output_dir)
        gr_path  = os.path.join(tmp_dir, gr_file.name)
        cif_path = os.path.join(tmp_dir, cif_file_up.name)

        gr_file.seek(0);     open(gr_path,  "wb").write(gr_file.read())
        cif_file_up.seek(0); open(cif_path, "wb").write(cif_file_up.read())

        progress_bar = st.progress(0, text="Initialising…")
        st.markdown("**Live output:**")
        log_area  = st.empty()
        log_lines = []

        # ── Live stdout redirector ────────────────────────────────────────────
        import io, sys

        # Step keywords → progress %
        STEP_PROGRESS = {
            "STEP 1": (20, "Step 1/4 — Structure generation"),
            "STEP 2": (40, "Step 2/4 — Fast screening"),
            "STEP 3": (65, "Step 3/4 — Fine refinement"),
            "STEP 4": (85, "Step 4/4 — Report generation"),
            "ANALYSIS COMPLETE": (100, "✅ Analysis complete!"),
        }

        class LiveStream(io.TextIOBase):
            """Redirect write() calls to Streamlit in real time."""
            def __init__(self, real_stdout):
                self._real = real_stdout
                self._buf  = ""

            def write(self, text):
                self._real.write(text)   # keep console output too
                self._real.flush()
                self._buf += text
                # flush complete lines
                while "\n" in self._buf:
                    line, self._buf = self._buf.split("\n", 1)
                    line = line.rstrip()
                    if line:
                        log_lines.append(line)
                        # keep last 40 lines visible
                        log_area.code("\n".join(log_lines[-40:]), language="text")
                        # update progress bar if line matches a step keyword
                        for kw, (pct, label) in STEP_PROGRESS.items():
                            if kw in line:
                                progress_bar.progress(pct, text=label)
                                break
                return len(text)

            def flush(self):
                self._real.flush()

        all_lines = log_lines  # reference shared with LiveStream

        try:
            from .pdfanalysis import perform_automatic_pdf_analysis

            log_lines.append("✓ Module imported")
            log_lines.append(f"r_coh = {r_coh_value:.2f} Å")
            log_area.code("\n".join(log_lines), language="text")
            progress_bar.progress(10, text="Starting analysis…")

            old_stdout = sys.stdout
            sys.stdout = LiveStream(old_stdout)

            try:
                perform_automatic_pdf_analysis(
                    pdf_file=gr_path,
                    cif_file=cif_path,
                    r_coh=r_coh_value,
                    tolerance_size_structure=float(tolerance_size),
                    n_spheres=int(n_spheres),
                    max_search_param=int(max_search),
                    rbins_fast=int(rbins_fast),
                    rmin=float(rmin),
                    rmax_fast=float(rmax_fast),
                    threshold_percent_fast=float(threshold_fast),
                    rbins_fine=int(rbins_fine),
                    verbose=False,
                )
            finally:
                sys.stdout = old_stdout

            progress_bar.progress(100, text="✅ Analysis complete!")

            # Parse key results from all captured lines
            captured_text = "\n".join(log_lines)
            results = {}
            for line in log_lines:
                if "Rw:" in line:
                    try: results["Rw"] = float(line.split("Rw:")[-1].strip())
                    except: pass
                if "Zoomscale:" in line:
                    try: results["Zoomscale"] = float(line.split("Zoomscale:")[-1].strip())
                    except: pass
                if "Nombre d'atomes:" in line or "Number of atoms:" in line:
                    try: results["Atoms"] = line.split(":")[-1].strip()
                    except: pass
                if "Composition:" in line:
                    try: results["Composition"] = line.split("Composition:")[-1].strip()
                    except: pass
                if "Best structure:" in line:
                    try: results["Structure"] = line.split("Best structure:")[-1].strip()
                    except: pass
                if "Report saved:" in line:
                    try: results["Report"] = line.split("Report saved:")[-1].strip()
                    except: pass

            # Display results
            if results:
                st.markdown("#### 📊 Results Summary")
                cols = st.columns(2)
                if "Rw" in results:
                    cols[0].metric("Rw factor", f"{results['Rw']:.4f}")
                if "Zoomscale" in results:
                    cols[1].metric("Zoomscale", f"{results['Zoomscale']:.6f}")
                if "Atoms" in results:
                    cols[0].metric("Num. atoms", results["Atoms"])
                if "Composition" in results:
                    cols[1].metric("Composition", results["Composition"])
                if "Structure" in results:
                    st.markdown(f"**Best structure:** `{results['Structure']}`")

            # Offer report download if it was saved
            report_path = results.get("Report", "").strip()
            if report_path and os.path.isfile(report_path):
                with open(report_path, "rb") as fp:
                    st.download_button(
                        label="⬇️ Download PDF Report",
                        data=fp,
                        file_name=os.path.basename(report_path),
                        mime="application/pdf",
                        use_container_width=True,
                    )

        except ImportError as e:
            progress_bar.empty()
            st.error(f"Import error: {e}\n\nMake sure the pdfanalysis package is properly installed "
                     f"with all required modules.")
        except Exception as e:
            progress_bar.empty()
            st.exception(e)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
            st.caption("🗑️ Temporary working folder cleaned up")

    # ── Previous detection display ────────────────────────────────────────────
    elif "r_coh_detected" in st.session_state:
        st.markdown("#### Last detected r_coh")
        st.markdown(
            f'<div class="result-box">r_coh = <strong>{st.session_state.r_coh_detected:.2f} Å</strong></div>',
            unsafe_allow_html=True)

    else:
        st.markdown(
            "<div style='background:#161b22;border:1px dashed #30363d;border-radius:8px;"
            "padding:40px;text-align:center;color:#8b949e;font-family:IBM Plex Mono,monospace;"
            "font-size:0.85rem;'>Results will appear here after analysis</div>",
            unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption("PDF Structure Analyzer · Built with Streamlit · Powered by diffpy.cmi")
