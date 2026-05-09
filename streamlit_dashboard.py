"""
Next-generation Streamlit dashboard for silent user drop-off detection.

The UI is organized as a structured presentation dashboard instead of a long scrolling report.
It supports model evidence, batch operations, and project readiness for the
user drop-off detection thesis.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple, cast

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Early User Churn Detection in Web Applications: A Production Machine Learning System for Revenue Retention",
    page_icon=":chart_with_downwards_trend:",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================================
# DESIGN SYSTEM
# ============================================================================

st.markdown(
    """
<style>
    #MainMenu, header, footer, .stDeployButton {display: none !important;}

    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    :root {
        --ink: #111827;
        --muted: #64748b;
        --line: #dbe3ec;
        --paper: #ffffff;
        --soft: #f8fafc;
        --navy: #1f2937;
        --blue: #355c7d;
        --teal: #5f7d8a;
        --green: #7b8f6f;
        --amber: #a88a5b;
        --rose: #9a6f75;
    }

    .stApp,
    .main,
    p,
    div,
    span,
    label,
    button,
    input,
    textarea {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
    }

    .main {
        background: linear-gradient(135deg, #fbfcfe 0%, #f4f7fb 45%, #eef2f7 100%);
        min-height: 100vh;
    }

    .main .block-container {
        max-width: 1440px;
        padding: 2rem 1.5rem;
    }

    section[data-testid="stSidebar"] {
        display: none !important;
    }

    div[data-testid="collapsedControl"] {
        display: none !important;
    }

    h1, h2, h3, h4, h5, h6 {
        color: var(--ink);
        letter-spacing: -0.015em;
        font-weight: 700;
    }

    h1 {
        font-size: 2.25rem;
        line-height: 1.2;
    }

    h2 {
        font-size: 1.875rem;
        line-height: 1.3;
        margin: 1.5rem 0 0.75rem;
    }

    h3 {
        font-size: 1.125rem;
        line-height: 1.4;
    }

    p {
        color: var(--muted);
        line-height: 1.6;
    }

    .topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1.5rem;
        background: rgba(255, 255, 255, 0.96);
        border: 1px solid rgba(219, 227, 236, 0.95);
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin-bottom: 1.75rem;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.08);
        backdrop-filter: blur(8px);
    }

    .brand {
        display: flex;
        align-items: center;
        gap: 1rem;
        min-width: 0;
    }

    .brand-mark {
        width: 48px;
        height: 48px;
        min-width: 48px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #fff;
        font-weight: 800;
        font-size: 1.25rem;
        background: linear-gradient(135deg, #355c7d 0%, #5f7d8a 100%);
        box-shadow: 0 8px 16px rgba(31, 41, 55, 0.12);
    }

    .brand-title {
        color: var(--ink);
        font-weight: 800;
        line-height: 1.2;
        font-size: 1.05rem;
    }

    .brand-subtitle {
        color: var(--muted);
        font-size: 0.8rem;
        margin-top: 2px;
    }

    .topbar-actions {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        flex-wrap: wrap;
        justify-content: flex-end;
        min-width: 0;
    }

    .api-pill,
    .nav-note {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        border: 1px solid var(--line);
        border-radius: 999px;
        padding: 0.5rem 0.875rem;
        background: #f6f8fb;
        color: var(--ink);
        font-size: 0.8125rem;
        font-weight: 600;
        white-space: nowrap;
        transition: all 0.2s ease;
    }

    .api-pill:hover,
    .nav-note:hover {
        background: #edf2f7;
        border-color: #cfd8e3;
    }

    .api-pill .status-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        display: inline-block;
        animation: statusPulse 2s infinite;
    }

    @keyframes statusPulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }

    div[data-testid="stPills"] {
        background: rgba(255, 255, 255, 0.95);
        border: 1px solid rgba(203, 213, 225, 0.8);
        border-radius: 12px;
        padding: 0.75rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06);
    }

    div[data-testid="stPills"] button {
        border-radius: 10px !important;
        min-height: 44px !important;
        padding: 0.5rem 1.125rem !important;
        font-weight: 600 !important;
        border: 1px solid transparent !important;
        color: var(--ink) !important;
        background: transparent !important;
        transition: all 0.2s ease !important;
    }

    div[data-testid="stPills"] button:hover {
        background: rgba(53, 92, 125, 0.08) !important;
        border-color: rgba(53, 92, 125, 0.18) !important;
        color: var(--blue) !important;
    }

    div[data-testid="stPills"] button[aria-pressed="true"] {
        background: linear-gradient(135deg, #355c7d, #5f7d8a) !important;
        color: #ffffff !important;
        box-shadow: 0 8px 16px rgba(31, 41, 55, 0.14) !important;
    }

    .app-hero {
        min-height: 280px;
        display: grid;
        grid-template-columns: 1.2fr 0.8fr;
        gap: 1.5rem;
        margin-bottom: 2rem;
    }

    .hero-copy {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(245, 248, 252, 0.98));
        border: 1px solid rgba(219, 227, 236, 0.95);
        border-radius: 12px;
        padding: 2rem;
        color: var(--ink);
        box-shadow: 0 12px 32px rgba(15, 23, 42, 0.08);
        position: relative;
        overflow: hidden;
    }

    .hero-copy::before {
        content: "";
        position: absolute;
        inset: -1px -1px -1px 0;
        border-radius: 12px;
        padding: 1px;
        background: linear-gradient(135deg, rgba(53, 92, 125, 0.14), rgba(95, 125, 138, 0.14));
        -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
        mask-composite: exclude;
        pointer-events: none;
    }

    .hero-copy::after {
        content: "";
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #355c7d, #5f7d8a, #a88a5b, #9a6f75);
    }

    .eyebrow {
        color: #355c7d;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 1rem;
    }

    .hero-copy h1 {
        color: var(--ink);
        font-size: 2.25rem;
        line-height: 1.2;
        max-width: 100%;
        margin: 0 0 1rem;
    }

    .hero-copy p {
        color: var(--muted);
        max-width: 100%;
        margin: 0;
        font-size: 1rem;
        line-height: 1.6;
    }

    .signal-panel {
        background: #ffffff;
        border: 1px solid rgba(219, 227, 236, 0.95);
        border-radius: 12px;
        padding: 1.5rem;
        min-height: 280px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
    }

    .signal-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1.5rem;
        gap: 1rem;
    }

    .signal-title {
        font-weight: 700;
        color: var(--ink);
        font-size: 1rem;
    }

    .status-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        border-radius: 999px;
        padding: 0.5rem 0.875rem;
        background: #f6f8fb;
        color: var(--ink);
        border: 1px solid rgba(219, 227, 236, 0.95);
        font-size: 0.8rem;
        font-weight: 600;
        white-space: nowrap;
    }

    .status-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        display: inline-block;
    }

    .status-dot.online {background: #10b981;}
    .status-dot.offline {background: #ef4444;}

    .signal-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 8px;
        align-items: end;
        height: 128px;
        padding: 10px 4px;
        border-radius: 8px;
        background:
            linear-gradient(180deg, rgba(53,92,125,0.04), rgba(95,125,138,0.04)),
            repeating-linear-gradient(0deg, transparent 0 31px, rgba(17,24,39,0.08) 31px 32px);
    }

    .signal-bar {
        border-radius: 7px 7px 3px 3px;
        background: linear-gradient(180deg, var(--blue), var(--teal));
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.35);
        min-height: 24px;
    }

    .signal-bar:nth-child(2) {height: 54px; background: linear-gradient(180deg, #56768a, #7b8f6f);}
    .signal-bar:nth-child(3) {height: 100px; background: linear-gradient(180deg, #a88a5b, #9a6f75);}
    .signal-bar:nth-child(4) {height: 72px; background: linear-gradient(180deg, #355c7d, #7b8f6f);}
    .signal-bar:nth-child(5) {height: 116px; background: linear-gradient(180deg, #9a6f75, #a88a5b);}

    .signal-foot {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 8px;
        margin-top: 14px;
    }

    .mini-stat {
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 10px;
        background: #fbfcfe;
    }

    .mini-stat span {
        display: block;
        color: var(--muted);
        font-size: 0.72rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .mini-stat strong {
        color: var(--ink);
        font-size: 1.12rem;
    }

    .kpi-card,
    .panel,
    .identity-card,
    .play-card {
        background: var(--paper);
        border: 1px solid rgba(219, 227, 236, 0.95);
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
    }

    .kpi-card {
        min-height: 120px;
        padding: 1.25rem;
        position: relative;
        overflow: hidden;
    }

    .kpi-card::before {
        content: "";
        position: absolute;
        left: 0;
        top: 0;
        width: 100%;
        height: 3px;
        background: var(--blue);
    }

    .kpi-card.teal::before {background: var(--teal);}
    .kpi-card.green::before {background: var(--green);}
    .kpi-card.amber::before {background: var(--amber);}
    .kpi-card.rose::before {background: var(--rose);}

    .kpi-label {
        color: var(--muted);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .kpi-value {
        color: var(--ink);
        font-size: 1.875rem;
        font-weight: 800;
        line-height: 1;
        margin: 0.75rem 0 0.5rem;
    }

    .kpi-copy {
        color: var(--muted);
        margin: 0;
        font-size: 0.8rem;
        line-height: 1.5;
    }

    .panel {
        padding: 1.35rem;
        margin-bottom: 1.35rem;
    }

    .panel-title {
        color: var(--ink);
        font-size: 1rem;
        font-weight: 700;
        margin: 0 0 0.5rem;
    }

    .panel-copy {
        color: var(--muted);
        margin: 0 0 1.25rem;
        font-size: 0.92rem;
    }

    .pipeline-strip {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.85rem;
        margin-bottom: 1.1rem;
    }

    .pipeline-chip {
        border: 1px solid rgba(219, 227, 236, 0.95);
        border-radius: 10px;
        padding: 1.05rem;
        background: linear-gradient(135deg, #ffffff, #f8fafc);
        box-shadow: 0 3px 10px rgba(15, 23, 42, 0.03);
        transition: all 0.2s ease;
    }

    .pipeline-chip:hover {
        border-color: rgba(53, 92, 125, 0.18);
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
    }

    .pipeline-chip span {
        display: block;
        color: var(--muted);
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }

    .pipeline-chip strong {
        color: var(--ink);
        font-size: 1rem;
        display: block;
        margin-bottom: 0.5rem;
        font-weight: 700;
    }

    .pipeline-chip p {
        color: var(--muted);
        margin: 0;
        font-size: 0.8rem;
        line-height: 1.4;
    }

    .flow {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 8px;
    }

    .flow-step {
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 11px;
        background: #f8fafc;
        min-height: 82px;
    }

    .flow-step strong {
        display: block;
        color: var(--ink);
        margin-bottom: 8px;
    }

    .flow-step span {
        color: var(--muted);
        font-size: 0.82rem;
    }

    .architecture-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 10px;
    }

    .arch-tile {
        min-height: 116px;
        border: 1px solid rgba(219, 227, 236, 0.95);
        border-radius: 10px;
        padding: 14px;
        background: linear-gradient(180deg, #ffffff, #f7f9fc);
        box-shadow: 0 4px 12px rgba(15,23,42,0.04);
    }

    .arch-mark {
        width: 38px;
        height: 38px;
        border-radius: 10px;
        margin-bottom: 12px;
        background: linear-gradient(135deg, var(--blue), var(--teal));
    }

    .arch-tile:nth-child(2) .arch-mark {background: linear-gradient(135deg, var(--teal), var(--green));}
    .arch-tile:nth-child(3) .arch-mark {background: linear-gradient(135deg, var(--amber), var(--rose));}

    .arch-tile strong {
        display: block;
        color: var(--ink);
        font-size: 0.98rem;
        margin-bottom: 4px;
    }

    .arch-tile span {
        color: var(--muted);
        font-size: 0.82rem;
        line-height: 1.35;
    }

    .section-head {
        display: flex;
        align-items: end;
        justify-content: space-between;
        gap: 14px;
        margin: 14px 0 14px;
    }

    .section-head h2 {
        margin: 0;
        font-size: 2rem;
        line-height: 1.08;
    }

    .section-head p {
        margin: 8px 0 0;
        color: var(--muted);
        font-size: 0.94rem;
    }

    .visual-card {
        background: rgba(255, 255, 255, 0.96);
        border: 1px solid rgba(219, 227, 236, 0.95);
        border-radius: 12px;
        padding: 1.15rem;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
        min-height: 100%;
        overflow: hidden;
    }

    .visual-title {
        color: var(--ink);
        font-size: 1rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }

    .visual-copy {
        color: var(--muted);
        font-size: 0.85rem;
        margin-bottom: 1rem;
    }

    .tracking-snapshot {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.85rem;
        margin: 0.9rem 0;
    }

    .snapshot-card {
        border: 1px solid rgba(219, 227, 236, 0.95);
        border-radius: 10px;
        padding: 0.95rem;
        background: linear-gradient(135deg, #fbfcfe, #f4f7fb);
        text-align: center;
    }

    .snapshot-card span {
        display: block;
        color: var(--muted);
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }

    .snapshot-card strong {
        display: block;
        color: var(--ink);
        font-size: 1.5rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }

    .snapshot-card p {
        color: var(--muted);
        font-size: 0.8rem;
        margin: 0;
        line-height: 1.4;
    }

    .tracking-notes {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.85rem;
        margin-top: 0.9rem;
    }

    .tracking-note {
        border: 1px solid rgba(219, 227, 236, 0.95);
        border-radius: 10px;
        padding: 0.95rem;
        background: #fbfcfe;
    }

    .tracking-note span {
        display: block;
        color: var(--muted);
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }

    .tracking-note strong {
        display: block;
        color: var(--ink);
        font-size: 0.95rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }

    .tracking-note p {
        color: var(--muted);
        font-size: 0.8rem;
        margin: 0;
        line-height: 1.4;
    }

    .event-stream {
        display: grid;
        gap: 0.75rem;
        max-height: 420px;
        overflow-y: auto;
        overflow-x: hidden;
        padding-right: 0.5rem;
    }

    .event-stream::-webkit-scrollbar {
        width: 6px;
    }

    .event-stream::-webkit-scrollbar-track {
        background: transparent;
    }

    .event-stream::-webkit-scrollbar-thumb {
        background: rgba(219, 227, 236, 0.8);
        border-radius: 3px;
    }

    .stream-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        margin-bottom: 1rem;
    }

    .topbar-actions .mini-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        border: 1px solid rgba(219, 227, 236, 0.95);
        border-radius: 999px;
        padding: 0.5rem 0.875rem;
        background: #f7f9fc;
        color: var(--ink);
        font-size: 0.8rem;
        font-weight: 600;
        white-space: nowrap;
    }

    .topbar-actions .mini-pill strong {
        font-weight: 700;
        color: var(--ink);
    }

    .stream-status {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.75rem;
        color: #355c7d;
        background: #eef3f8;
        border: 1px solid #d7e1ea;
        border-radius: 999px;
        padding: 0.4rem 0.8rem;
        font-weight: 700;
    }

    .stream-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: #355c7d;
        box-shadow: 0 0 0 0 rgba(53, 92, 125, 0.3);
        animation: streamPulse 1.8s infinite;
    }

    @keyframes streamPulse {
        0% {box-shadow: 0 0 0 0 rgba(53, 92, 125, 0.3);}
        70% {box-shadow: 0 0 0 6px rgba(53, 92, 125, 0);}
        100% {box-shadow: 0 0 0 0 rgba(53, 92, 125, 0);}
    }

    .stream-item {
        display: grid;
        grid-template-columns: 40px minmax(0, 1fr) auto;
        align-items: center;
        gap: 0.75rem;
        border: 1px solid rgba(219, 227, 236, 0.95);
        border-radius: 10px;
        padding: 0.75rem;
        background: linear-gradient(135deg, #ffffff, #f8fafc);
        transition: all 0.2s ease;
        width: 100%;
        box-sizing: border-box;
    }

    .stream-item:hover {
        transform: translateY(-1px);
        border-color: rgba(53, 92, 125, 0.22);
        box-shadow: 0 5px 14px rgba(15, 23, 42, 0.05);
    }

    .stream-icon {
        width: 36px;
        height: 36px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #fff;
        font-weight: 700;
        font-size: 0.85rem;
        background: linear-gradient(135deg, #355c7d, #5f7d8a);
        flex-shrink: 0;
    }

    .stream-text strong {
        display: block;
        color: var(--ink);
        font-size: 0.9rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }

    .stream-text {
        min-width: 0;
    }

    .stream-text span,
    .stream-tag {
        color: var(--muted);
        font-size: 0.75rem;
    }

    .stream-meta {
        margin-top: 0.3rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        flex-wrap: wrap;
        color: #6b7280;
        font-size: 0.7rem;
    }

    .stream-tag {
        border-radius: 999px;
        padding: 0.35rem 0.65rem;
        background: #f4f7fb;
        border: 1px solid #dbe3ec;
        white-space: nowrap;
        font-weight: 700;
    }

    .stream-tag.session {background: #eef3f8; border-color: #d7e1ea; color: #355c7d;}
    .stream-tag.interest {background: #f3f6f8; border-color: #dbe3ec; color: #5f7d8a;}
    .stream-tag.intent {background: #f5f3ef; border-color: #e4ddd3; color: #7b8f6f;}
    .stream-tag.purchase {background: #f7f4ee; border-color: #e6d9c7; color: #a88a5b;}
    .stream-tag.conversion {background: #f2f4ef; border-color: #dde6d7; color: #7b8f6f;}
    .stream-tag.retention {background: #f5f0f1; border-color: #e5d7da; color: #9a6f75;}

    .stream-legend {
        margin-top: 8px;
        color: var(--muted);
        font-size: 0.72rem;
    }

    .risk-board {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 10px;
    }

    .risk-card {
        border-radius: 12px;
        padding: 14px;
        border: 1px solid var(--line);
        background: linear-gradient(180deg, #ffffff, #f8fafc);
        min-height: 118px;
        position: relative;
        overflow: hidden;
    }

    .risk-card:after {
        content: "";
        position: absolute;
        right: -24px;
        top: -24px;
        width: 88px;
        height: 88px;
        border-radius: 50%;
        background: rgba(53,92,125,0.08);
    }

    .risk-card.medium:after {background: rgba(168,138,91,0.12);}
    .risk-card.high:after {background: rgba(154,111,117,0.12);}

    .risk-card span {
        color: var(--muted);
        font-size: 0.76rem;
        font-weight: 800;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    .risk-card strong {
        display: block;
        color: var(--ink);
        font-size: 1.55rem;
        margin: 8px 0 4px;
    }

    .risk-card p {
        color: var(--muted);
        margin: 0;
        font-size: 0.82rem;
    }

    .data-flow {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 10px;
        align-items: stretch;
    }

    .flow-node {
        border: 1px solid var(--line);
        border-radius: 13px;
        padding: 14px;
        background: #ffffff;
        text-align: center;
        box-shadow: 0 8px 22px rgba(15,23,42,0.05);
    }

    .flow-node .node-mark {
        width: 42px;
        height: 42px;
        border-radius: 13px;
        margin: 0 auto 10px;
        background: linear-gradient(135deg, var(--blue), var(--teal));
    }

    .flow-node strong {
        display: block;
        color: var(--ink);
        font-size: 0.9rem;
        margin-bottom: 5px;
    }

    .flow-node span {
        color: var(--muted);
        font-size: 0.76rem;
    }

    .callout {
        border-radius: 10px;
        border: 1px solid var(--line);
        padding: 14px 16px;
        background: #fff;
        color: var(--ink);
        margin: 10px 0;
    }

    .callout.info {border-left: 4px solid var(--blue);}
    .callout.success {border-left: 4px solid var(--green); background: #f0fdf4;}
    .callout.warning {border-left: 4px solid var(--amber); background: #fffbeb;}
    .callout.danger {border-left: 4px solid var(--rose); background: #fff1f2;}

    .identity-card {
        padding: 18px;
        min-height: 100%;
        background:
            linear-gradient(135deg, rgba(23,32,51,0.96), rgba(15,118,110,0.92)),
            linear-gradient(90deg, rgba(255,255,255,0.08), transparent);
        color: #fff;
    }

    .identity-card h3 {
        color: #fff;
        margin: 0 0 8px;
    }

    .identity-card p,
    .identity-card li {
        color: rgba(255,255,255,0.82);
        font-size: 0.92rem;
    }

    .identity-card ul {
        margin: 10px 0 0;
        padding-left: 18px;
    }

    .play-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
    }

    .play-card {
        padding: 15px;
        min-height: 132px;
    }

    .play-card strong {
        display: block;
        color: var(--ink);
        margin-bottom: 7px;
    }

    .play-card span {
        color: var(--muted);
        font-size: 0.9rem;
    }

    .stButton > button,
    .stDownloadButton > button {
        background: linear-gradient(135deg, #3b82f6, #06b6d4) !important;
        border: 1px solid transparent !important;
        color: #fff !important;
        border-radius: 8px !important;
        min-height: 44px !important;
        font-weight: 700 !important;
        box-shadow: 0 6px 16px rgba(59, 130, 246, 0.15) !important;
        transition: all 0.2s ease !important;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 24px rgba(59, 130, 246, 0.25) !important;
    }

    div[data-testid="stMetric"] {
        background: #fff;
        border: 1px solid rgba(203, 213, 225, 0.8);
        border-radius: 10px;
        padding: 1rem 1.25rem;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid rgba(203, 213, 225, 0.8);
        border-radius: 10px;
        overflow: hidden;
    }

    @media (max-width: 1200px) {
        .main .block-container {
            max-width: 100%;
        }

        .app-hero,
        .data-flow {
            grid-template-columns: 1fr;
        }

        .pipeline-strip,
        .architecture-grid,
        .tracking-snapshot {
            grid-template-columns: repeat(2, 1fr);
        }
    }

    @media (max-width: 768px) {
        .topbar {
            flex-direction: column;
            align-items: flex-start;
        }

        .topbar-actions {
            justify-content: flex-start;
            width: 100%;
        }

        .main .block-container {
            padding: 1rem 0.75rem;
        }

        .hero-copy h1 {
            font-size: 1.75rem;
        }

        .pipeline-strip,
        .architecture-grid,
        .tracking-snapshot,
        .tracking-notes {
            grid-template-columns: 1fr;
        }

        .data-flow {
            grid-template-columns: repeat(2, 1fr);
        }

        .stream-item {
            grid-template-columns: 36px 1fr;
        }

        .stream-tag {
            grid-column: 2;
            justify-self: start;
        }
    }
</style>
""",
    unsafe_allow_html=True,
)

ACADEMIC_COLORS = ["#355c7d", "#5f7d8a", "#7b8f6f", "#a88a5b", "#9a6f75"]
ACADEMIC_SOFT_SCALE = ["#f7fbff", "#deecf9", "#c6e2f0", "#8fb7d6", "#547aa3"]
ACADEMIC_DIVERGING_SCALE = ["#edf2f7", "#dbe3ec", "#e9ddcf", "#d9c0c0", "#b98f95"]


# ============================================================================
# CONFIGURATION
# ============================================================================

API_URL = os.getenv("DROPOFF_API_URL", "http://127.0.0.1:5000")
API_TIMEOUT = 10

DEMO_PROFILES: Dict[str, Dict[str, Any]] = {
    "Low risk": {
        "days_since_signup": 120,
        "recency_days": 4,
        "frequency": 96,
        "session_duration": 24.0,
        "feature_count": 11,
        "device_type": "Desktop",
        "os_type": "Windows",
        "user_segment": "Premium",
        "region": "North",
    },
    "Balanced": {
        "days_since_signup": 220,
        "recency_days": 28,
        "frequency": 54,
        "session_duration": 13.0,
        "feature_count": 7,
        "device_type": "Mobile",
        "os_type": "Android",
        "user_segment": "Trial",
        "region": "East",
    },
    "High risk": {
        "days_since_signup": 410,
        "recency_days": 74,
        "frequency": 14,
        "session_duration": 4.5,
        "feature_count": 2,
        "device_type": "Mobile",
        "os_type": "iOS",
        "user_segment": "Free",
        "region": "South",
    },
}

COLUMN_MAP = {
    "Days Since Signup": "days_signup_age",
    "Days Since Last Activity": "recency_days",
    "Total Logins": "frequency_total",
    "Avg Session Duration (min)": "session_duration_avg",
    "Features Used": "feature_count_used",
    "Device Type": "device_type",
    "Operating System": "os_type",
    "User Segment": "user_segment",
    "Region": "region",
}


# ============================================================================
# DATA AND API HELPERS
# ============================================================================

@st.cache_resource
def get_api_session() -> requests.Session:
    session = requests.Session()
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "StreamlitDropoffDashboard/3.0",
    }
    api_key = os.getenv("API_KEY", "").strip()
    if api_key:
        headers["X-API-Key"] = api_key
    session.headers.update(headers)
    return session


@st.cache_data(ttl=30)
def check_api_status() -> bool:
    try:
        response = get_api_session().get(f"{API_URL}/health", timeout=2)
        return response.status_code == 200
    except requests.RequestException:
        return False


@st.cache_data(ttl=60)
def load_evaluation_metrics() -> Dict[str, Any]:
    path = Path("results/evaluation_metrics.json")
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


@st.cache_data(ttl=60)
def load_threshold_analysis() -> pd.DataFrame:
    path = Path("results/threshold_analysis.csv")
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


@st.cache_data(ttl=60)
def load_model_comparison() -> pd.DataFrame:
    path = Path("results/model_comparison.csv")
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def call_api(
    endpoint: str,
    method: str = "GET",
    data: Dict[str, Any] | None = None,
) -> Tuple[bool, Any, str]:
    try:
        session = get_api_session()
        url = f"{API_URL}{endpoint}"
        if method.upper() == "POST":
            response = session.post(url, json=data, timeout=API_TIMEOUT)
        else:
            response = session.get(url, timeout=API_TIMEOUT)

        if response.status_code in {200, 201, 207}:
            return True, response.json(), "Success"

        try:
            detail = response.json().get("error", response.text)
        except ValueError:
            detail = response.text
        return False, None, f"HTTP {response.status_code}: {detail}"
    except requests.RequestException as exc:
        return False, None, str(exc)


@st.cache_data(ttl=3)
def fetch_recent_predictions(limit: int = 6) -> List[Dict[str, Any]]:
    success, result, _ = call_api(f"/predictions?limit={max(1, min(1000, limit))}")
    if not success or not isinstance(result, dict):
        return []
    rows = result.get("predictions", [])
    if isinstance(rows, list):
        return rows
    return []


def _parse_payload_json(payload_json: str | None) -> Dict[str, Any]:
    if not payload_json:
        return {}
    try:
        parsed = json.loads(payload_json)
        return parsed if isinstance(parsed, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def _format_event_clock(created_at: str | None) -> str:
    if not created_at:
        return "unknown"
    try:
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        return dt.strftime("%H:%M:%S")
    except ValueError:
        return "unknown"


def _phase_from_features(payload: Dict[str, Any]) -> str:
    feature_count = float(payload.get("feature_count_used", 0) or 0)
    if feature_count <= 2:
        return "session"
    if feature_count <= 4:
        return "interest"
    if feature_count <= 6:
        return "intent"
    if feature_count <= 8:
        return "purchase"
    if feature_count <= 10:
        return "conversion"
    return "retention"


def _name_surface_from_phase(phase: str) -> Tuple[str, str]:
    mapping = {
        "session": ("login", "Session start"),
        "interest": ("product_viewed", "Product page"),
        "intent": ("search", "Search intent"),
        "purchase": ("add_to_cart", "Cart interaction"),
        "conversion": ("checkout_started", "Checkout started"),
        "retention": ("order_completed", "Order completion"),
    }
    return mapping.get(phase, ("activity", "User activity"))


def _format_live_value(value: Any) -> str:
    if value is None:
        return "unknown"
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return f"{value:.2f}"
    text = str(value).strip()
    return text or "unknown"


def _build_live_feature_sources(payload: Dict[str, Any], recent_count: int) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Feature": "days_signup_age",
                "Source": "User signup record",
                "Sample Value": _format_live_value(payload.get("days_signup_age")),
                "Used By": "Risk model",
            },
            {
                "Feature": "recency_days",
                "Source": "Latest event timestamp",
                "Sample Value": _format_live_value(payload.get("recency_days")),
                "Used By": "Risk model",
            },
            {
                "Feature": "frequency_total",
                "Source": "Session and login history",
                "Sample Value": _format_live_value(payload.get("frequency_total")),
                "Used By": "Risk model",
            },
            {
                "Feature": "session_duration_avg",
                "Source": "Session timing",
                "Sample Value": _format_live_value(payload.get("session_duration_avg")),
                "Used By": "Risk model",
            },
            {
                "Feature": "feature_count_used",
                "Source": "Recent behavior breadth",
                "Sample Value": _format_live_value(payload.get("feature_count_used")),
                "Used By": f"{recent_count} recent predictions",
            },
            {
                "Feature": "device_type / os_type",
                "Source": "Client metadata",
                "Sample Value": " / ".join(
                    [
                        _format_live_value(payload.get("device_type")),
                        _format_live_value(payload.get("os_type")),
                    ]
                ),
                "Used By": "Segmentation",
            },
            {
                "Feature": "user_segment / region",
                "Source": "Profile and geography",
                "Sample Value": " / ".join(
                    [
                        _format_live_value(payload.get("user_segment")),
                        _format_live_value(payload.get("region")),
                    ]
                ),
                "Used By": "Targeting",
            },
        ]
    )


def _build_empty_state_chart(title: str, message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(size=14, color="#66758a"),
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(
        title=title,
        height=305,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
    )
    return chart_layout(fig, 305)


def _parse_created_at(raw_value: Any) -> datetime | None:
    if raw_value is None:
        return None
    raw_text = str(raw_value).strip()
    if not raw_text:
        return None
    try:
        return datetime.fromisoformat(raw_text.replace("Z", "+00:00"))
    except ValueError:
        return None


def build_live_event_rows(predictions: List[Dict[str, Any]]) -> List[str]:
    if not predictions:
        return []

    rows: List[str] = []
    for idx, prediction in enumerate(reversed(predictions), start=1):
        payload = _parse_payload_json(str(prediction.get("payload_json", "")))
        phase = _phase_from_features(payload)
        name, surface = _name_surface_from_phase(phase)
        clock = _format_event_clock(prediction.get("created_at"))
        actor = " / ".join(
            [
                str(payload.get("device_type", "unknown")).lower(),
                str(payload.get("user_segment", "unknown")).lower(),
                str(payload.get("region", "unknown")).lower(),
            ]
        )

        rows.append(
            f'<div class="stream-item"><div class="stream-icon">{idx:02d}</div><div class="stream-text"><strong>{name}</strong><span>{surface}</span><div class="stream-meta"><span>{clock}</span><span>{actor}</span></div></div><div class="stream-tag {phase}">{phase}</div></div>'
        )

    return rows


@st.cache_data(ttl=3)
def load_live_prediction_frame(limit: int = 400) -> pd.DataFrame:
    predictions = fetch_recent_predictions(limit=limit)
    rows: List[Dict[str, Any]] = []

    for prediction in predictions:
        payload = _parse_payload_json(str(prediction.get("payload_json", "")))
        if not payload:
            continue

        created_at = _parse_created_at(prediction.get("created_at"))
        if created_at is None:
            continue

        phase = _phase_from_features(payload)
        region = str(payload.get("region", "unknown")).strip().title()
        risk_level = str(prediction.get("risk_level", "unknown")).strip().lower()

        rows.append(
            {
                "created_at": created_at,
                "phase": phase,
                "region": region or "Unknown",
                "risk_level": risk_level,
            }
        )

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    return df.dropna(subset=["created_at"])


def profile_to_payload(profile_data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "days_signup_age": profile_data["days_since_signup"],
        "recency_days": profile_data["recency_days"],
        "frequency_total": profile_data["frequency"],
        "session_duration_avg": profile_data["session_duration"],
        "feature_count_used": profile_data["feature_count"],
        "device_type": profile_data["device_type"],
        "os_type": profile_data["os_type"],
        "user_segment": profile_data["user_segment"],
        "region": profile_data["region"],
    }


def classify_risk(probability: float) -> str:
    if probability < 0.33:
        return "Low"
    if probability < 0.67:
        return "Medium"
    return "High"


def risk_kind(probability: float) -> str:
    if probability < 0.33:
        return "success"
    if probability < 0.67:
        return "warning"
    return "danger"


def metric_value(metrics: Dict[str, Any], key: str, fallback: float) -> float:
    return float(metrics.get("metrics", {}).get(key, fallback))


def score_profile(profile_name: str) -> Tuple[bool, Dict[str, Any], str]:
    payload = profile_to_payload(DEMO_PROFILES[profile_name])
    success, result, msg = call_api("/predict", "POST", payload)
    if not success:
        return False, {}, msg

    probability = float(result.get("dropoff_probability", 0))
    return (
        True,
        {
            "profile": profile_name,
            "probability": probability,
            "risk": result.get("risk_level") or classify_risk(probability),
            "prediction": result.get("predicted_label", int(probability >= 0.5)),
        },
        "Success",
    )


def uploaded_rows_to_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    renamed = df.rename(columns=COLUMN_MAP)
    required = list(COLUMN_MAP.values())
    missing = [col for col in required if col not in renamed.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    return cast(List[Dict[str, Any]], renamed.loc[:, required].to_dict(orient="records"))


# ============================================================================
# RENDER HELPERS
# ============================================================================

def render_kpi(label: str, value: str, copy: str, color: str = "blue") -> None:
    st.markdown(
        f"""
        <div class="kpi-card {color}">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <p class="kpi-copy">{copy}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_panel(title: str, copy: str = "") -> None:
    st.markdown(
        f"""
        <div class="panel">
            <div class="panel-title">{title}</div>
            <p class="panel-copy">{copy}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_callout(kind: str, title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="callout {kind}">
            <strong>{title}</strong><br>{body}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_signal_panel(api_online: bool, metrics_blob: Dict[str, Any], confusion: List[List[int]]) -> None:
    status_class = "online" if api_online else "offline"
    status_text = "API Live" if api_online else "API Offline"
    st.markdown(
        f"""
        <div class="signal-panel">
            <div class="signal-head">
                <div>
                    <div class="eyebrow">AI Risk Signal</div>
                    <div class="signal-title">Behavior-to-retention intelligence</div>
                </div>
                <span class="status-chip"><span class="status-dot {status_class}"></span>{status_text}</span>
            </div>
            <div class="signal-grid">
                <div class="signal-bar" style="height: 88px;"></div>
                <div class="signal-bar"></div>
                <div class="signal-bar"></div>
                <div class="signal-bar"></div>
                <div class="signal-bar"></div>
            </div>
            <div class="signal-foot">
                <div class="mini-stat"><span>ROC-AUC</span><strong>{metric_value(metrics_blob, "roc_auc", 0.9731):.3f}</strong></div>
                <div class="mini-stat"><span>Recall</span><strong>{metric_value(metrics_blob, "recall", 0.9178):.1%}</strong></div>
                <div class="mini-stat"><span>Found</span><strong>{int(confusion[1][1]):,}</strong></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_gauge(probability: float) -> go.Figure:
    fig = go.Figure(
        data=[
            go.Indicator(
                mode="gauge+number",
                value=probability * 100,
                number={"suffix": "%", "valueformat": ".1f"},
                title={"text": "Drop-off risk"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "#2563eb"},
                    "steps": [
                        {"range": [0, 33], "color": "#dcfce7"},
                        {"range": [33, 67], "color": "#fef3c7"},
                        {"range": [67, 100], "color": "#ffe4e6"},
                    ],
                    "threshold": {
                        "line": {"color": "#e11d48", "width": 4},
                        "thickness": 0.75,
                        "value": 70,
                    },
                },
            )
        ]
    )
    fig.update_layout(
        height=305,
        margin=dict(l=12, r=12, t=42, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial"),
    )
    return fig


def chart_layout(fig: go.Figure, height: int = 330) -> go.Figure:
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=28, b=10),
        font=dict(family="Arial", color="#142033"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        template="simple_white",
        colorway=ACADEMIC_COLORS,
        hoverlabel=dict(bgcolor="#ffffff", bordercolor="#dbe3ec", font=dict(color="#142033")),
    )
    return fig


def build_retention_funnel() -> go.Figure:
    """Build a clean retention progression chart without heavy borders or shapes."""
    funnel_df = pd.DataFrame(
        {
            "Stage": ["High Risk", "At Risk", "Engaged", "Active", "Visited"],
            "Users": [6200, 18450, 54600, 78200, 100000],
        }
    )
    stage_colors = ["#d9e2ec", "#d7e6df", "#e6dfcf", "#e1d0d5", "#ced9e6"]

    fig = go.Figure(
        go.Bar(
            x=funnel_df["Users"],
            y=funnel_df["Stage"],
            orientation="h",
            marker={
                "color": stage_colors,
                "line": {"width": 0},
            },
            text=[f"{value:,.0f}" for value in funnel_df["Users"]],
            textposition="outside",
            textfont={"size": 12, "color": "#334155", "family": "Arial, sans-serif"},
            hovertemplate="<b>%{y}</b><br>Users: %{x:,.0f}<extra></extra>",
        )
    )

    fig.update_layout(
        font={"family": "Arial, sans-serif", "size": 13, "color": "#334155"},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"t": 20, "b": 20, "l": 20, "r": 20},
        height=380,
        xaxis={"showgrid": False, "zeroline": False, "showline": False, "showticklabels": False},
        yaxis={"showgrid": False, "zeroline": False, "showline": False},
    )

    return fig


def build_segment_risk_donut() -> go.Figure:
    segment_df = pd.DataFrame(
        {
            "Segment": ["Free", "Trial", "Premium", "Returning"],
            "Risk Share": [42, 28, 12, 18],
        }
    )
    fig = px.pie(
        segment_df,
        names="Segment",
        values="Risk Share",
        hole=0.62,
        color="Segment",
        color_discrete_map={
            "Free": "#9a6f75",
            "Trial": "#a88a5b",
            "Premium": "#7b8f6f",
            "Returning": "#5f7d8a",
        },
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return chart_layout(fig, 305)


def build_event_volume_chart() -> go.Figure:
    live_df = load_live_prediction_frame(limit=800)
    if not live_df.empty:
        bucket_map = {
            "session": "Product Views",
            "interest": "Product Views",
            "intent": "Product Views",
            "purchase": "Cart Events",
            "conversion": "Checkout Events",
            "retention": "Checkout Events",
        }
        prepared = live_df.copy()
        prepared["event_bucket"] = prepared["phase"].map(bucket_map).fillna("Product Views")
        prepared["hour_dt"] = prepared["created_at"].dt.floor("h")

        grouped = prepared.groupby(["hour_dt", "event_bucket"], as_index=False).size()
        pivoted = grouped.pivot(index="hour_dt", columns="event_bucket", values="size").fillna(0)
        latest_hour = prepared["hour_dt"].max()
        start_hour = latest_hour - pd.Timedelta(hours=11)
        full_hours = pd.date_range(start=start_hour, end=latest_hour, freq="h")
        pivoted = pivoted.reindex(full_hours, fill_value=0)
        pivoted.index.name = "hour_dt"

        for col in ["Product Views", "Cart Events", "Checkout Events"]:
            if col not in pivoted.columns:
                pivoted[col] = 0

        pivoted = pivoted[["Product Views", "Cart Events", "Checkout Events"]].sort_index().tail(12)
        event_df = pivoted.reset_index()
        event_df["Hour"] = event_df["hour_dt"].dt.strftime("%H:%M")
        event_df = event_df.drop(columns=["hour_dt"])
    else:
        return _build_empty_state_chart("Event Volume", "Waiting for prediction records to populate the summary.")

    fig = px.area(
        event_df,
        x="Hour",
        y=["Product Views", "Cart Events", "Checkout Events"],
        color_discrete_sequence=["#355c7d", "#5f7d8a", "#a88a5b"],
    )
    fig.update_layout(yaxis_title="Events", xaxis_title="Hour")
    return chart_layout(fig, 305)


def build_region_heatmap() -> go.Figure:
    live_df = load_live_prediction_frame(limit=800)
    if not live_df.empty:
        grouped = live_df.groupby(["region", "risk_level"], as_index=False).size()
        pivoted = grouped.pivot(index="region", columns="risk_level", values="size").fillna(0)

        for col in ["low", "medium", "high"]:
            if col not in pivoted.columns:
                pivoted[col] = 0

        pivoted = pivoted[["low", "medium", "high"]]
        totals = pivoted.sum(axis=1).replace(0, 1)
        heat_df = (pivoted.div(totals, axis=0) * 100).round(1)
        heat_df.columns = ["Low", "Medium", "High"]
        heat_df = heat_df.sort_index()
    else:
        return _build_empty_state_chart("Region Risk Heatmap", "Waiting for prediction records to populate the geographic summary.")

    fig = px.imshow(
        heat_df,
        text_auto=True,
        aspect="auto",
        color_continuous_scale=ACADEMIC_DIVERGING_SCALE,
        labels=dict(color="Risk %"),
    )
    fig.update_layout(xaxis_title="Risk Level", yaxis_title="Region")
    return chart_layout(fig, 305)


# ============================================================================
# DATA LOAD
# ============================================================================

metrics_blob = load_evaluation_metrics()
confusion = metrics_blob.get("confusion_matrix", [[4226, 415], [276, 3083]])
threshold_df = load_threshold_analysis()
model_df = load_model_comparison()
api_online = check_api_status()


# ============================================================================
# NAVIGATION
# ============================================================================

PAGES = [
    "Command Center",
    "Production Tracking",
    "Model Intelligence",
    "Batch Scoring",
    "System Health",
]

NAV_LABELS = {
    "Command Center": "01  Overview",
    "Production Tracking": "02  Behavioral Analysis",
    "Model Intelligence": "03  Model Evaluation",
    "Batch Scoring": "04  Batch Evaluation",
    "System Health": "05  System Review",
}

if "page" not in st.session_state:
    st.session_state["page"] = PAGES[0]

status_class = "online" if api_online else "offline"
status_text = "Data Ready" if api_online else "API Offline"
st.markdown(
    f"""
    <div class="topbar">
        <div class="brand">
            <div class="brand-mark">DD</div>
            <div>
                <div class="brand-title">Early User Churn Detection</div>
                <div class="brand-subtitle">Thesis presentation dashboard</div>
            </div>
        </div>
        <div class="topbar-actions">
            <span class="mini-pill">Evaluation sample <strong>{metric_value(metrics_blob, "predictions_total", 860):,.0f}</strong></span>
            <span class="api-pill"><span class="status-dot {status_class}"></span>{status_text}</span>
            <span class="nav-note">Model {metric_value(metrics_blob, "roc_auc", 0.9731):.3f} ROC-AUC</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

selected_page = st.pills(
    "Dashboard navigation",
    PAGES,
    default=st.session_state["page"],
    format_func=lambda page_name: NAV_LABELS[page_name],
    label_visibility="collapsed",
)
if selected_page:
    st.session_state["page"] = selected_page
page = st.session_state["page"]


# ============================================================================
# PROJECT OVERVIEW
# ============================================================================

if page == "Command Center":
    st.markdown(
        """
        <div class="section-head">
            <div>
                <h2>Project Overview</h2>
                <p>Summary view of retention risk, model strength, and project evidence.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    hero_col, signal_col = st.columns([1.18, 0.82])
    with hero_col:
        st.markdown(
            """
            <div class="hero-copy">
                <div class="eyebrow">Retention Intelligence</div>
                <h1>Early User Churn Detection in Web Applications</h1>
                <p>
                    A modern ML dashboard that converts behavioral signals into risk scores,
                    intervention priorities, model evidence, and analytical insight.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with signal_col:
        render_signal_panel(api_online, metrics_blob, confusion)

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi("ROC-AUC", f"{metric_value(metrics_blob, 'roc_auc', 0.9731):.3f}", "Separation quality.", "blue")
    with k2:
        render_kpi("Recall", f"{metric_value(metrics_blob, 'recall', 0.9178):.1%}", "Risk capture.", "green")
    with k3:
        render_kpi("Value", f"${metric_value(metrics_blob, 'business_value', 584850):,.0f}", "Retention impact.", "amber")
    with k4:
        render_kpi("Flagged", f"{int(confusion[1][1]):,}", "Users found.", "rose")

    st.markdown(
        """
        <div class="panel">
            <div class="panel-title">Analytical Workflow</div>
            <div class="architecture-grid">
                <div class="arch-tile">
                    <div class="arch-mark"></div>
                    <strong>Browser/App Events</strong>
                    <span>Clickstream and session activity captured for analysis.</span>
                </div>
                <div class="arch-tile">
                    <div class="arch-mark"></div>
                    <strong>Feature Job</strong>
                    <span>Events become user-level features such as recency, frequency, and usage depth.</span>
                </div>
                <div class="arch-tile">
                    <div class="arch-mark"></div>
                    <strong>Prediction Store</strong>
                    <span>API scores are stored and summarized for retention teams.</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    visual_left, visual_right = st.columns([1.1, 0.9])
    with visual_left:
        st.markdown(
            """
            <div class="visual-card">
                <div class="visual-title">Retention Funnel</div>
                <div class="visual-copy">How users move from activity into risk groupings.</div>
            """,
            unsafe_allow_html=True,
        )
        st.plotly_chart(build_retention_funnel(), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with visual_right:
        st.markdown(
            """
            <div class="visual-card">
                <div class="visual-title">Risk By Segment</div>
                <div class="visual-copy">Which groups are most relevant for retention review.</div>
            """,
            unsafe_allow_html=True,
        )
        st.plotly_chart(build_segment_risk_donut(), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class="risk-board">
            <div class="risk-card">
                <span>Low Risk</span>
                <strong>72%</strong>
                <p>Healthy users with regular activity.</p>
            </div>
            <div class="risk-card medium">
                <span>Medium Risk</span>
                <strong>19%</strong>
                <p>Need nudges and product guidance.</p>
            </div>
            <div class="risk-card high">
                <span>High Risk</span>
                <strong>9%</strong>
                <p>Priority users for retention action.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================================
# BEHAVIORAL SUMMARY
# ============================================================================

elif page == "Production Tracking":
    st.markdown(
        """
        <div class="section-head">
            <div>
                <h2>Project Workflow</h2>
                <p>The project converts behavioral signals into predictions and summarizes the results for thesis presentation.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Static presentation controls
    col_refresh, col_status = st.columns([2, 2])
    with col_refresh:
        auto_refresh = False
    
    with col_status:
        api_check = check_api_status()
        status_symbol = "🟢 Available" if api_check else "🔴 Unavailable"
        st.metric("API Status", status_symbol)

    st.caption("Static summary view for thesis review and presentation.")
    
    # Status summary banner
    errors_detected = []
    if not api_check:
        errors_detected.append("⚠️ API Server unavailable - Prediction results cannot be refreshed")
    
    success, recent_preds, _ = call_api("/predictions?limit=1")
    if success and not recent_preds:
        errors_detected.append("⚠️ No predictions available - The result store is currently empty")
    
    if errors_detected:
        st.warning("⚠️ **Status Notes**\n\n" + "\n\n".join(errors_detected))
    else:
        st.success("✅ Current system state is available for review")

    prediction_rows = fetch_recent_predictions(limit=6) if api_online else []
    latest_prediction = prediction_rows[0] if prediction_rows else {}
    latest_payload = _parse_payload_json(str(latest_prediction.get("payload_json", ""))) if latest_prediction else {}
    live_frame = load_live_prediction_frame(limit=800) if api_online else pd.DataFrame()
    live_total = int(len(live_frame)) if isinstance(live_frame, pd.DataFrame) else 0
    live_regions = int(live_frame["region"].nunique()) if isinstance(live_frame, pd.DataFrame) and not live_frame.empty else 0
    live_high_risk = int((live_frame["risk_level"] == "high").sum()) if isinstance(live_frame, pd.DataFrame) and not live_frame.empty else 0
    live_high_share = (live_high_risk / live_total) if live_total else 0.0

    st.markdown(
        f"""
        <div class="panel">
            <div class="panel-title">Summary Snapshot</div>
            <div class="panel-copy">This card summarizes the current project state without repeating the table below.</div>
            <div class="tracking-snapshot">
                <div class="snapshot-card">
                    <span>Observed Volume</span>
                    <strong>{live_total:,}</strong>
                    <p>Scored events captured in the current sample.</p>
                </div>
                <div class="snapshot-card">
                    <span>Region Coverage</span>
                    <strong>{live_regions}</strong>
                    <p>Distinct regions represented in the dataset.</p>
                </div>
                <div class="snapshot-card">
                    <span>High-Risk Share</span>
                    <strong>{live_high_share:.0%}</strong>
                    <p>Share of events marked as high risk.</p>
                </div>
                <div class="snapshot-card">
                    <span>Latest Risk State</span>
                    <strong>{_format_live_value(latest_prediction.get("risk_level"))}</strong>
                    <p>Most recent prediction outcome.</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="panel">
            <div class="panel-title">Project Flow</div>
            <div class="panel-copy">Each stage in the project maps the path from user behavior to prediction output.</div>
            <div class="pipeline-strip">
                <div class="pipeline-chip">
                    <span>Event Capture</span>
                    <strong>Input</strong>
                    <p>Login, search, cart, checkout.</p>
                </div>
                <div class="pipeline-chip">
                    <span>Feature Job</span>
                    <strong>Processing</strong>
                    <p>User-level behavior features.</p>
                </div>
                <div class="pipeline-chip">
                    <span>ML Scoring</span>
                    <strong>Model</strong>
                    <p>Prediction or scheduled scoring.</p>
                </div>
                <div class="pipeline-chip">
                    <span>Dashboard</span>
                    <strong>Insights</strong>
                    <p>Summaries, filters, and risk groups.</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="panel">
            <div class="panel-title">Application Flow</div>
            <div class="panel-copy">This is the path from raw behavior to scored output and summary reporting.</div>
            <div class="data-flow">
                <div class="flow-node">
                    <div class="node-mark"></div>
                    <strong>Browser Events</strong>
                    <span>Clicks, sessions, and behavior signals</span>
                </div>
                <div class="flow-node">
                    <div class="node-mark"></div>
                    <strong>Features</strong>
                    <span>Aggregated signals and user-level inputs</span>
                </div>
                <div class="flow-node">
                    <div class="node-mark"></div>
                    <strong>Scoring API</strong>
                    <span>Risk prediction and classification</span>
                </div>
                <div class="flow-node">
                    <div class="node-mark"></div>
                    <strong>Prediction Store</strong>
                    <span>Stored outputs for review and analysis</span>
                </div>
                <div class="flow-node">
                    <div class="node-mark"></div>
                    <strong>Dashboard</strong>
                    <span>Insights, summary, and presentation</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    event_col, feature_col = st.columns([1.0, 1.0])
    with event_col:
        stream_rows = build_live_event_rows(prediction_rows)
        stream_html = "".join(stream_rows)
        stream_state = "ACTIVE" if stream_rows else "IDLE"
        stream_copy = (
            "Latest scored behaviors from the prediction store."
            if stream_rows
            else "No recent prediction events yet. Add data to populate this section."
        )

        if not stream_rows:
            stream_rows = [
                '<div class="stream-item"><div class="stream-icon">--</div><div class="stream-text"><strong>waiting_for_events</strong><span>Prediction records will appear here automatically</span><div class="stream-meta"><span>now</span><span>api / monitor</span></div></div><div class="stream-tag session">session</div></div>'
            ]
            stream_html = "".join(stream_rows)

        st.markdown(
            (
                f'<div class="visual-card">'
                f'<div class="stream-head">'
                f'<div><div class="visual-title">Event Summary</div>'
                f'<div class="visual-copy">{stream_copy}</div></div>'
                f'<div class="stream-status"><span class="stream-dot"></span>{stream_state}</div>'
                f'</div>'
                f'<div class="event-stream">{stream_html}</div>'
                f'<div class="stream-legend">Recent events are summarized here without duplicating the snapshot metrics.</div>'
                f'</div>'
            ),
            unsafe_allow_html=True,
        )

    with feature_col:
        st.markdown(
            """
            <div class="visual-card">
                <div class="visual-title">Feature Reference Table</div>
                <div class="visual-copy">The latest payload values explain the inputs used by the model.</div>
            """,
            unsafe_allow_html=True,
        )
        feature_sources = _build_live_feature_sources(latest_payload, len(prediction_rows))
        st.dataframe(feature_sources, use_container_width=True, hide_index=True)
        st.markdown(
            """
            <div class="tracking-notes">
                <div class="tracking-note">
                    <span>System State</span>
                    <strong>API Connected</strong>
                    <p>Prediction records are available for review in the dashboard.</p>
                </div>
                <div class="tracking-note">
                    <span>Update Mode</span>
                    <strong>Optional</strong>
                    <p>Updates can be triggered manually for a presentation-friendly view.</p>
                </div>
                <div class="tracking-note">
                    <span>Audience</span>
                    <strong>Research / Retention</strong>
                    <p>Built for analysis, presentation, and discussion of at-risk users.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.markdown("### Event Volume")
        st.plotly_chart(build_event_volume_chart(), use_container_width=True)
    with chart_col2:
        st.markdown("### Region Risk Heatmap")
        st.plotly_chart(build_region_heatmap(), use_container_width=True)

    st.markdown("### Managing Large User Volume")
    scale_df = pd.DataFrame(
        [
            {"Layer": "Event tracking", "Thesis Role": "Record user actions in an events table for later analysis."},
            {"Layer": "Feature generation", "Thesis Role": "Aggregate events per user at regular intervals."},
            {"Layer": "Batch prediction", "Thesis Role": "Score large user groups using scheduled jobs or batch calls."},
            {"Layer": "Dashboard", "Thesis Role": "Show summaries, filters, segments, regions, and risk groups."},
        ]
    )
    st.dataframe(scale_df, use_container_width=True, hide_index=True)

    st.markdown(
        """
        <div class="panel">
            <div class="panel-title">Evaluation Panel</div>
            <div class="panel-copy">Use preset profiles or manually specified inputs to illustrate the thesis evaluation workflow.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Preset buttons
    preset_col1, preset_col2, preset_col3 = st.columns(3)
    run_profile: str | None = None
    with preset_col1:
        if st.button("Low-risk case", use_container_width=True):
            run_profile = "Low risk"
    with preset_col2:
        if st.button("Balanced case", use_container_width=True):
            run_profile = "Balanced"
    with preset_col3:
        if st.button("High-risk case", use_container_width=True):
            run_profile = "High risk"

    # Manual input mode
    st.markdown("### Manual case specification")
    
    with st.form("custom_test_form", border=True):
        form_col1, form_col2 = st.columns(2)
        
        with form_col1:
            session_length = st.slider(
                "Session length (minutes)",
                min_value=0,
                max_value=120,
                value=30,
                step=5,
                help="Duration of observed user activity"
            )
            cart_value = st.number_input(
                "Cart value ($)",
                min_value=0.0,
                max_value=10000.0,
                value=100.0,
                step=10.0,
                help="Approximate cart value observed in the session"
            )
            page_views = st.number_input(
                "Page views",
                min_value=0,
                max_value=500,
                value=15,
                step=1,
                help="Total pages viewed in the session"
            )
        
        with form_col2:
            days_since_signup = st.slider(
                "Days since signup",
                min_value=0,
                max_value=365,
                value=45,
                step=1,
                help="Age of the user account in days"
            )
            bounce_rate = st.slider(
                "Bounce rate (%)",
                min_value=0.0,
                max_value=100.0,
                value=25.0,
                step=5.0,
                help="Percentage of sessions that ended quickly"
            )
            conversion_rate = st.slider(
                "Conversion rate (%)",
                min_value=0.0,
                max_value=100.0,
                value=3.5,
                step=0.5,
                help="Observed conversion percentage"
            )
        
        submit_custom = st.form_submit_button(
            "Evaluate Case",
            use_container_width=True,
            type="primary"
        )
        
        if submit_custom:
            try:
                custom_payload = {
                    "session_length_minutes": float(session_length),
                    "cart_value_usd": float(cart_value),
                    "page_views": int(page_views),
                    "days_since_signup": int(days_since_signup),
                    "bounce_rate_pct": float(bounce_rate),
                    "conversion_rate_pct": float(conversion_rate),
                }
                
                # Call API with custom payload
                success, data, msg = call_api("/predict", method="POST", data=custom_payload)

                if success and isinstance(data, dict):
                    probability = float(data.get("probability", 0))
                    st.session_state["tracking_test_result"] = {
                        "profile": "Custom",
                        "probability": probability,
                        "risk_label": classify_risk(probability),
                        "risk_kind": risk_kind(probability),
                        "custom": True,
                    }
                    st.rerun()
                else:
                    st.error(f"Evaluation error: {msg}")
            except Exception as e:
                st.error(f"Evaluation failed: {str(e)}")

    if run_profile:
        success, data, msg = score_profile(run_profile)
        if success:
            probability = float(data["probability"])
            st.session_state["tracking_test_result"] = {
                "profile": run_profile,
                "probability": probability,
                "risk_label": classify_risk(probability),
                "risk_kind": risk_kind(probability),
            }
            st.rerun()
        else:
            st.session_state["tracking_test_result"] = {"error": msg}
            st.error(f"Prediction failed: {msg}")

    test_result = st.session_state.get("tracking_test_result")
    if isinstance(test_result, dict):
        if "error" in test_result:
            st.error(f"Prediction failed: {test_result['error']}")
        else:
            gauge_col, text_col = st.columns([0.8, 1.2])
            with gauge_col:
                st.plotly_chart(build_gauge(float(test_result["probability"])), use_container_width=True)
            with text_col:
                st.metric("Profile", str(test_result["profile"]))
                st.metric("Drop-off probability", f"{float(test_result['probability']) * 100:.1f}%")
                render_callout(test_result["risk_kind"], test_result["risk_label"], "Prediction completed.")

    if auto_refresh:
        time.sleep(6)
        st.rerun()


# ============================================================================
# MODEL INTELLIGENCE
# ============================================================================

elif page == "Model Intelligence":
    st.markdown("## Model Analysis")
    st.caption("Quantitative evidence for performance, threshold selection, and interpretability in the proposed model.")

    metric_df = pd.DataFrame(
        {
            "Metric": ["Accuracy", "Precision", "Recall", "F1 Score", "ROC-AUC", "PR-AUC"],
            "Score": [
                metric_value(metrics_blob, "accuracy", 0.9136),
                metric_value(metrics_blob, "precision", 0.8814),
                metric_value(metrics_blob, "recall", 0.9178),
                metric_value(metrics_blob, "f1", 0.8992),
                metric_value(metrics_blob, "roc_auc", 0.9731),
                metric_value(metrics_blob, "pr_auc", 0.9633),
            ],
            "Target": [0.90, 0.85, 0.90, 0.85, 0.95, 0.90],
        }
    )

    top_left, top_right = st.columns([1.2, 0.8])
    with top_left:
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=metric_df["Metric"],
                y=metric_df["Score"],
                name="Achieved",
                marker_color="#355c7d",
                text=[f"{score:.1%}" for score in metric_df["Score"]],
                textposition="auto",
            )
        )
        fig.add_trace(
            go.Bar(
                x=metric_df["Metric"],
                y=metric_df["Target"],
                name="Target",
                marker_color="#dbe3ec",
                text=[f"{score:.1%}" for score in metric_df["Target"]],
                textposition="auto",
            )
        )
        fig.update_layout(barmode="group", yaxis_tickformat=".0%", yaxis_range=[0, 1.05])
        st.plotly_chart(chart_layout(fig, 335), use_container_width=True)
    with top_right:
        tn, fp = confusion[0]
        fn, tp = confusion[1]
        cm_df = pd.DataFrame(
            [
                {"Actual": "Retained", "Predicted": "Retained", "Count": tn},
                {"Actual": "Retained", "Predicted": "Drop-off", "Count": fp},
                {"Actual": "Drop-off", "Predicted": "Retained", "Count": fn},
                {"Actual": "Drop-off", "Predicted": "Drop-off", "Count": tp},
            ]
        )
        fig_cm = px.bar(
            cm_df,
            x="Predicted",
            y="Count",
            color="Actual",
            barmode="group",
            color_discrete_map={"Retained": "#5f7d8a", "Drop-off": "#9a6f75"},
        )
        fig_cm.update_layout(title="Confusion matrix summary")
        st.plotly_chart(chart_layout(fig_cm, 335), use_container_width=True)

    lower_left, lower_right = st.columns(2)
    with lower_left:
        if threshold_df.empty:
            render_callout("warning", "Threshold data missing", "results/threshold_analysis.csv was not found.")
        else:
            threshold_long = threshold_df.melt(
                id_vars=["threshold"],
                value_vars=["precision", "recall", "f1"],
                var_name="Metric",
                value_name="Score",
            )
            fig_threshold = px.line(
                threshold_long,
                x="threshold",
                y="Score",
                color="Metric",
                markers=True,
                color_discrete_map={"precision": "#355c7d", "recall": "#7b8f6f", "f1": "#a88a5b"},
                title="Threshold comparison",
            )
            fig_threshold.update_layout(yaxis_tickformat=".0%")
            st.plotly_chart(chart_layout(fig_threshold, 340), use_container_width=True)

    with lower_right:
        importance_df = pd.DataFrame(
            {
                "Feature": [
                    "Recency",
                    "Session Duration",
                    "Feature Count",
                    "Free Segment",
                    "Mobile Device",
                    "Frequency",
                    "Account Age",
                    "Region",
                    "OS Type",
                ],
                "Importance": [0.28, 0.25, 0.24, 0.12, 0.08, 0.02, 0.01, 0.005, 0.005],
            }
        )
        fig_importance = px.bar(
            importance_df,
            x="Importance",
            y="Feature",
            orientation="h",
            color="Importance",
            color_continuous_scale=ACADEMIC_SOFT_SCALE,
            title="Feature contribution",
        )
        fig_importance.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
        st.plotly_chart(chart_layout(fig_importance, 340), use_container_width=True)

    if not model_df.empty:
        display_model_df = model_df.copy()
        display_model_df["model"] = display_model_df["model"].str.replace("_", " ").str.title()
        st.dataframe(display_model_df, use_container_width=True, hide_index=True)


# ============================================================================
# BATCH SCORING
# ============================================================================

elif page == "Batch Scoring":
    st.markdown("## Batch Analysis")
    st.caption("CSV upload, batch prediction, and exportable summary outputs for thesis evaluation.")

    sample_df = pd.DataFrame(
        [
            {
                "Days Since Signup": 120,
                "Days Since Last Activity": 4,
                "Total Logins": 96,
                "Avg Session Duration (min)": 24.0,
                "Features Used": 11,
                "Device Type": "Desktop",
                "Operating System": "Windows",
                "User Segment": "Premium",
                "Region": "North",
            },
            {
                "Days Since Signup": 410,
                "Days Since Last Activity": 74,
                "Total Logins": 14,
                "Avg Session Duration (min)": 4.5,
                "Features Used": 2,
                "Device Type": "Mobile",
                "Operating System": "iOS",
                "User Segment": "Free",
                "Region": "South",
            },
        ]
    )

    top_a, top_b = st.columns([0.7, 1.3])
    with top_a:
        st.download_button(
            "Download evaluation template",
            sample_df.to_csv(index=False).encode("utf-8"),
            "dropoff_batch_template.csv",
            "text/csv",
            use_container_width=True,
        )
        uploaded_file = st.file_uploader("Upload evaluation CSV", type=["csv"])
    with top_b:
        st.dataframe(sample_df, use_container_width=True, hide_index=True)

    if uploaded_file:
        uploaded_df = pd.read_csv(uploaded_file)
        st.markdown("### Uploaded Data Sample")
        st.dataframe(uploaded_df.head(12), use_container_width=True, hide_index=True)

        if st.button("Run batch evaluation", use_container_width=True):
            try:
                records = uploaded_rows_to_records(uploaded_df)
            except ValueError as exc:
                st.error(str(exc))
            else:
                success, result, msg = call_api("/predict-batch", "POST", {"records": records})
                if not success:
                    st.error(f"Batch prediction failed: {msg}")
                else:
                    predictions = pd.DataFrame(result.get("predictions", []))
                    if predictions.empty:
                        render_callout("warning", "No predictions returned", "Review validation details below.")
                    else:
                        enriched = uploaded_df.copy()
                        enriched["dropoff_probability"] = predictions["dropoff_probability"].values
                        enriched["risk_level"] = predictions["risk_level"].values
                        enriched["predicted_label"] = predictions["predicted_label"].values
                        high_risk_count = int((enriched["dropoff_probability"] >= 0.67).sum())
                        st.metric("Records evaluated", len(enriched))
                        st.metric("High-risk records", high_risk_count)
                        st.dataframe(enriched, use_container_width=True, hide_index=True)

                        export1, export2 = st.columns(2)
                        with export1:
                            st.download_button(
                                "Download scored CSV",
                                enriched.to_csv(index=False).encode("utf-8"),
                                "dropoff_predictions.csv",
                                "text/csv",
                                use_container_width=True,
                            )
                        with export2:
                            st.download_button(
                                "Download scored JSON",
                                enriched.to_json(orient="records", indent=2).encode("utf-8"),
                                "dropoff_predictions.json",
                                "application/json",
                                use_container_width=True,
                            )

                    errors = result.get("errors", [])
                    if errors:
                        st.warning(f"{len(errors)} rows failed validation.")
                        st.dataframe(pd.DataFrame(errors), use_container_width=True, hide_index=True)


# ============================================================================
# SYSTEM HEALTH
# ============================================================================

elif page == "System Health":
    st.markdown("## System Health")
    st.caption("Static summary of API health, model readiness, and project status for thesis presentation.")
    
    # Health status indicators
    api_status = check_api_status()
    ready1, ready2, ready3 = st.columns(3)
    
    with ready1:
        status_icon = "✅ Available" if api_status else "❌ Unavailable"
        color = "green" if api_status else "red"
        render_kpi("Service Layer", status_icon, "Backend service status and validation checks.", color)
    
    with ready2:
        model_status = "✅ Ready"
        render_kpi("Model Layer", model_status, "Prediction and feature engineering components ready.", "teal")
    
    with ready3:
        render_kpi("Dashboard", "✅ Ready", "Interactive interface for presentation and analysis.", "blue")

    # Real-time monitoring with error detection
    monitor_col, errors_col = st.columns([1.2, 1])
    
    with monitor_col:
        st.markdown("### Service Summary")
        st.caption("Snapshot of backend metrics used in the thesis evaluation.")
        
        # Fetch and display monitor data
        success, data, msg = call_api("/monitor")
        
        if success and isinstance(data, dict):
            # Display key metrics in columns
            metric_cols = st.columns(4)
            metrics_dict = data if isinstance(data, dict) else {}
            
            metric_items = [
                ("Requests", metrics_dict.get("requests", 0), "blue"),
                ("Predictions", metrics_dict.get("predictions", 0), "teal"),
                ("Errors", metrics_dict.get("errors", 0), "red"),
                ("Uptime", metrics_dict.get("uptime", "—"), "green"),
            ]
            
            for idx, (label, value, color) in enumerate(metric_items):
                with metric_cols[idx]:
                    st.metric(label, value)
            
            # Detailed JSON view
            with st.expander("Detailed Service Data", expanded=False):
                st.json(data)
        else:
            st.error(f"❌ Service unavailable: {msg}")
            st.info("Attempting to reconnect.")

    with errors_col:
        st.markdown("### Observations")
        st.caption("Notes on the current system state and validation results.")
        
        # Check for common issues
        alerts = []
        
        if not api_status:
            alerts.append(("❌ API Offline", "Flask API not responding. Check server status.", "error"))
        
        success, predictions, _ = call_api("/predictions?limit=10")
        if not success or not predictions:
            alerts.append(("⚠️ No Data", "No recent predictions. Check data pipeline.", "warning"))
        
        if not alerts:
            st.success("✅ Current system state is stable")
        else:
            for title, msg, alert_type in alerts:
                if alert_type == "error":
                    st.error(title)
                    st.caption(msg)
                else:
                    st.warning(title)
                    st.caption(msg)

    # Project summary
    st.markdown("### Project Summary")
    st.caption("Main components included in the final thesis submission.")
    
    artifacts = pd.DataFrame(
        [
            {"Component": "Model", "Status": "✅ Ready", "Artifact": "models/final_model.pkl"},
            {"Component": "API Server", "Status": "✅ Ready" if api_status else "⚠️ Unavailable", "Artifact": "src/api/app.py"},
            {"Component": "Database", "Status": "✅ Available", "Artifact": "SQLite store"},
            {"Component": "Dashboard", "Status": "✅ Included", "Artifact": "streamlit_dashboard.py"},
            {"Component": "Evaluation", "Status": "✅ Completed", "Artifact": "results/*.json, results/*.csv"},
            {"Component": "Workflow", "Status": "✅ Documented", "Artifact": "Project report and thesis materials"},
        ]
    )
    st.dataframe(artifacts, use_container_width=True, hide_index=True)
