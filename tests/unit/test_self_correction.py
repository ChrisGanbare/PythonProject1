"""Tests for Self-Correction feedback loop — error classification, diagnosis, runner."""

from __future__ import annotations

import pytest

from shared.render.core.self_correction import (
    CorrectionRecord,
    CorrectionReport,
    ErrorCategory,
    RenderDiagnosis,
    SelfCorrectingRunner,
    classify_error,
)


class TestErrorClassification:
    """classify_error should map stderr patterns to correct categories."""

    @pytest.mark.parametrize(
        "stderr, expected_category",
        [
            ("findfont: Font family ['Comic Sans'] not found", ErrorCategory.FONT_NOT_FOUND),
            ("FontNotFoundError: cannot find font 'xyz'", ErrorCategory.FONT_NOT_FOUND),
            ("ModuleNotFoundError: No module named 'plotly'", ErrorCategory.MISSING_DEPENDENCY),
            ("ImportError: cannot import name 'foo'", ErrorCategory.MISSING_DEPENDENCY),
            ("Error while encoding frame 42", ErrorCategory.FFMPEG_ERROR),
            ("ffmpeg error: pipe: broken", ErrorCategory.FFMPEG_ERROR),
            ("MemoryError: unable to allocate 4 GiB", ErrorCategory.OUT_OF_MEMORY),
            ("killed by signal 9 (OOM)", ErrorCategory.OUT_OF_MEMORY),
            ("TimeoutExpired: cmd timed out after 600s", ErrorCategory.TIMEOUT),
            ("ValueError: x out of range", ErrorCategory.INVALID_PARAMETER),
            ("FileNotFoundError: No such file: 'data.csv'", ErrorCategory.FILE_NOT_FOUND),
            ("ManimError: Scene 'Foo' not found", ErrorCategory.MANIM_SCENE_ERROR),
            ("cairo error: invalid surface", ErrorCategory.MANIM_SCENE_ERROR),
            ("matplotlib error in tight_layout", ErrorCategory.MATPLOTLIB_ERROR),
            ("something completely unknown happened", ErrorCategory.UNKNOWN),
        ],
    )
    def test_classify_stderr(self, stderr: str, expected_category: ErrorCategory):
        diagnosis = classify_error(stderr)
        assert diagnosis.category == expected_category

    def test_classify_with_exception(self):
        exc = ModuleNotFoundError("No module named 'manim'")
        diagnosis = classify_error("", exception=exc)
        assert diagnosis.category == ErrorCategory.MISSING_DEPENDENCY

    def test_unknown_fallback(self):
        diagnosis = classify_error("all good, no errors at all... jk")
        assert diagnosis.category == ErrorCategory.UNKNOWN
        assert not diagnosis.auto_correctable


class TestRenderDiagnosis:
    def test_auto_correctable_font(self):
        diag = classify_error("findfont: Font family ['Missing'] not found")
        assert diag.auto_correctable is True
        assert "VIDEO_FONT_FAMILY" in diag.env_patches

    def test_auto_correctable_oom(self):
        diag = classify_error("MemoryError: unable to allocate")
        assert diag.auto_correctable is True
        assert diag.param_patches.get("quality") == "preview"

    def test_not_auto_correctable_missing_dep(self):
        diag = classify_error("ModuleNotFoundError: No module named 'foo'")
        assert diag.auto_correctable is False

    def test_stderr_truncated(self):
        long_stderr = "x" * 5000
        diag = classify_error(long_stderr)
        assert len(diag.raw_stderr) <= 2000


class TestCorrectionReport:
    def test_empty_report(self):
        report = CorrectionReport()
        assert report.total_attempts == 0
        assert report.final_success is False

    def test_report_to_dict(self):
        diag = RenderDiagnosis(
            category=ErrorCategory.FONT_NOT_FOUND,
            message="font missing",
            suggested_fix="use fallback",
            auto_correctable=True,
        )
        record = CorrectionRecord(
            attempt=1, diagnosis=diag, applied_patches={"font": "Noto"}, succeeded=True
        )
        report = CorrectionReport(records=[record], final_success=True)
        d = report.to_dict()
        assert d["total_attempts"] == 1
        assert d["final_success"] is True
        assert d["records"][0]["category"] == "font_not_found"

    def test_save_and_load(self, tmp_path):
        diag = RenderDiagnosis(
            category=ErrorCategory.TIMEOUT,
            message="timed out",
            suggested_fix="lower quality",
            auto_correctable=True,
        )
        report = CorrectionReport(
            records=[CorrectionRecord(attempt=1, diagnosis=diag, applied_patches={}, succeeded=False)],
        )
        path = tmp_path / "correction.json"
        report.save(path)
        assert path.exists()
        import json

        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["total_attempts"] == 1


class TestSelfCorrectingRunner:
    def test_success_on_first_try(self):
        def ok_fn(x=1):
            return x * 2

        runner = SelfCorrectingRunner(max_retries=2)
        result, report = runner.run(ok_fn, {"x": 5})
        assert result == 10
        assert report.final_success is True
        assert report.total_attempts == 0  # no failures recorded

    def test_retry_on_auto_correctable(self):
        call_count = 0

        def flaky_fn():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("findfont: Font family not found")
            return "ok"

        runner = SelfCorrectingRunner(max_retries=2, backoff_base=0.01)
        result, report = runner.run(
            flaky_fn,
            error_extractor=lambda e: str(e),
        )
        assert result == "ok"
        assert report.final_success is True
        assert call_count == 2

    def test_gives_up_on_non_correctable(self):
        def bad_fn():
            raise RuntimeError("ModuleNotFoundError: No module named 'nonexistent'")

        runner = SelfCorrectingRunner(max_retries=2, backoff_base=0.01)
        with pytest.raises(RuntimeError, match="ModuleNotFoundError"):
            runner.run(bad_fn, error_extractor=lambda e: str(e))

    def test_exhausts_retries(self):
        def always_oom(**kwargs):
            raise MemoryError("out of memory")

        runner = SelfCorrectingRunner(max_retries=2, backoff_base=0.01)
        with pytest.raises(MemoryError):
            runner.run(always_oom, error_extractor=lambda e: str(e))

    def test_on_retry_callback(self):
        attempts_seen = []

        def flaky(**kwargs):
            if len(attempts_seen) == 0:
                raise RuntimeError("MemoryError: OOM")
            return "recovered"

        def on_retry(attempt, diag):
            attempts_seen.append(attempt)

        runner = SelfCorrectingRunner(max_retries=2, backoff_base=0.01)
        result, _ = runner.run(
            flaky,
            error_extractor=lambda e: str(e),
            on_retry=on_retry,
        )
        assert result == "recovered"
        assert len(attempts_seen) == 1
