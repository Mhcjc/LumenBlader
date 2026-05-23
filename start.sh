#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

cleanup() {
    echo "Stopping services..."
    kill $TIKTOK_PID $APP_PID 2>/dev/null
    wait $TIKTOK_PID $APP_PID 2>/dev/null
    echo "All stopped."
}
trap cleanup EXIT INT TERM

# Check dependencies
echo "Checking dependencies..."
if command -v whisper-cpp >/dev/null 2>&1; then
    echo "  whisper-cpp: OK"
elif command -v whisper >/dev/null 2>&1; then
    echo "  whisper (openai-whisper): OK"
else
    echo "  ⚠️  whisper not installed — video transcription will be skipped"
    echo "     Install: brew install whisper-cpp"
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "  ❌ ffmpeg not installed — required for video processing"
    echo "     Install: brew install ffmpeg"
    exit 1
fi
echo ""

echo "Starting TikTokDownloader (API mode)..."
cd "$PARENT_DIR/TikTokDownloader"
# Auto-select: language=1(zh_CN), disclaimer=YES, mode=5(Web API)
echo -e "1\nYES\n5" | .venv/bin/python main.py &
TIKTOK_PID=$!

sleep 5

echo "Starting LumenBlader..."
cd "$SCRIPT_DIR"
.venv/bin/python run.py &
APP_PID=$!

echo ""
echo "=== Services ==="
echo "  TikTokDownloader: http://127.0.0.1:5555"
echo "  LumenBlader:       http://localhost:8080"
echo "================="
echo ""
echo "Press Ctrl+C to stop all services."

wait
