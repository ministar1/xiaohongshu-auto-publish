from __future__ import annotations

import pytest

from xiaohongshu_auto_publish.errors import StateError
from xiaohongshu_auto_publish.models import TaskStatus
from xiaohongshu_auto_publish.orchestration.states import TRANSITIONS, Trigger, retry_target, validate_transition


def test_transition_matrix_allows_declared_transitions() -> None:
    for transition in TRANSITIONS:
        assert validate_transition(transition.current, transition.trigger) == transition


def test_transition_matrix_rejects_illegal_trigger() -> None:
    with pytest.raises(StateError):
        validate_transition(TaskStatus.CREATED, Trigger.PUBLISH_DONE)


def test_retry_target_uses_last_failed_stage() -> None:
    assert retry_target("package") == TaskStatus.PACKAGE_READY
