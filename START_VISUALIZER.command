#!/bin/bash
# macOS: double-click this file to start the visual graph editor in your browser.
cd "$(dirname "$0")" || exit 1
printf '\nStarting CS 421 Graph Coloring Visualizer...\n'
python3 visualizer.py
printf '\nPress Enter to close this window.\n'
read -r
