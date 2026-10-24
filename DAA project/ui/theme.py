"""
Design tokens and glassmorphism styling matching the dark Traffic Management reference.
"""

CSS_STYLES = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

:root {
    --bg-app: #0B0C0E;
    --card-surface: rgba(20, 22, 26, 0.72);
    --card-border: rgba(255, 255, 255, 0.07);
    --card-highlight: rgba(255, 255, 255, 0.04);
    --pill-active: #2A2D33;
    --pill-inactive: rgba(255, 255, 255, 0.05);
    --text-primary: #ECEDEF;
    --text-secondary: #8B8F97;
    --text-tertiary: #5A5E66;
    --status-green: #3DDC84;
    --status-red: #FF4D4F;
    --status-orange: #F59E42;
    --canvas-bg: #0A0B0D;
}

body {
    background-color: var(--bg-app) !important;
    background-image: radial-gradient(circle at 50% 20%, rgba(30, 34, 42, 0.4) 0%, rgba(11, 12, 14, 0.95) 75%) !important;
    color: var(--text-primary) !important;
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    letter-spacing: -0.02em;
    margin: 0;
    padding: 0;
    overflow-x: hidden;
    font-feature-settings: 'tnum' on, 'lnum' on;
}

.tabular-nums {
    font-variant-numeric: tabular-nums;
}

/* Glass Surface Styling */
.glass-panel {
    background: var(--card-surface);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border: 1px solid var(--card-border);
    box-shadow: inset 0 1px 1px 0 var(--card-highlight), 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    border-radius: 24px;
}

.glass-pill {
    background: var(--pill-inactive);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 9999px;
    transition: all 0.15s ease-in-out;
}

.glass-pill-active {
    background: var(--pill-active) !important;
    color: #FFFFFF !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

.glass-card-hover {
    transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
}

.glass-card-hover:hover {
    transform: translateY(-2px);
    border-color: rgba(255, 255, 255, 0.14);
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.45);
}

/* Typography tokens */
.page-hero-title {
    font-size: 44px;
    font-weight: 300;
    line-height: 1.1;
    letter-spacing: -0.03em;
    color: var(--text-primary);
}

.big-metric-num {
    font-size: 52px;
    font-weight: 300;
    letter-spacing: -0.03em;
    line-height: 1.0;
    color: #FFFFFF;
}

.big-metric-unit {
    font-size: 20px;
    font-weight: 400;
    color: var(--text-secondary);
    margin-left: 4px;
}

/* Custom Scrollbar */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: transparent;
}
::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.12);
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.22);
}

/* SVG Animations */
@keyframes routeGlow {
    0% { stroke-dashoffset: 200; }
    100% { stroke-dashoffset: 0; }
}

.animated-route {
    stroke-dasharray: 8, 4;
    animation: routeGlow 3s linear infinite;
}

.animated-shortest-path {
    stroke-dasharray: 400;
    animation: routeGlow 1.2s ease-out forwards;
}

.pulse-green {
    animation: pulseGlow 2s infinite;
}

@keyframes pulseGlow {
    0% { transform: scale(1); opacity: 0.9; }
    50% { transform: scale(1.15); opacity: 0.4; }
    100% { transform: scale(1); opacity: 0.9; }
}
"""
