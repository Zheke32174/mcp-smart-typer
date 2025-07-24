# -*- mode: python ; coding: utf-8 -*-

"""
PyInstaller specification file for MCP Smart Typer UIA Server
Creates a single-file executable with all dependencies bundled.
"""

import sys
from pathlib import Path

# Define paths
project_root = Path('.')
src_path = project_root / 'src'

block_cipher = None

# Collect all source files
src_files = []
for py_file in src_path.rglob('*.py'):
    if py_file.name != '__pycache__':
        relative_path = py_file.relative_to(project_root)
        src_files.append((str(py_file), str(relative_path.parent)))

a = Analysis(
    [str(src_path / 'main.py')],
    pathex=[str(project_root), str(src_path)],
    binaries=[],
    datas=src_files,
    hiddenimports=[
        'grpc',
        'grpcio',
        'grpc_tools',
        'pyautogui',
        'pygetwindow',
        'pynput',
        'pywinauto',
        'uiautomation',
        'pillow',
        'opencv-python',
        'numpy',
        'generated.ui_automation_pb2',
        'generated.ui_automation_pb2_grpc',
        'windows_uia_automation',
        'uia_grpc_server',
        'ui_automation',
        'windows_ui_automation',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'pandas',
        'jupyter',
        'IPython',
        'tornado',
        'zmq',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Remove duplicate files
seen = set()
unique_datas = []
for item in a.datas:
    if item[0] not in seen:
        seen.add(item[0])
        unique_datas.append(item)
a.datas = unique_datas

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='mcp-uia-server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
    version_info={
        'version': (1, 0, 0, 0),
        'description': 'MCP Smart Typer Windows UIA Automation Server',
        'product_name': 'MCP UIA Server',
        'product_version': (1, 0, 0, 0),
        'file_version': (1, 0, 0, 0),
        'company_name': 'MCP Smart Typer Team',
        'file_description': 'Windows UI Automation gRPC Server',
        'copyright': 'Copyright (c) 2024 MCP Smart Typer Team',
        'trademarks': '',
        'original_filename': 'mcp-uia-server.exe',
        'internal_name': 'mcp-uia-server',
    }
)
