@echo off
REM Build script for MCP Smart Typer UIA Server
REM Creates a single-file executable with all dependencies

echo ========================================
echo MCP Smart Typer UIA Server Build Script
echo ========================================

echo.
echo [1/5] Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [2/5] Generating protobuf Python files...
python -m grpc_tools.protoc --proto_path=proto --python_out=src/generated --grpc_python_out=src/generated proto/ui_automation.proto
if errorlevel 1 (
    echo ERROR: Failed to generate protobuf files
    pause
    exit /b 1
)

echo.
echo [3/5] Testing UIA automation module...
cd src
python -c "import windows_uia_automation; print('UIA module loaded successfully')"
if errorlevel 1 (
    echo ERROR: UIA module test failed
    cd ..
    pause
    exit /b 1
)
cd ..

echo.
echo [4/5] Building single-file executable with PyInstaller...
pyinstaller build_uia_server.spec --clean --noconfirm
if errorlevel 1 (
    echo ERROR: PyInstaller build failed
    pause
    exit /b 1
)

echo.
echo [5/5] Verifying build output...
if exist "dist\mcp-uia-server.exe" (
    echo SUCCESS: Executable created at dist\mcp-uia-server.exe
    dir dist\mcp-uia-server.exe
) else (
    echo ERROR: Executable not found in dist directory
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo The executable is located at: dist\mcp-uia-server.exe
echo.
echo Usage:
echo   dist\mcp-uia-server.exe --help
echo   dist\mcp-uia-server.exe --port 50051
echo   dist\mcp-uia-server.exe --verbose
echo.
pause
