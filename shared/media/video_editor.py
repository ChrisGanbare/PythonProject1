"""视频后处理与交付辅助能力。"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import cast

import cv2
import matplotlib.font_manager as font_manager
from PIL import Image, ImageDraw, ImageFont

from shared.core.exceptions import RenderError


class VideoEditor:
    def __init__(self):
        self.ffmpeg_path = shutil.which("ffmpeg")
        self.ffprobe_path = shutil.which("ffprobe")

    @staticmethod
    def _ensure_input_file(input_path: Path, step: str) -> None:
        if not input_path.exists():
            raise RenderError(f"file not found: {input_path}", step=step)

    @staticmethod
    def _format_srt_timestamp(seconds: float) -> str:
        total_milliseconds = max(0, int(round(seconds * 1000)))
        hours, remainder = divmod(total_milliseconds, 3_600_000)
        minutes, remainder = divmod(remainder, 60_000)
        secs, milliseconds = divmod(remainder, 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

    @staticmethod
    def _format_ass_timestamp(seconds: float) -> str:
        total_centiseconds = max(0, int(round(seconds * 100)))
        hours, remainder = divmod(total_centiseconds, 360_000)
        minutes, remainder = divmod(remainder, 6_000)
        secs, centiseconds = divmod(remainder, 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"

    @staticmethod
    def _escape_ass_text(text: str) -> str:
        return (
            text.replace("\\", r"\\")
            .replace("{", r"\{")
            .replace("}", r"\}")
            .replace("\r\n", r"\N")
            .replace("\n", r"\N")
        )

    @staticmethod
    def _hex_to_ass_color(color: str) -> str:
        value = color.strip().lstrip("#")
        if len(value) != 6:
            return "&H00FFFFFF"
        rr, gg, bb = value[0:2], value[2:4], value[4:6]
        return f"&H00{bb.upper()}{gg.upper()}{rr.upper()}"

    @staticmethod
    def _alpha_to_ass(alpha: float) -> str:
        alpha = max(0.0, min(1.0, alpha))
        ass_alpha = int(round((1.0 - alpha) * 255))
        return f"&H{ass_alpha:02X}"

    @staticmethod
    def _coerce_render_expression_payload(render_expression) -> dict:
        if render_expression is None:
            return {}
        if hasattr(render_expression, "model_dump"):
            return render_expression.model_dump()
        return dict(render_expression)

    @staticmethod
    def _read_video_frame_as_image(input_video: Path, timestamp_seconds: float = 0.0) -> Image.Image | None:
        if not input_video.exists():
            return None
        capture = cv2.VideoCapture(str(input_video))
        try:
            if not capture.isOpened():
                return None
            fps = capture.get(cv2.CAP_PROP_FPS) or 0.0
            target_frame = max(0, int(round(timestamp_seconds * fps))) if fps > 0 else 0
            if target_frame > 0:
                capture.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            success, frame = capture.read()
            if not success or frame is None:
                return None
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return Image.fromarray(rgb_frame)
        finally:
            capture.release()

    @staticmethod
    def _resolve_pillow_font(candidates: list[str], size: int) -> ImageFont.ImageFont:
        for family in candidates:
            try:
                font_path = font_manager.findfont(
                    font_manager.FontProperties(family=[family]),
                    fallback_to_default=False,
                )
                if font_path and Path(font_path).exists():
                    return cast(ImageFont.ImageFont, ImageFont.truetype(font_path, size=size))
            except Exception:
                continue
        return ImageFont.load_default()

    @staticmethod
    def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int, max_lines: int) -> list[str]:
        lines: list[str] = []
        for raw_line in text.splitlines() or [text]:
            current = ""
            for char in raw_line:
                candidate = f"{current}{char}"
                bbox = draw.textbbox((0, 0), candidate, font=font)
                if bbox[2] - bbox[0] <= max_width or not current:
                    current = candidate
                    continue
                lines.append(current)
                current = char
                if len(lines) >= max_lines:
                    break
            if len(lines) >= max_lines:
                break
            if current:
                lines.append(current)
            if len(lines) >= max_lines:
                break

        if len(lines) > max_lines:
            lines = lines[:max_lines]
        if lines:
            last = lines[-1]
            while True:
                bbox = draw.textbbox((0, 0), f"{last}…", font=font)
                if bbox[2] - bbox[0] <= max_width or not last:
                    break
                last = last[:-1]
            if last != lines[-1]:
                lines[-1] = f"{last}…"
        return lines or [text]

    @staticmethod
    def _draw_text_block(
        draw: ImageDraw.ImageDraw,
        text: str,
        x: int,
        y: int,
        max_width: int,
        font: ImageFont.ImageFont,
        fill: str,
        line_height: float,
        max_lines: int,
    ) -> int:
        lines = VideoEditor._wrap_text(draw, text, font, max_width=max_width, max_lines=max_lines)
        bbox = draw.textbbox((0, 0), "测", font=font)
        step = max(1, int((bbox[3] - bbox[1]) * line_height))
        for idx, line in enumerate(lines):
            draw.text((x, y + idx * step), line, font=font, fill=fill)
        return y + len(lines) * step

    def create_cover_template(
        self,
        output_image: Path,
        render_expression,
        input_video: Path | None = None,
        timestamp_seconds: float = 0.0,
    ) -> Path:
        """基于共享渲染表达生成主题化封面；失败时由调用方决定是否回退。"""

        payload = self._coerce_render_expression_payload(render_expression)
        cover = payload.get("cover") or {}
        if not cover:
            raise RenderError("cover template tokens missing", step="create_cover_template")

        theme = payload.get("theme") or {}
        typography = payload.get("typography") or {}
        safe_area = payload.get("safe_area") or {}

        width = int(safe_area.get("frame_width", 1280))
        height = int(safe_area.get("frame_height", 720))
        output_image.parent.mkdir(parents=True, exist_ok=True)

        base = None
        if cover.get("use_video_frame_background") and input_video is not None:
            base = self._read_video_frame_as_image(input_video, timestamp_seconds=timestamp_seconds)
            if base is not None:
                base = base.resize((width, height)).convert("RGBA")
        if base is None:
            base = Image.new("RGBA", (width, height), theme.get("background_color", "#111827"))
            gradient = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            gradient_draw = ImageDraw.Draw(gradient)
            for y in range(height):
                alpha = int(110 * (y / max(height - 1, 1)))
                gradient_draw.line(
                    [(0, y), (width, y)],
                    fill=theme.get("panel_color", "#1F2937") + f"{alpha:02x}",
                    width=1,
                )
            base = Image.alpha_composite(base, gradient)

        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rectangle((0, 0, width, height), fill=(8, 15, 30, 115))
        canvas = Image.alpha_composite(base, overlay)
        draw = ImageDraw.Draw(canvas)

        left = int(safe_area.get("left_px", 0)) + 56
        right = width - int(safe_area.get("right_px", 0)) - 56
        top = int(safe_area.get("top_px", 0)) + 56
        bottom = height - int(safe_area.get("bottom_px", 0)) - 56
        content_width = max(240, right - left)

        card_fill = theme.get("panel_color", "#1F2937")
        card_outline = theme.get("accent_color", "#4F9EFF")
        panel_box = (left, top, right, bottom)
        draw.rounded_rectangle(panel_box, radius=28, fill=card_fill, outline=card_outline, width=4)

        font_candidates = [
            typography.get("font_family"),
            *list(typography.get("font_fallbacks") or []),
        ]
        eyebrow_font = self._resolve_pillow_font(font_candidates, max(18, int(typography.get("caption_size", 18) * 1.2)))
        title_font = self._resolve_pillow_font(font_candidates, max(28, int(typography.get("title_size", 56) * 0.78)))
        highlight_font = self._resolve_pillow_font(font_candidates, max(20, int(typography.get("subtitle_size", 30) * 0.82)))
        summary_font = self._resolve_pillow_font(font_candidates, max(18, int(typography.get("body_size", 22) * 0.88)))

        cursor_y = top + 40
        cursor_y = self._draw_text_block(
            draw,
            str(cover.get("eyebrow_text", "")),
            left + 34,
            cursor_y,
            content_width - 68,
            eyebrow_font,
            theme.get("muted_text_color", "#94A3B8"),
            line_height=float(typography.get("caption_line_height", 1.2)),
            max_lines=1,
        )
        cursor_y += 18
        cursor_y = self._draw_text_block(
            draw,
            str(cover.get("title_text", "")),
            left + 34,
            cursor_y,
            content_width - 68,
            title_font,
            theme.get("title_color", "#FFFFFF"),
            line_height=float(typography.get("title_line_height", 1.16)),
            max_lines=3,
        )
        cursor_y += 22

        highlight_text = str(cover.get("highlight_text", "")).strip()
        if highlight_text:
            highlight_bbox = draw.textbbox((0, 0), highlight_text, font=highlight_font)
            badge_width = int(min(content_width - 68, (highlight_bbox[2] - highlight_bbox[0]) + 40))
            badge_height = int((highlight_bbox[3] - highlight_bbox[1]) + 24)
            draw.rounded_rectangle(
                (left + 34, cursor_y, left + 34 + badge_width, cursor_y + badge_height),
                radius=20,
                fill=theme.get("accent_color", "#4F9EFF"),
            )
            draw.text(
                (left + 54, cursor_y + 10),
                highlight_text,
                font=highlight_font,
                fill=theme.get("background_color", "#0B1120"),
            )
            cursor_y += badge_height + 24

        self._draw_text_block(
            draw,
            str(cover.get("summary_text", "")),
            left + 34,
            cursor_y,
            content_width - 68,
            summary_font,
            theme.get("body_color", "#E5E7EB"),
            line_height=float(typography.get("body_line_height", 1.44)),
            max_lines=3,
        )

        canvas.convert("RGB").save(output_image)
        return output_image

    def generate_cover_image(
        self,
        output_image: Path,
        render_expression=None,
        input_video: Path | None = None,
        timestamp_seconds: float = 0.0,
    ) -> Path:
        """优先生成模板封面，失败时回退到视频截帧。"""

        try:
            if render_expression is not None:
                return self.create_cover_template(
                    output_image=output_image,
                    render_expression=render_expression,
                    input_video=input_video,
                    timestamp_seconds=timestamp_seconds,
                )
        except Exception:
            if input_video is None:
                raise
        if input_video is None:
            raise RenderError("cover generation requires render_expression or input_video", step="generate_cover_image")
        return self.extract_cover_frame(input_video, output_image, timestamp_seconds=timestamp_seconds)

    def write_srt(self, subtitle_items: list[dict[str, object]], output_file: Path) -> Path:
        """将字幕片段写入标准 SRT 文件。

        仅依赖 `start` / `end` / `text` 三个字段；其余扩展键会被忽略，
        便于上层传入 style_token、beat_type 等共享字幕元数据。
        """
        output_file.parent.mkdir(parents=True, exist_ok=True)

        rows: list[str] = []
        for index, item in enumerate(subtitle_items, start=1):
            start = float(cast(float | str, item["start"]))
            end = float(cast(float | str, item["end"]))
            text = str(item["text"]).strip()
            if not text:
                continue
            rows.extend(
                [
                    str(index),
                    f"{self._format_srt_timestamp(start)} --> {self._format_srt_timestamp(end)}",
                    text,
                    "",
                ]
            )

        output_file.write_text("\n".join(rows), encoding="utf-8")
        return output_file

    def write_ass(
        self,
        subtitle_items: list[dict[str, object]],
        output_file: Path,
        render_expression=None,
    ) -> Path:
        """根据共享字幕令牌生成样式化 ASS 字幕。"""

        payload = self._coerce_render_expression_payload(render_expression)
        subtitle_layout = payload.get("subtitle_layout") or {}
        subtitle_styles = payload.get("subtitle_styles") or {}
        typography = payload.get("typography") or {}
        safe_area = payload.get("safe_area") or {}

        frame_width = int(safe_area.get("frame_width", 1080))
        frame_height = int(safe_area.get("frame_height", 1920))
        margin_l = int(frame_width * float(subtitle_layout.get("safe_left_ratio", 0.0))) + 36
        margin_r = int(frame_width * float(subtitle_layout.get("safe_right_ratio", 0.0))) + 36
        margin_v = int(subtitle_layout.get("bottom_px", 80)) + 30
        align = str(subtitle_layout.get("align", "center"))
        anchor = str(subtitle_layout.get("anchor", "bottom"))
        max_width_ratio = float(subtitle_layout.get("max_width_ratio", 0.82))
        max_lines = int(subtitle_layout.get("max_lines", 2))
        alignment = 2 if anchor == "bottom" and align == "center" else 2

        def _wrap_ass_text(text: str, font_size: int) -> str:
            approx_chars = max(8, int((frame_width * max_width_ratio) / max(font_size * 0.9, 1)))
            lines: list[str] = []
            for raw_line in str(text).splitlines() or [str(text)]:
                current = ""
                for char in raw_line:
                    candidate = f"{current}{char}"
                    if len(candidate) <= approx_chars or not current:
                        current = candidate
                        continue
                    lines.append(current)
                    current = char
                    if len(lines) >= max_lines:
                        break
                if len(lines) >= max_lines:
                    break
                if current:
                    lines.append(current)
                if len(lines) >= max_lines:
                    break
            lines = lines[:max_lines] if lines else [str(text)]
            return self._escape_ass_text("\n".join(lines))

        style_lines: list[str] = []
        for style_name, style in subtitle_styles.items():
            font_family = str(style.get("font_family", typography.get("font_family", "Arial")))
            font_size = int(style.get("font_size", typography.get("body_size", 22)))
            font_weight = str(style.get("font_weight", "normal"))
            bold = -1 if font_weight in {"bold", "semibold", "heavy", "medium"} else 0
            primary = self._hex_to_ass_color(str(style.get("text_color", "#FFFFFF")))
            outline = self._hex_to_ass_color(str(style.get("stroke_color", "#000000")))
            back_alpha = self._alpha_to_ass(float(style.get("background_alpha", 0.0)))
            style_lines.append(
                "Style: {name},{font},{size},{primary},{secondary},{outline},{back},"
                "{bold},0,0,0,100,100,0,0,1,{outline_width},0,{alignment},{margin_l},{margin_r},{margin_v},1".format(
                    name=style_name,
                    font=font_family,
                    size=font_size,
                    primary=primary,
                    secondary=primary,
                    outline=outline,
                    back=f"{back_alpha}000000",
                    bold=bold,
                    outline_width=max(1.0, float(style.get("stroke_width", 2.0))),
                    alignment=alignment,
                    margin_l=margin_l,
                    margin_r=margin_r,
                    margin_v=margin_v,
                )
            )

        if not style_lines:
            style_lines.append(
                f"Style: Default,Arial,26,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,2.0,0,{alignment},{margin_l},{margin_r},{margin_v},1"
            )

        events: list[str] = []
        for item in subtitle_items:
            start = float(cast(float | str, item["start"]))
            end = float(cast(float | str, item["end"]))
            text = str(item["text"]).strip()
            if not text:
                continue
            style_token = str(item.get("style_token", "body_explainer"))
            style_payload = subtitle_styles.get(style_token) or subtitle_styles.get("body_explainer") or {}
            font_size = int(style_payload.get("font_size", typography.get("body_size", 22)))
            wrapped_text = _wrap_ass_text(text, font_size=font_size)
            events.append(
                f"Dialogue: 0,{self._format_ass_timestamp(start)},{self._format_ass_timestamp(end)},{style_token if style_token in subtitle_styles else 'Default'},,0,0,0,,{wrapped_text}"
            )

        ass_content = "\n".join(
            [
                "[Script Info]",
                "ScriptType: v4.00+",
                f"PlayResX: {frame_width}",
                f"PlayResY: {frame_height}",
                "ScaledBorderAndShadow: yes",
                "WrapStyle: 2",
                "",
                "[V4+ Styles]",
                "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding",
                *style_lines,
                "",
                "[Events]",
                "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text",
                *events,
            ]
        )

        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(ass_content, encoding="utf-8")
        return output_file

    def extract_cover_frame(
        self,
        input_video: Path,
        output_image: Path,
        timestamp_seconds: float = 0.0,
    ) -> Path:
        """提取指定时间点的视频帧作为封面。"""
        self._ensure_input_file(input_video, step="extract_cover_frame")
        output_image.parent.mkdir(parents=True, exist_ok=True)

        capture = cv2.VideoCapture(str(input_video))
        try:
            if not capture.isOpened():
                raise RenderError("cannot open video", step="extract_cover_frame")

            fps = capture.get(cv2.CAP_PROP_FPS) or 0.0
            target_frame = max(0, int(round(timestamp_seconds * fps))) if fps > 0 else 0
            if target_frame > 0:
                capture.set(cv2.CAP_PROP_POS_FRAMES, target_frame)

            success, frame = capture.read()
            if not success or frame is None:
                raise RenderError("cannot read frame from video", step="extract_cover_frame")

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            Image.fromarray(rgb_frame).save(output_image)
            return output_image
        finally:
            capture.release()

    def _ensure_ffmpeg(self) -> None:
        if not self.ffmpeg_path:
            raise RenderError("ffmpeg not found in PATH", step="initialization")

    def _run_command(self, command: list[str], step: str) -> None:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if completed.returncode != 0:
            raise RenderError(
                f"command failed: {' '.join(command)}",
                step=step,
                ffmpeg_stderr=completed.stderr,
            )

    @staticmethod
    def _escape_subtitle_filter_path(path: Path) -> str:
        escaped = path.resolve().as_posix().replace(":", r"\:")
        escaped = escaped.replace("'", r"\'")
        return escaped

    def _has_audio_stream(self, input_video: Path) -> bool:
        if not self.ffprobe_path:
            return False
        completed = subprocess.run(
            [
                self.ffprobe_path,
                "-v",
                "error",
                "-select_streams",
                "a:0",
                "-show_entries",
                "stream=codec_type",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(input_video),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return completed.returncode == 0 and "audio" in completed.stdout.lower()

    def add_subtitle(self, input_video: Path, subtitle_file: Path, output_video: Path, subtitle_codec: str = "mov_text") -> Path:
        self._ensure_ffmpeg()
        self._ensure_input_file(input_video, step="add_subtitle")
        self._ensure_input_file(subtitle_file, step="add_subtitle")
        output_video.parent.mkdir(parents=True, exist_ok=True)
        del subtitle_codec
        subtitle_filter = f"subtitles='{self._escape_subtitle_filter_path(subtitle_file)}'"
        command = [
            self.ffmpeg_path,
            "-y",
            "-i",
            str(input_video),
            "-vf",
            subtitle_filter,
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-c:a",
            "copy",
            str(output_video),
        ]
        self._run_command(command, step="add_subtitle")
        return output_video

    def add_audio(
        self,
        input_video: Path,
        audio_file: Path,
        output_video: Path,
        loop_audio: bool = True,
        audio_volume: float = 0.3,
        video_audio_volume: float = 1.0,
        ducking_enabled: bool = True,
        ducking_strength: float = 0.6,
    ) -> Path:
        self._ensure_ffmpeg()
        self._ensure_input_file(input_video, step="add_audio")
        self._ensure_input_file(audio_file, step="add_audio")
        output_video.parent.mkdir(parents=True, exist_ok=True)

        has_video_audio = self._has_audio_stream(input_video)
        command: list[str] = [self.ffmpeg_path, "-y", "-i", str(input_video)]
        if loop_audio:
            command.extend(["-stream_loop", "-1"])
        command.extend(["-i", str(audio_file)])

        if has_video_audio:
            effective_bgm_volume = max(0.0, audio_volume * (1.0 - ducking_strength)) if ducking_enabled else audio_volume
            filter_complex = (
                f"[0:a]volume={video_audio_volume}[main];"
                f"[1:a]volume={effective_bgm_volume}[bgm];"
                f"[main][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
            )
            command.extend(
                [
                    "-filter_complex",
                    filter_complex,
                    "-map",
                    "0:v:0",
                    "-map",
                    "[aout]",
                    "-c:v",
                    "copy",
                    "-c:a",
                    "aac",
                    "-shortest",
                    str(output_video),
                ]
            )
        else:
            command.extend(
                [
                    "-map",
                    "0:v:0",
                    "-map",
                    "1:a:0",
                    "-c:v",
                    "copy",
                    "-af",
                    f"volume={audio_volume}",
                    "-c:a",
                    "aac",
                    "-shortest",
                    str(output_video),
                ]
            )

        self._run_command(command, step="add_audio")
        return output_video

    def compose_final_video(
        self,
        rendered_video: Path,
        final_video: Path,
        subtitle_file: Path | None = None,
        burn_subtitles: bool = True,
        background_music: Path | None = None,
        bgm_volume: float = 0.22,
        video_audio_volume: float = 1.0,
        loop_audio: bool = True,
        ducking_enabled: bool = True,
        ducking_strength: float = 0.6,
    ) -> Path:
        """串联字幕烧录与 BGM 混音，输出最终成片。"""
        self._ensure_input_file(rendered_video, step="compose_final_video")
        final_video.parent.mkdir(parents=True, exist_ok=True)

        current_video = rendered_video
        temp_video: Path | None = None
        try:
            if burn_subtitles and subtitle_file is not None:
                temp_video = final_video.with_name(f"{final_video.stem}.subtitled{final_video.suffix}")
                current_video = self.add_subtitle(rendered_video, subtitle_file, temp_video)

            if background_music is not None:
                current_video = self.add_audio(
                    current_video,
                    background_music,
                    final_video,
                    loop_audio=loop_audio,
                    audio_volume=bgm_volume,
                    video_audio_volume=video_audio_volume,
                    ducking_enabled=ducking_enabled,
                    ducking_strength=ducking_strength,
                )
            elif current_video != final_video:
                shutil.copyfile(current_video, final_video)
                current_video = final_video
            else:
                shutil.copyfile(rendered_video, final_video)
                current_video = final_video

            return current_video
        finally:
            if temp_video and temp_video.exists() and temp_video != final_video:
                temp_video.unlink(missing_ok=True)

    def concatenate_videos(self, video_list: list[Path], output_video: Path, transition_duration: float = 0.5) -> Path:
        self._ensure_ffmpeg()
        for video in video_list:
            self._ensure_input_file(video, step="concatenate_videos")
        output_video.parent.mkdir(parents=True, exist_ok=True)
        output_video.write_bytes(b"")
        return output_video

    def convert_format(self, input_video: Path, output_video: Path, target_format: str = "mp4", bitrate: int = 8000) -> Path:
        self._ensure_ffmpeg()
        self._ensure_input_file(input_video, step="convert_format")
        output_video.parent.mkdir(parents=True, exist_ok=True)
        output_video.write_bytes(input_video.read_bytes())
        return output_video

    def get_video_info(self, video_path: Path) -> dict:
        self._ensure_input_file(video_path, step="get_video_info")

        capture = cv2.VideoCapture(str(video_path))
        try:
            if not capture.isOpened():
                raise RenderError("cannot open video", step="get_video_info")

            fps = capture.get(cv2.CAP_PROP_FPS) or 0.0
            frame_count = capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
            width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
            height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
            duration = (frame_count / fps) if fps > 0 else 0.0

            return {
                "path": str(video_path),
                "file_size": video_path.stat().st_size,
                "duration": round(duration, 3),
                "resolution": f"{width}x{height}" if width and height else None,
                "fps": round(fps, 3) if fps > 0 else None,
            }
        finally:
            capture.release()
