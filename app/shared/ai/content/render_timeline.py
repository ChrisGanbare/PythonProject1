"""Screenplay to render timeline mapping."""

from __future__ import annotations

import re

from pydantic import BaseModel, Field, model_validator

from shared.ai.content.scene_pacing import resolve_scene_pacing_token
from shared.ai.content.screenplay import Screenplay


class TimelineSegment(BaseModel):
    role: str
    scene_id: str | None = None
    scene_label: str | None = None
    scene_ids: list[str] = Field(default_factory=list)
    narration: str | None = None
    visual_prompt: str | None = None
    mood: str | None = None
    pacing_token: str | None = None
    start_seconds: float = 0.0
    end_seconds: float = 0.0
    duration_seconds: float = 0.0
    start_frame: int = 0
    end_frame: int = 0
    duration_frames: int = 0

    @model_validator(mode="after")
    def _normalize_scene_identifiers(self) -> "TimelineSegment":
        if self.scene_id and not self.scene_ids:
            self.scene_ids = [self.scene_id]
        elif self.scene_ids and not self.scene_id:
            self.scene_id = self.scene_ids[0]
        return self


class RenderTimeline(BaseModel):
    total_seconds: float
    total_frames: int
    phases: list[TimelineSegment] = Field(default_factory=list)
    scenes: list[TimelineSegment] = Field(default_factory=list)

    def get_phase(self, role: str) -> TimelineSegment | None:
        for segment in self.phases:
            if segment.role == role:
                return segment
        return None

    def _normalize_frame(self, frame: int) -> int:
        if self.total_frames <= 1:
            return 0
        return max(0, min(int(frame), self.total_frames - 1))

    def _get_segment_for_frame(self, segments: list[TimelineSegment], frame: int) -> TimelineSegment | None:
        if not segments:
            return None

        normalized_frame = self._normalize_frame(frame)
        fallback = segments[-1]
        for segment in segments:
            start_frame = max(0, int(segment.start_frame))
            end_frame = max(start_frame + 1, int(segment.end_frame or self.total_frames))
            if start_frame <= normalized_frame < end_frame:
                return segment
            if normalized_frame < start_frame:
                return segment
        return fallback

    def get_phase_for_frame(self, frame: int) -> TimelineSegment | None:
        return self._get_segment_for_frame(self.phases, frame)

    def get_scene_for_frame(self, frame: int) -> TimelineSegment | None:
        return self._get_segment_for_frame(self.scenes, frame)

    @staticmethod
    def _truncate_log_text(text: str | None, limit: int = 28) -> str:
        value = " ".join(str(text or "").split())
        if len(value) <= limit:
            return value
        return value[: max(0, limit - 1)].rstrip() + "…"

    def scene_schedule_records(self) -> list[dict[str, str | int | float]]:
        records: list[dict[str, str | int | float]] = []
        for segment in self.scenes:
            records.append(
                {
                    "role": segment.role,
                    "scene_id": segment.scene_id or (segment.scene_ids[0] if segment.scene_ids else ""),
                    "scene_label": segment.scene_label or "",
                    "mood": segment.mood or "",
                    "pacing_token": segment.pacing_token or "steady",
                    "start_frame": int(segment.start_frame),
                    "end_frame": int(segment.end_frame),
                    "duration_frames": int(segment.duration_frames),
                    "start_seconds": round(float(segment.start_seconds), 3),
                    "end_seconds": round(float(segment.end_seconds), 3),
                    "duration_seconds": round(float(segment.duration_seconds), 3),
                    "visual_prompt": self._truncate_log_text(segment.visual_prompt, 42),
                    "narration": self._truncate_log_text(segment.narration),
                }
            )
        return records

    def scene_schedule_log_lines(self) -> list[str]:
        lines: list[str] = []
        for record in self.scene_schedule_records():
            lines.append(
                "scene_schedule"
                f" :: role={record['role']}"
                f" :: scene_id={record['scene_id']}"
                f" :: label={record['scene_label']}"
                f" :: frames={record['start_frame']}-{record['end_frame']}"
                f" :: duration={record['duration_frames']}"
                f" :: seconds={record['start_seconds']}-{record['end_seconds']}"
                f" :: token={record['pacing_token']}"
                f" :: narration={record['narration']}"
            )
        return lines

    def export_schedule_payload(self) -> dict[str, object]:
        return {
            "total_seconds": round(float(self.total_seconds), 3),
            "total_frames": int(self.total_frames),
            "phases": [
                {
                    "role": segment.role,
                    "scene_id": segment.scene_id,
                    "scene_label": segment.scene_label,
                    "start_frame": int(segment.start_frame),
                    "end_frame": int(segment.end_frame),
                    "duration_frames": int(segment.duration_frames),
                    "start_seconds": round(float(segment.start_seconds), 3),
                    "end_seconds": round(float(segment.end_seconds), 3),
                    "duration_seconds": round(float(segment.duration_seconds), 3),
                }
                for segment in self.phases
            ],
            "scenes": self.scene_schedule_records(),
            "log_lines": self.scene_schedule_log_lines(),
        }


_INTRO_HINTS = ("hook", "intro", "opening", "open")
_CONCLUSION_HINTS = ("conclusion", "outro", "ending", "end", "cta")


def _scene_label(scene_id: str) -> str:
    normalized = re.sub(r"^scene[_-]*\d+[_-]*", "", scene_id, flags=re.IGNORECASE)
    label = normalized.replace("_", " ").replace("-", " ").strip()
    return label.title() if label else scene_id


def _classify_scene_role(scene_id: str, index: int, total: int) -> str:
    normalized = scene_id.lower()
    if any(token in normalized for token in _INTRO_HINTS):
        return "intro"
    if any(token in normalized for token in _CONCLUSION_HINTS):
        return "conclusion"
    if index == 0:
        return "intro"
    if index == total - 1:
        return "conclusion"
    return "main"


def _build_phase_segment(role: str, scene_segments: list[TimelineSegment], total_frames: int) -> TimelineSegment:
    if not scene_segments:
        return TimelineSegment(role=role, end_frame=total_frames)
    first_segment = scene_segments[0]
    start_seconds = scene_segments[0].start_seconds
    end_seconds = scene_segments[-1].end_seconds
    start_frame = scene_segments[0].start_frame
    end_frame = scene_segments[-1].end_frame
    return TimelineSegment(
        role=role,
        scene_id=first_segment.scene_id,
        scene_label=first_segment.scene_label,
        scene_ids=[scene_id for seg in scene_segments for scene_id in seg.scene_ids],
        narration=first_segment.narration,
        visual_prompt=first_segment.visual_prompt,
        mood=first_segment.mood,
        pacing_token=first_segment.pacing_token,
        start_seconds=start_seconds,
        end_seconds=end_seconds,
        duration_seconds=max(0.0, end_seconds - start_seconds),
        start_frame=start_frame,
        end_frame=end_frame,
        duration_frames=max(0, end_frame - start_frame),
    )


def build_render_timeline(screenplay: Screenplay, total_secs: int | float, fps: int) -> RenderTimeline:
    total_seconds = max(float(total_secs), 1.0)
    total_frames = max(1, int(round(total_seconds * fps)))
    scenes = screenplay.scenes or []
    if not scenes:
        intro = TimelineSegment(role="intro", start_seconds=0.0, end_seconds=total_seconds, duration_seconds=total_seconds, start_frame=0, end_frame=total_frames, duration_frames=total_frames)
        return RenderTimeline(total_seconds=total_seconds, total_frames=total_frames, phases=[intro], scenes=[intro])

    raw_weights = [max(float(scene.duration_est), 0.1) for scene in scenes]
    total_weight = sum(raw_weights) or float(len(scenes))

    scene_segments: list[TimelineSegment] = []
    cursor_seconds = 0.0
    cursor_frame = 0
    for index, (scene, weight) in enumerate(zip(scenes, raw_weights, strict=True)):
        duration_seconds = total_seconds * (weight / total_weight)
        if index == len(scenes) - 1:
            end_seconds = total_seconds
            end_frame = total_frames
        else:
            end_seconds = min(total_seconds, cursor_seconds + duration_seconds)
            end_frame = min(total_frames, int(round(end_seconds * fps)))
            if end_frame <= cursor_frame:
                end_frame = min(total_frames, cursor_frame + 1)
                end_seconds = end_frame / fps

        role = _classify_scene_role(scene.id, index, len(scenes))
        segment = TimelineSegment(
            role=role,
            scene_id=scene.id,
            scene_label=_scene_label(scene.id),
            scene_ids=[scene.id],
            narration=scene.narration,
            visual_prompt=scene.visual_prompt,
            mood=scene.mood.value,
            pacing_token=resolve_scene_pacing_token(role, scene.id, scene.mood.value),
            start_seconds=cursor_seconds,
            end_seconds=end_seconds,
            duration_seconds=max(0.0, end_seconds - cursor_seconds),
            start_frame=cursor_frame,
            end_frame=end_frame,
            duration_frames=max(0, end_frame - cursor_frame),
        )
        scene_segments.append(segment)
        cursor_seconds = end_seconds
        cursor_frame = end_frame

    intro_segments = [seg for seg in scene_segments if seg.role == "intro"]
    main_segments = [seg for seg in scene_segments if seg.role == "main"]
    conclusion_segments = [seg for seg in scene_segments if seg.role == "conclusion"]

    if not main_segments and len(scene_segments) >= 2:
        middle = scene_segments[1:-1]
        if middle:
            main_segments = middle
        elif len(scene_segments) == 2:
            main_segments = [scene_segments[0]]

    phases = [
        _build_phase_segment("intro", intro_segments or scene_segments[:1], total_frames),
        _build_phase_segment("main", main_segments or scene_segments[1:-1] or scene_segments[:1], total_frames),
        _build_phase_segment("conclusion", conclusion_segments or scene_segments[-1:], total_frames),
    ]

    intro_phase, main_phase, conclusion_phase = phases
    if main_phase.start_frame < intro_phase.end_frame:
        main_phase.start_frame = intro_phase.end_frame
        main_phase.start_seconds = intro_phase.end_seconds
    if conclusion_phase.start_frame < main_phase.end_frame:
        conclusion_phase.start_frame = main_phase.end_frame
        conclusion_phase.start_seconds = main_phase.end_seconds
    conclusion_phase.end_frame = total_frames
    conclusion_phase.end_seconds = total_seconds
    main_phase.end_frame = max(main_phase.start_frame + 1, min(main_phase.end_frame, conclusion_phase.start_frame))
    main_phase.end_seconds = main_phase.end_frame / fps
    intro_phase.end_frame = max(intro_phase.start_frame + 1, min(intro_phase.end_frame, main_phase.start_frame))
    intro_phase.end_seconds = intro_phase.end_frame / fps
    intro_phase.duration_frames = intro_phase.end_frame - intro_phase.start_frame
    intro_phase.duration_seconds = intro_phase.end_seconds - intro_phase.start_seconds
    main_phase.duration_frames = main_phase.end_frame - main_phase.start_frame
    main_phase.duration_seconds = main_phase.end_seconds - main_phase.start_seconds
    conclusion_phase.duration_frames = conclusion_phase.end_frame - conclusion_phase.start_frame
    conclusion_phase.duration_seconds = conclusion_phase.end_seconds - conclusion_phase.start_seconds

    return RenderTimeline(
        total_seconds=total_seconds,
        total_frames=total_frames,
        phases=phases,
        scenes=scene_segments,
    )

