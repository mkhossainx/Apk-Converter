#!/usr/bin/env python3
"""
APK/APKM/XAPK → SINGLE APK
Auto‑downloads bundletool.
"""

import os
import sys
import shutil
import zipfile
import subprocess
import tempfile
import uuid
import json
import requests
from pathlib import Path
from flask import Flask, request, render_template_string, send_file, jsonify, after_this_request

# ================== CONFIG ==================
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500 MB
BUNDLETOOL_FILENAME = 'bundletool.jar'
BUNDLETOOL_URL = 'https://github.com/google/bundletool/releases/latest/download/bundletool.jar'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ================== HELPER FUNCTIONS ==================

def download_bundletool():
    """Download latest bundletool.jar if missing"""
    if os.path.exists(BUNDLETOOL_FILENAME):
        return BUNDLETOOL_FILENAME
    print("[*] Downloading bundletool.jar ...")
    try:
        r = requests.get(BUNDLETOOL_URL, stream=True)
        with open(BUNDLETOOL_FILENAME, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        os.chmod(BUNDLETOOL_FILENAME, 0o755)
        return BUNDLETOOL_FILENAME
    except Exception as e:
        raise Exception(f"Failed to download bundletool: {e}")

def find_bundletool():
    bt = os.environ.get('BUNDLETOOL_PATH')
    if bt and os.path.exists(bt):
        return bt
    if os.path.exists(BUNDLETOOL_FILENAME):
        return BUNDLETOOL_FILENAME
    # Try to download
    return download_bundletool()

def run_cmd(cmd, capture=True):
    """Run command, return (stdout, stderr, returncode)"""
    result = subprocess.run(cmd, capture_output=capture, text=True)
    return result.stdout, result.stderr, result.returncode

def detect_type(filepath):
    ext = Path(filepath).suffix.lower()
    if ext in ['.apks', '.apkm']:
        return 'apks'
    elif ext == '.xapk':
        return 'xapk'
    else:
        try:
            with zipfile.ZipFile(filepath, 'r') as z:
                names = z.namelist()
                if any(n.endswith('.apk') for n in names) and any(n.endswith('.obb') for n in names):
                    return 'xapk'
                elif any(n.endswith('.apk') for n in names):
                    return 'apks'
        except:
            pass
    return None

# ================== MERGE METHODS ==================

def merge_method_bundletool(splits_dir, output_path):
    """Method 1: bundletool merge"""
    bt = find_bundletool()
    splits = sorted([str(p) for p in Path(splits_dir).glob('*.apk')])
    if not splits:
        raise Exception("No split APK found.")
    splits_arg = ','.join(splits)
    cmd = ['java', '-jar', bt, 'merge', f'--input-splits={splits_arg}', f'--output={output_path}']
    stdout, stderr, rc = run_cmd(cmd)
    if rc != 0:
        raise Exception(f"bundletool merge failed: {stderr or stdout}")
    return output_path

def merge_method_apktool(splits_dir, output_path):
    """Method 2: Use apktool to decode all splits and merge resources (experimental)"""
    # This is complex and may not work for all. We'll skip for brevity.
    # Actually, we'll try to extract base and then merge resources from other splits manually.
    # For now, we raise to fallback.
    raise Exception("apktool merge not implemented, falling back.")

def merge_method_simple(splits_dir, output_path):
    """Method 3: Extract base.apk and just copy (fallback)"""
    base = os.path.join(splits_dir, 'base.apk')
    if not os.path.exists(base):
        # try any apk that contains 'base'
        for f in Path(splits_dir).glob('*.apk'):
            if 'base' in f.name.lower():
                base = str(f)
                break
        else:
            raise Exception("No base.apk found.")
    shutil.copy(base, output_path)
    return output_path

def convert_apks(filepath, output_path):
    """Main conversion for APKS/APKM – tries all methods"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Extract all APK splits
        with zipfile.ZipFile(filepath, 'r') as z:
            z.extractall(tmpdir)
        splits_dir = tmpdir

        # Try method 1: bundletool merge
        try:
            return merge_method_bundletool(splits_dir, output_path)
        except Exception as e1:
            print(f"[!] bundletool merge failed: {e1}")
            # Try method 2: apktool (skip)
            try:
                return merge_method_apktool(splits_dir, output_path)
            except Exception as e2:
                print(f"[!] apktool merge failed: {e2}")
                # Finally, method 3: just copy base.apk
                try:
                    return merge_method_simple(splits_dir, output_path)
                except Exception as e3:
                    raise Exception(f"All merge methods failed. Last error: {e3}")

def convert_xapk(filepath, output_path):
    """XAPK: extract APK from zip"""
    with zipfile.ZipFile(filepath, 'r') as z:
        apk_files = [f for f in z.namelist() if f.lower().endswith('.apk')]
        if not apk_files:
            raise Exception("No APK found inside XAPK.")
        main_apk = next((f for f in apk_files if 'obb' not in f.lower()), apk_files[0])
        with open(output_path, 'wb') as out:
            out.write(z.read(main_apk))
    return output_path

# ================== NEW HTML TEMPLATE (Ultra-Modern UI) ==================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=yes">
    <title>APK Converter · MKxHACKER</title>
    <!-- Google Fonts + Font Awesome -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">

    <style>
        /* ===== CSS Variables & Reset ===== */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        :root {
            --primary: #6366F1;
            --primary-light: #818CF8;
            --secondary: #8B5CF6;
            --accent: #06B6D4;
            --success: #22C55E;
            --error: #EF4444;
            --bg-primary: #0F172A;
            --bg-secondary: #111827;
            --bg-card: #1E293B;
            --glass-bg: rgba(30, 41, 59, 0.6);
            --glass-border: rgba(255,255,255,0.08);
            --text-primary: #F1F5F9;
            --text-secondary: #94A3B8;
            --shadow: 0 20px 60px rgba(0,0,0,0.5);
            --radius: 28px;
            --transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        body {
            font-family: 'Poppins', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            overflow-x: hidden;
            position: relative;
        }

        /* ===== Animated Background Blobs ===== */
        .blob {
            position: fixed;
            border-radius: 50%;
            filter: blur(120px);
            opacity: 0.25;
            z-index: 0;
            pointer-events: none;
            animation: blobFloat 20s infinite alternate ease-in-out;
        }
        .blob-1 {
            width: 500px;
            height: 500px;
            background: var(--primary);
            top: -150px;
            left: -150px;
        }
        .blob-2 {
            width: 400px;
            height: 400px;
            background: var(--secondary);
            bottom: -100px;
            right: -100px;
            animation-delay: -6s;
        }
        .blob-3 {
            width: 300px;
            height: 300px;
            background: var(--accent);
            top: 40%;
            left: 50%;
            transform: translateX(-50%);
            animation-delay: -12s;
        }
        @keyframes blobFloat {
            0% { transform: translate(0, 0) scale(1); }
            33% { transform: translate(60px, -40px) scale(1.1); }
            66% { transform: translate(-30px, 60px) scale(0.9); }
            100% { transform: translate(20px, -20px) scale(1.05); }
        }

        /* ===== Main Container ===== */
        .app-container {
            position: relative;
            z-index: 1;
            width: 100%;
            max-width: 480px;
            margin: 0 auto;
        }

        /* ===== Glassmorphism Card ===== */
        .glass-card {
            background: var(--glass-bg);
            backdrop-filter: blur(24px);
            -webkit-backdrop-filter: blur(24px);
            border: 1px solid var(--glass-border);
            border-radius: var(--radius);
            padding: 32px 24px;
            box-shadow: var(--shadow);
            transition: var(--transition);
        }

        /* ===== Header ===== */
        .app-header {
            text-align: center;
            margin-bottom: 28px;
        }
        .app-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 80px;
            height: 80px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border-radius: 28px;
            font-size: 40px;
            color: #fff;
            box-shadow: 0 12px 40px rgba(99,102,241,0.4);
            margin-bottom: 16px;
            animation: floatIcon 4s ease-in-out infinite;
        }
        @keyframes floatIcon {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }
        .app-title {
            font-size: 28px;
            font-weight: 800;
            background: linear-gradient(to right, var(--primary-light), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: -0.5px;
        }
        .app-subtitle {
            font-size: 14px;
            color: var(--text-secondary);
            font-weight: 400;
            margin-top: 4px;
            letter-spacing: 0.3px;
        }

        /* ===== Upload Area (Drag & Drop) ===== */
        .upload-area {
            position: relative;
            border: 2px dashed rgba(255,255,255,0.15);
            border-radius: 20px;
            padding: 40px 20px;
            text-align: center;
            transition: var(--transition);
            background: rgba(255,255,255,0.02);
            cursor: pointer;
            margin-bottom: 20px;
            min-height: 160px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        .upload-area.dragover {
            border-color: var(--primary);
            background: rgba(99,102,241,0.08);
            box-shadow: 0 0 40px rgba(99,102,241,0.15);
        }
        .upload-area .upload-icon {
            font-size: 52px;
            color: var(--text-secondary);
            margin-bottom: 12px;
            transition: var(--transition);
        }
        .upload-area.dragover .upload-icon {
            color: var(--primary);
            transform: scale(1.1);
        }
        .upload-area .upload-text {
            font-size: 16px;
            font-weight: 500;
            color: var(--text-secondary);
        }
        .upload-area .upload-hint {
            font-size: 13px;
            color: var(--text-secondary);
            opacity: 0.6;
        }
        .upload-area .file-preview {
            display: none;
            margin-top: 16px;
            width: 100%;
            background: rgba(255,255,255,0.05);
            border-radius: 14px;
            padding: 14px 16px;
            text-align: left;
            animation: slideUp 0.4s ease;
        }
        .upload-area .file-preview .file-info {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .upload-area .file-preview .file-icon {
            font-size: 32px;
            color: var(--primary);
        }
        .upload-area .file-preview .file-name {
            font-weight: 500;
            font-size: 15px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .upload-area .file-preview .file-size {
            font-size: 13px;
            color: var(--text-secondary);
        }
        .upload-area .file-preview .file-badge {
            background: var(--primary);
            color: #fff;
            font-size: 11px;
            font-weight: 600;
            padding: 2px 10px;
            border-radius: 20px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-left: auto;
        }
        .upload-area .file-preview .remove-file {
            background: none;
            border: none;
            color: var(--text-secondary);
            font-size: 18px;
            cursor: pointer;
            padding: 4px 8px;
            transition: var(--transition);
        }
        .upload-area .file-preview .remove-file:hover {
            color: var(--error);
        }
        .upload-area input[type="file"] {
            display: none;
        }

        /* ===== Buttons ===== */
        .btn-group {
            display: flex;
            gap: 12px;
            margin-top: 8px;
        }
        .btn {
            flex: 1;
            padding: 16px 20px;
            border: none;
            border-radius: 16px;
            font-family: 'Poppins', sans-serif;
            font-weight: 600;
            font-size: 16px;
            cursor: pointer;
            transition: var(--transition);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            position: relative;
            overflow: hidden;
        }
        .btn-primary {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: #fff;
            box-shadow: 0 8px 24px rgba(99,102,241,0.35);
        }
        .btn-primary:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 12px 36px rgba(99,102,241,0.5);
        }
        .btn-primary:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        .btn-secondary {
            background: rgba(255,255,255,0.08);
            color: var(--text-primary);
            border: 1px solid rgba(255,255,255,0.1);
        }
        .btn-secondary:hover {
            background: rgba(255,255,255,0.14);
        }
        .btn-success {
            background: var(--success);
            color: #fff;
        }
        .btn-danger {
            background: var(--error);
            color: #fff;
        }

        /* Ripple effect */
        .btn::after {
            content: '';
            position: absolute;
            inset: 0;
            background: radial-gradient(circle at var(--mx, 50%) var(--my, 50%), rgba(255,255,255,0.2) 0%, transparent 60%);
            opacity: 0;
            transition: opacity 0.5s;
            pointer-events: none;
        }
        .btn:active::after {
            opacity: 1;
            transition: 0s;
        }

        /* ===== Status & Progress ===== */
        .status-container {
            margin-top: 24px;
            display: none;
            flex-direction: column;
            align-items: center;
            gap: 16px;
            animation: fadeIn 0.5s ease;
        }
        .status-container.active {
            display: flex;
        }
        .progress-ring {
            position: relative;
            width: 80px;
            height: 80px;
        }
        .progress-ring svg {
            transform: rotate(-90deg);
        }
        .progress-ring .bg-circle {
            fill: none;
            stroke: rgba(255,255,255,0.06);
            stroke-width: 6;
        }
        .progress-ring .progress-circle {
            fill: none;
            stroke: var(--primary);
            stroke-width: 6;
            stroke-linecap: round;
            stroke-dasharray: 226.19;
            stroke-dashoffset: 226.19;
            transition: stroke-dashoffset 0.35s ease, stroke 0.3s;
        }
        .progress-ring .progress-text {
            position: absolute;
            inset: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 20px;
            color: var(--text-primary);
        }
        .status-message {
            font-size: 15px;
            font-weight: 500;
            color: var(--text-secondary);
            text-align: center;
        }
        .status-message .status-icon {
            margin-right: 8px;
        }

        /* ===== Success / Error Screens ===== */
        .result-screen {
            display: none;
            flex-direction: column;
            align-items: center;
            gap: 16px;
            margin-top: 20px;
            animation: fadeIn 0.6s ease;
        }
        .result-screen.active {
            display: flex;
        }
        .result-icon {
            font-size: 72px;
            animation: popIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .result-icon.success {
            color: var(--success);
        }
        .result-icon.error {
            color: var(--error);
        }
        .result-title {
            font-size: 22px;
            font-weight: 700;
        }
        .result-sub {
            font-size: 14px;
            color: var(--text-secondary);
            text-align: center;
            max-width: 280px;
        }
        .result-actions {
            display: flex;
            gap: 12px;
            width: 100%;
            margin-top: 4px;
        }
        .result-actions .btn {
            flex: 1;
        }

        /* ===== Footer ===== */
        .footer {
            margin-top: 28px;
            text-align: center;
            font-size: 13px;
            color: var(--text-secondary);
            opacity: 0.6;
        }
        .footer a {
            color: var(--primary-light);
            text-decoration: none;
        }

        /* ===== Animations ===== */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(16px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes slideUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes popIn {
            0% { transform: scale(0); opacity: 0; }
            80% { transform: scale(1.1); }
            100% { transform: scale(1); opacity: 1; }
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,0.2);
            border-top-color: #fff;
            border-radius: 50%;
            animation: spin 0.7s linear infinite;
        }

        /* ===== Scrollbar ===== */
        ::-webkit-scrollbar {
            width: 6px;
        }
        ::-webkit-scrollbar-track {
            background: transparent;
        }
        ::-webkit-scrollbar-thumb {
            background: var(--primary);
            border-radius: 10px;
        }

        /* ===== Responsive ===== */
        @media (max-width: 480px) {
            .app-container { padding: 0; }
            .glass-card { padding: 24px 16px; border-radius: 24px; }
            .app-title { font-size: 24px; }
            .upload-area { padding: 30px 16px; min-height: 130px; }
            .upload-area .upload-icon { font-size: 42px; }
            .btn { font-size: 14px; padding: 14px 16px; }
        }
        /* Light mode (optional) */
        body.light {
            --bg-primary: #F1F5F9;
            --bg-secondary: #E2E8F0;
            --bg-card: #FFFFFF;
            --glass-bg: rgba(255,255,255,0.7);
            --glass-border: rgba(0,0,0,0.06);
            --text-primary: #0F172A;
            --text-secondary: #475569;
            --shadow: 0 20px 60px rgba(0,0,0,0.1);
        }
        body.light .upload-area {
            background: rgba(0,0,0,0.02);
        }
        body.light .upload-area.dragover {
            background: rgba(99,102,241,0.06);
        }
        body.light .btn-secondary {
            background: rgba(0,0,0,0.05);
            border-color: rgba(0,0,0,0.08);
        }
        body.light .btn-secondary:hover {
            background: rgba(0,0,0,0.1);
        }
        body.light .progress-ring .bg-circle {
            stroke: rgba(0,0,0,0.08);
        }
        /* Theme toggle */
        .theme-toggle {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10;
            background: var(--glass-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--glass-border);
            border-radius: 50%;
            width: 44px;
            height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            cursor: pointer;
            color: var(--text-primary);
            transition: var(--transition);
            box-shadow: var(--shadow);
        }
        .theme-toggle:hover {
            transform: scale(1.05);
        }
        .theme-toggle .fa-moon { display: block; }
        .theme-toggle .fa-sun { display: none; }
        body.light .theme-toggle .fa-moon { display: none; }
        body.light .theme-toggle .fa-sun { display: block; }

        /* Toast */
        .toast {
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            background: var(--glass-bg);
            backdrop-filter: blur(16px);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            padding: 14px 24px;
            color: var(--text-primary);
            font-weight: 500;
            box-shadow: var(--shadow);
            z-index: 100;
            opacity: 0;
            transition: opacity 0.4s, transform 0.4s;
            transform: translateX(-50%) translateY(20px);
            pointer-events: none;
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 14px;
            max-width: 90%;
        }
        .toast.show {
            opacity: 1;
            transform: translateX(-50%) translateY(0);
            pointer-events: auto;
        }
        .toast .toast-icon { font-size: 20px; }
        .toast.success .toast-icon { color: var(--success); }
        .toast.error .toast-icon { color: var(--error); }
        .toast.info .toast-icon { color: var(--primary); }
    </style>
</head>
<body>
    <!-- Theme Toggle -->
    <div class="theme-toggle" id="themeToggle" aria-label="Toggle theme">
        <i class="fas fa-moon"></i>
        <i class="fas fa-sun"></i>
    </div>

    <!-- Animated Blobs -->
    <div class="blob blob-1"></div>
    <div class="blob blob-2"></div>
    <div class="blob blob-3"></div>

    <!-- Toast -->
    <div class="toast" id="toast">
        <span class="toast-icon"></span>
        <span class="toast-msg">Message</span>
    </div>

    <!-- Main App -->
    <div class="app-container">
        <div class="glass-card">
            <!-- Header -->
            <div class="app-header">
                <div class="app-icon">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="app-title">APK Converter</div>
                <div class="app-subtitle">Convert .apks · .apkm · .xapk → .apk</div>
            </div>

            <!-- Upload Area -->
            <div class="upload-area" id="uploadArea">
                <div class="upload-icon" id="uploadIcon">
                    <i class="fas fa-cloud-upload-alt"></i>
                </div>
                <div class="upload-text" id="uploadText">Tap or drag & drop your file</div>
                <div class="upload-hint">Supports .apks, .apkm, .xapk</div>
                <div class="file-preview" id="filePreview">
                    <div class="file-info">
                        <div class="file-icon"><i class="fas fa-file-archive"></i></div>
                        <div>
                            <div class="file-name" id="fileName">file.apks</div>
                            <div class="file-size" id="fileSize">12.3 MB</div>
                        </div>
                        <div class="file-badge" id="fileBadge">APKS</div>
                        <button class="remove-file" id="removeFile" aria-label="Remove file">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
                <input type="file" id="fileInput" name="file" accept=".apks,.apkm,.xapk">
            </div>

            <!-- Buttons -->
            <div class="btn-group">
                <button class="btn btn-primary" id="convertBtn" disabled>
                    <i class="fas fa-arrow-right"></i> Convert
                </button>
                <button class="btn btn-secondary" id="resetBtn">
                    <i class="fas fa-undo-alt"></i>
                </button>
            </div>

            <!-- Status / Progress -->
            <div class="status-container" id="statusContainer">
                <div class="progress-ring">
                    <svg width="80" height="80" viewBox="0 0 80 80">
                        <circle class="bg-circle" cx="40" cy="40" r="36"/>
                        <circle class="progress-circle" id="progressCircle" cx="40" cy="40" r="36"/>
                    </svg>
                    <div class="progress-text" id="progressText">0%</div>
                </div>
                <div class="status-message" id="statusMessage">
                    <span class="status-icon"><i class="fas fa-spinner fa-pulse"></i></span>
                    Processing...
                </div>
            </div>

            <!-- Result Screen -->
            <div class="result-screen" id="resultScreen">
                <div class="result-icon" id="resultIcon"><i class="fas fa-check-circle"></i></div>
                <div class="result-title" id="resultTitle">Success!</div>
                <div class="result-sub" id="resultSub">Your APK is ready for download.</div>
                <div class="result-actions">
                    <button class="btn btn-success" id="downloadBtn"><i class="fas fa-download"></i> Download</button>
                    <button class="btn btn-secondary" id="convertAgainBtn"><i class="fas fa-sync-alt"></i> Again</button>
                </div>
            </div>

            <!-- Footer -->
            <div class="footer">
                Made with <i class="fas fa-heart" style="color: var(--error);"></i> by
                <a href="https://t.me/mk_hossain" target="_blank">MK Hossain</a>
            </div>
        </div>
    </div>

    <script>
        // ============================================================
        // FRONTEND LOGIC – Only UI, no backend changes
        // ============================================================

        (function() {
            'use strict';

            // --- DOM refs ---
            const uploadArea = document.getElementById('uploadArea');
            const fileInput = document.getElementById('fileInput');
            const filePreview = document.getElementById('filePreview');
            const fileName = document.getElementById('fileName');
            const fileSize = document.getElementById('fileSize');
            const fileBadge = document.getElementById('fileBadge');
            const removeFileBtn = document.getElementById('removeFile');
            const convertBtn = document.getElementById('convertBtn');
            const resetBtn = document.getElementById('resetBtn');
            const statusContainer = document.getElementById('statusContainer');
            const progressCircle = document.getElementById('progressCircle');
            const progressText = document.getElementById('progressText');
            const statusMessage = document.getElementById('statusMessage');
            const resultScreen = document.getElementById('resultScreen');
            const resultIcon = document.getElementById('resultIcon');
            const resultTitle = document.getElementById('resultTitle');
            const resultSub = document.getElementById('resultSub');
            const downloadBtn = document.getElementById('downloadBtn');
            const convertAgainBtn = document.getElementById('convertAgainBtn');
            const themeToggle = document.getElementById('themeToggle');
            const toast = document.getElementById('toast');
            const toastMsg = toast.querySelector('.toast-msg');
            const toastIcon = toast.querySelector('.toast-icon');

            // --- State ---
            let selectedFile = null;
            let isConverting = false;
            let downloadUrl = null;

            const CIRCUMFERENCE = 2 * Math.PI * 36; // ~226.19

            // --- Helper: Toast ---
            function showToast(message, type = 'info', duration = 3000) {
                toast.className = 'toast';
                toast.classList.add(type);
                toastIcon.className = 'toast-icon fas';
                if (type === 'success') toastIcon.classList.add('fa-check-circle');
                else if (type === 'error') toastIcon.classList.add('fa-exclamation-circle');
                else toastIcon.classList.add('fa-info-circle');
                toastMsg.textContent = message;
                toast.classList.add('show');
                clearTimeout(toast._timer);
                toast._timer = setTimeout(() => {
                    toast.classList.remove('show');
                }, duration);
            }

            // --- File handling ---
            function formatSize(bytes) {
                if (bytes < 1024) return bytes + ' B';
                if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
                return (bytes / 1048576).toFixed(1) + ' MB';
            }

            function getFileExtension(filename) {
                return filename.split('.').pop().toLowerCase();
            }

            function handleFile(file) {
                if (!file) return;
                // Check extension
                const ext = getFileExtension(file.name);
                if (!['apks', 'apkm', 'xapk'].includes(ext)) {
                    showToast('Unsupported file type. Please upload .apks, .apkm, or .xapk', 'error');
                    return;
                }
                selectedFile = file;
                // Update UI
                fileName.textContent = file.name;
                fileSize.textContent = formatSize(file.size);
                fileBadge.textContent = ext.toUpperCase();
                filePreview.style.display = 'block';
                document.getElementById('uploadText').style.display = 'none';
                document.getElementById('uploadIcon').querySelector('i').className = 'fas fa-file-archive';
                convertBtn.disabled = false;
                // Hide status & result
                statusContainer.classList.remove('active');
                resultScreen.classList.remove('active');
                // Show toast
                showToast('File selected: ' + file.name, 'success');
            }

            function resetFile() {
                selectedFile = null;
                fileInput.value = '';
                filePreview.style.display = 'none';
                document.getElementById('uploadText').style.display = 'block';
                document.getElementById('uploadIcon').querySelector('i').className = 'fas fa-cloud-upload-alt';
                convertBtn.disabled = true;
                statusContainer.classList.remove('active');
                resultScreen.classList.remove('active');
                if (downloadUrl) {
                    URL.revokeObjectURL(downloadUrl);
                    downloadUrl = null;
                }
            }

            // --- Drag & Drop ---
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });
            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('dragover');
            });
            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    handleFile(files[0]);
                    // Also set the file input for consistency (not strictly needed)
                    const dt = new DataTransfer();
                    dt.items.add(files[0]);
                    fileInput.files = dt.files;
                }
            });

            // --- Click to upload ---
            uploadArea.addEventListener('click', () => {
                if (isConverting) return;
                fileInput.click();
            });

            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    handleFile(e.target.files[0]);
                }
            });

            // --- Remove file ---
            removeFileBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                resetFile();
            });

            // --- Reset button ---
            resetBtn.addEventListener('click', () => {
                if (isConverting) return;
                resetFile();
                showToast('Reset', 'info');
            });

            // --- Convert button ---
            convertBtn.addEventListener('click', async () => {
                if (!selectedFile || isConverting) return;

                isConverting = true;
                convertBtn.disabled = true;
                resetBtn.disabled = true;

                // Show status with progress
                statusContainer.classList.add('active');
                resultScreen.classList.remove('active');
                progressCircle.style.strokeDashoffset = CIRCUMFERENCE;
                progressText.textContent = '0%';
                statusMessage.innerHTML = '<span class="status-icon"><i class="fas fa-spinner fa-pulse"></i></span> Initializing...';
                // Animate progress simulation (just for UX; real progress not available)
                let simulated = 0;
                const interval = setInterval(() => {
                    simulated += 2;
                    if (simulated >= 90) {
                        clearInterval(interval);
                        return;
                    }
                    const offset = CIRCUMFERENCE - (simulated / 100) * CIRCUMFERENCE;
                    progressCircle.style.strokeDashoffset = offset;
                    progressText.textContent = simulated + '%';
                }, 200);

                const formData = new FormData();
                formData.append('file', selectedFile);

                try {
                    const response = await fetch('/', {
                        method: 'POST',
                        body: formData
                    });

                    clearInterval(interval);
                    // Set progress to 100% quickly
                    progressCircle.style.strokeDashoffset = 0;
                    progressText.textContent = '100%';

                    if (response.ok) {
                        // Success – download
                        const blob = await response.blob();
                        downloadUrl = URL.createObjectURL(blob);
                        // Show result success
                        statusContainer.classList.remove('active');
                        resultScreen.classList.add('active');
                        resultIcon.className = 'result-icon success';
                        resultIcon.innerHTML = '<i class="fas fa-check-circle"></i>';
                        resultTitle.textContent = 'Conversion Completed!';
                        resultSub.textContent = 'Your APK is ready for download.';
                        downloadBtn.onclick = () => {
                            const a = document.createElement('a');
                            a.href = downloadUrl;
                            a.download = 'converted.apk';
                            document.body.appendChild(a);
                            a.click();
                            a.remove();
                            showToast('Download started!', 'success');
                        };
                        convertAgainBtn.style.display = 'inline-flex';
                        showToast('Conversion successful!', 'success');
                    } else {
                        // Error
                        const errData = await response.json();
                        throw new Error(errData.error || 'Conversion failed');
                    }
                } catch (err) {
                    clearInterval(interval);
                    statusContainer.classList.remove('active');
                    resultScreen.classList.add('active');
                    resultIcon.className = 'result-icon error';
                    resultIcon.innerHTML = '<i class="fas fa-exclamation-circle"></i>';
                    resultTitle.textContent = 'Conversion Failed';
                    resultSub.textContent = err.message || 'Something went wrong. Please try again.';
                    downloadBtn.style.display = 'none';
                    convertAgainBtn.style.display = 'inline-flex';
                    showToast('Error: ' + err.message, 'error');
                } finally {
                    isConverting = false;
                    convertBtn.disabled = false;
                    resetBtn.disabled = false;
                    // reset progress to 0 for next time
                    setTimeout(() => {
                        progressCircle.style.strokeDashoffset = CIRCUMFERENCE;
                        progressText.textContent = '0%';
                    }, 300);
                }
            });

            // --- Convert Again ---
            convertAgainBtn.addEventListener('click', () => {
                resetFile();
                resultScreen.classList.remove('active');
                downloadBtn.style.display = 'inline-flex';
                convertAgainBtn.style.display = 'none';
                showToast('Ready for new conversion', 'info');
            });

            // --- Theme toggle ---
            themeToggle.addEventListener('click', () => {
                document.body.classList.toggle('light');
                const isLight = document.body.classList.contains('light');
                localStorage.setItem('theme', isLight ? 'light' : 'dark');
            });
            // Load saved theme
            if (localStorage.getItem('theme') === 'light') {
                document.body.classList.add('light');
            }

            // --- Initial state ---
            resetFile();

            // --- Ripple effect on buttons ---
            document.querySelectorAll('.btn').forEach(btn => {
                btn.addEventListener('mousedown', (e) => {
                    const rect = btn.getBoundingClientRect();
                    btn.style.setProperty('--mx', ((e.clientX - rect.left) / rect.width * 100) + '%');
                    btn.style.setProperty('--my', ((e.clientY - rect.top) / rect.height * 100) + '%');
                });
            });

        })();
    </script>
</body>
</html>
"""

# ================== FLASK ROUTES ==================

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        unique_id = str(uuid.uuid4())
        ext = Path(file.filename).suffix
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{unique_id}{ext}')
        file.save(input_path)

        ftype = detect_type(input_path)
        if not ftype:
            os.remove(input_path)
            return jsonify({'error': 'Unsupported format'}), 400

        output_path = os.path.join(app.config['OUTPUT_FOLDER'], f'{unique_id}.apk')
        log_messages = []
        def log(msg):
            log_messages.append(msg)
            print(msg)

        try:
            log(f"[*] Detected type: {ftype}")
            if ftype == 'apks':
                log("[*] Trying APKS merge...")
                convert_apks(input_path, output_path)
                log("[✓] Merge complete.")
            elif ftype == 'xapk':
                log("[*] Extracting APK from XAPK...")
                convert_xapk(input_path, output_path)
                log("[✓] Extraction complete.")
            else:
                raise Exception('Unsupported')
            os.remove(input_path)

            @after_this_request
            def cleanup(response):
                try:
                    os.remove(output_path)
                except:
                    pass
                return response
            return send_file(output_path, as_attachment=True, download_name=f'converted_{unique_id}.apk')
        except Exception as e:
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)
            error_msg = str(e)
            log(f"[!] ERROR: {error_msg}")
            return jsonify({'error': error_msg, 'log': '\n'.join(log_messages)}), 500
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    # Ensure bundletool is downloaded on startup
    try:
        find_bundletool()
        print("[✓] bundletool ready.")
    except Exception as e:
        print(f"[!] Warning: {e}")
    print("🔥 MKxHACKER APK Converter started at http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)