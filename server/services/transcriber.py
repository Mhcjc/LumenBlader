import asyncio
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

WHISPER_CPP_MODEL = Path.home() / ".whisper-cpp" / "models" / "ggml-medium.bin"


class Transcriber:
    """Transcribes video audio to text using whisper-cpp (preferred) or openai-whisper (fallback)."""

    def __init__(self):
        self._engine = self._detect_engine()
        if self._engine:
            logger.info("Transcriber engine detected: %s", self._engine)
        else:
            logger.warning("No transcription engine available (whisper-cpp or openai-whisper)")

    @property
    def engine_name(self) -> str:
        return self._engine or ""

    def is_available(self) -> bool:
        return self._engine is not None

    async def transcribe(self, video_path: Path, lang: str = "zh") -> str:
        """Transcribe a video file and return the transcript text.

        Args:
            video_path: Path to the video file.
            lang: Language code for transcription (default: "zh" for Chinese).

        Returns:
            The transcription text, or empty string on failure.
        """
        if not self._engine:
            logger.error("No transcription engine available")
            return ""

        if not video_path.exists():
            logger.error("Video file does not exist: %s", video_path)
            return ""

        if self._engine == "whisper-cpp":
            return await self._transcribe_whisper_cpp(video_path, lang)
        elif self._engine == "openai-whisper":
            return await self._transcribe_openai_whisper(video_path, lang)
        return ""

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_engine() -> Optional[str]:
        """Detect the best available transcription engine."""
        # Prefer whisper-cpp (faster, lighter)
        if shutil.which("whisper-cpp") and WHISPER_CPP_MODEL.exists():
            return "whisper-cpp"
        # Fallback to openai-whisper
        if shutil.which("whisper"):
            return "openai-whisper"
        return None

    async def _transcribe_whisper_cpp(self, video_path: Path, lang: str) -> str:
        """Transcribe using whisper-cpp: ffmpeg -> 16kHz mono WAV -> whisper-cpp."""
        tmp_dir = Path(tempfile.mkdtemp(prefix="transcriber_"))
        wav_path = tmp_dir / "audio.wav"
        txt_prefix = tmp_dir / "audio"

        try:
            # Step 1: Extract audio as 16kHz mono WAV
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                str(wav_path),
            ]
            proc = await asyncio.create_subprocess_exec(
                *ffmpeg_cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate()
            if proc.returncode != 0:
                logger.error("ffmpeg failed (rc=%d): %s", proc.returncode, stderr.decode(errors="replace"))
                return ""

            # Step 2: Run whisper-cpp
            whisper_cmd = [
                "whisper-cpp",
                "-m", str(WHISPER_CPP_MODEL),
                "-l", lang,
                "-otxt",
                "-of", str(txt_prefix),
                str(wav_path),
            ]
            proc = await asyncio.create_subprocess_exec(
                *whisper_cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate()
            if proc.returncode != 0:
                logger.error("whisper-cpp failed (rc=%d): %s", proc.returncode, stderr.decode(errors="replace"))
                return ""

            # Step 3: Read the output text file
            txt_path = Path(f"{txt_prefix}.txt")
            if txt_path.exists():
                text = txt_path.read_text(encoding="utf-8").strip()
                return text

            logger.error("whisper-cpp output file not found: %s", txt_path)
            return ""

        except Exception:
            logger.exception("Transcription failed (whisper-cpp)")
            return ""
        finally:
            # Clean up temp files
            shutil.rmtree(tmp_dir, ignore_errors=True)

    async def _transcribe_openai_whisper(self, video_path: Path, lang: str) -> str:
        """Transcribe using openai-whisper CLI."""
        tmp_dir = Path(tempfile.mkdtemp(prefix="transcriber_"))

        try:
            whisper_cmd = [
                "whisper",
                str(video_path),
                "--language", lang,
                "--model", "medium",
                "--output_format", "txt",
                "--output_dir", str(tmp_dir),
            ]
            proc = await asyncio.create_subprocess_exec(
                *whisper_cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate()
            if proc.returncode != 0:
                logger.error("openai-whisper failed (rc=%d): %s", proc.returncode, stderr.decode(errors="replace"))
                return ""

            # Whisper outputs {stem}.txt in the output directory
            stem = video_path.stem
            txt_path = tmp_dir / f"{stem}.txt"
            if txt_path.exists():
                text = txt_path.read_text(encoding="utf-8").strip()
                return text

            logger.error("openai-whisper output file not found: %s", txt_path)
            return ""

        except Exception:
            logger.exception("Transcription failed (openai-whisper)")
            return ""
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
