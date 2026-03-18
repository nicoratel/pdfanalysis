#!/bin/bash
# Launch PDF Analysis Streamlit App
# Fixes libstdc++ CXXABI_1.3.15 conflict between system and conda env

conda activate diffpy
export LD_PRELOAD=$(find $CONDA_PREFIX -name "libstdc++.so.6" | head -1)
echo "Using libstdc++: $LD_PRELOAD"
streamlit run app_pdf_analysis.py