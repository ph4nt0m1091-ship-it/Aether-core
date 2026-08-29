import json
import re

from datetime import datetime
from pathlib import Path


class FailureMemory:
    """
    Persistent operational failure memory for Aether.

    This store is deliberately separate from personal
    memory. It records only execution/recovery patterns
    needed to understand recurring operational failures.

    It does not persist prompts, passwords, tokens, API
    keys, authorization values, or arbitrary workflow data.
    """

    def __init__(
        self,
        path="storage/failure_memory.json"
    ):

        self.path = Path(
            path
        )

        self.max_events = 200
        self.max_recoveries = 100

    # ---------------------------------
    # LOAD
    # ---------------------------------

    def load(self):

        if not self.path.exists():

            return self._empty()

        try:

            with self.path.open(
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(
                    file
                )

        except (
            OSError,
            json.JSONDecodeError
        ):

            return self._empty()

        if not isinstance(
            data,
            dict
        ):

            return self._empty()

        data.setdefault(
            "version",
            1
        )

        data.setdefault(
            "patterns",
            {}
        )

        data.setdefault(
            "events",
            []
        )

        data.setdefault(
            "recoveries",
            []
        )

        return data

    # ---------------------------------
    # SAVE
    # ---------------------------------

    def save(
        self,
        data
    ):

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with self.path.open(
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=4
            )

    # ---------------------------------
    # RECORD FAILURE
    # ---------------------------------

    def record_failure(
        self,
        workflow_id,
        step,
        result,
        phase="initial"
    ):

        data = self.load()

        event = self._failure_event(
            workflow_id,
            step,
            result,
            phase
        )

        signature = event[
            "signature"
        ]

        patterns = data[
            "patterns"
        ]

        pattern = patterns.get(
            signature
        )

        if not isinstance(
            pattern,
            dict
        ):

            pattern = {
                "signature": signature,
                "count": 0,
                "first_seen": event[
                    "timestamp"
                ],
                "last_seen": event[
                    "timestamp"
                ],
                "type": event[
                    "type"
                ],
                "action": event[
                    "action"
                ],
                "target": event[
                    "target"
                ],
                "provider": event[
                    "provider"
                ],
                "capability": event[
                    "capability"
                ],
                "model": event[
                    "model"
                ],
                "failure_type": event[
                    "failure_type"
                ],
                "error": event[
                    "error"
                ]
            }

        pattern[
            "count"
        ] = int(
            pattern.get(
                "count",
                0
            )
        ) + 1

        pattern[
            "last_seen"
        ] = event[
            "timestamp"
        ]

        pattern[
            "last_phase"
        ] = phase

        patterns[
            signature
        ] = pattern

        events = data[
            "events"
        ]

        events.append(
            event
        )

        data[
            "events"
        ] = events[
            -self.max_events:
        ]

        self.save(
            data
        )

        return dict(
            pattern
        )

    # ---------------------------------
    # RECORD RECOVERY
    # ---------------------------------

    def record_recovery(
        self,
        workflow_id,
        step,
        recovery,
        result
    ):

        data = self.load()

        event = {
            "timestamp": self._timestamp(),
            "workflow_id": str(
                workflow_id or ""
            ),
            "type": str(
                step.get(
                    "type",
                    ""
                )
                if isinstance(
                    step,
                    dict
                )
                else ""
            ),
            "action": str(
                step.get(
                    "action",
                    ""
                )
                if isinstance(
                    step,
                    dict
                )
                else ""
            ),
            "target": str(
                step.get(
                    "target",
                    ""
                )
                if isinstance(
                    step,
                    dict
                )
                else ""
            ),
            "capability": str(
                recovery.get(
                    "capability",
                    ""
                )
                if isinstance(
                    recovery,
                    dict
                )
                else ""
            ),
            "retry_succeeded": bool(
                recovery.get(
                    "retry_succeeded",
                    False
                )
                if isinstance(
                    recovery,
                    dict
                )
                else False
            ),
            "fallback_attempted": bool(
                recovery.get(
                    "fallback_attempted",
                    False
                )
                if isinstance(
                    recovery,
                    dict
                )
                else False
            ),
            "fallback_succeeded": bool(
                recovery.get(
                    "fallback_succeeded",
                    False
                )
                if isinstance(
                    recovery,
                    dict
                )
                else False
            ),
            "fallback_from_model": str(
                recovery.get(
                    "fallback_from_model",
                    ""
                )
                if isinstance(
                    recovery,
                    dict
                )
                else ""
            ),
            "fallback_model": str(
                recovery.get(
                    "fallback_model",
                    ""
                )
                if isinstance(
                    recovery,
                    dict
                )
                else ""
            ),
            "provider": str(
                result.get(
                    "provider",
                    ""
                )
                if isinstance(
                    result,
                    dict
                )
                else ""
            )
        }

        recoveries = data[
            "recoveries"
        ]

        recoveries.append(
            event
        )

        data[
            "recoveries"
        ] = recoveries[
            -self.max_recoveries:
        ]

        self.save(
            data
        )

        return event

    # ---------------------------------
    # RECENT FAILURES
    # ---------------------------------

    def recent_failures(
        self,
        limit=20
    ):

        data = self.load()

        return data.get(
            "events",
            []
        )[
            -limit:
        ]

    # ---------------------------------
    # RECENT RECOVERIES
    # ---------------------------------

    def recent_recoveries(
        self,
        limit=20
    ):

        data = self.load()

        return data.get(
            "recoveries",
            []
        )[
            -limit:
        ]

    # ---------------------------------
    # REPEATED PATTERNS
    # ---------------------------------

    def repeated_patterns(
        self,
        minimum_count=2,
        limit=10
    ):

        data = self.load()

        patterns = [
            item
            for item in data.get(
                "patterns",
                {}
            ).values()
            if isinstance(
                item,
                dict
            )
            and int(
                item.get(
                    "count",
                    0
                )
            ) >= minimum_count
        ]

        patterns.sort(
            key=lambda item: (
                int(
                    item.get(
                        "count",
                        0
                    )
                ),
                item.get(
                    "last_seen",
                    ""
                )
            ),
            reverse=True
        )

        return patterns[
            :limit
        ]

    # ---------------------------------
    # ADAPTIVE RECOVERY EVIDENCE
    # ---------------------------------

    def adaptive_recovery_evidence(
        self,
        step,
        result
    ):
        """
        Return conservative evidence that may justify
        skipping one redundant same-model retry.

        Evidence is observational only. This method does
        not choose a provider, execute anything, change
        permissions, or introduce a cloud route.
        """

        if not isinstance(
            step,
            dict
        ):

            return {
                "repeated_failure_count": 0,
                "preferred_fallback_model": None,
                "preferred_fallback_successes": 0,
                "fallback_successes": {}
            }

        if not isinstance(
            result,
            dict
        ):

            result = {}

        event = self._failure_event(
            "",
            step,
            result,
            phase="initial"
        )

        data = self.load()

        pattern = (
            data.get(
                "patterns",
                {}
            )
            .get(
                event[
                    "signature"
                ],
                {}
            )
        )

        repeated_failure_count = int(
            pattern.get(
                "count",
                0
            )
            if isinstance(
                pattern,
                dict
            )
            else 0
        )

        step_data = step.get(
            "data",
            {}
        )

        if not isinstance(
            step_data,
            dict
        ):

            step_data = {}

        current_model = str(
            result.get(
                "model",
                step_data.get(
                    "model",
                    ""
                )
            )
            or ""
        ).strip()

        action = str(
            step.get(
                "action",
                ""
            )
            or ""
        )

        target = str(
            step.get(
                "target",
                ""
            )
            or ""
        )

        capability = str(
            result.get(
                "capability",
                action
            )
            or ""
        )

        successes = {}

        for recovery in data.get(
            "recoveries",
            []
        ):

            if not isinstance(
                recovery,
                dict
            ):

                continue

            if not recovery.get(
                "fallback_succeeded",
                False
            ):

                continue

            if str(
                recovery.get(
                    "action",
                    ""
                )
                or ""
            ) != action:

                continue

            if str(
                recovery.get(
                    "target",
                    ""
                )
                or ""
            ) != target:

                continue

            if str(
                recovery.get(
                    "capability",
                    ""
                )
                or ""
            ) != capability:

                continue

            if str(
                recovery.get(
                    "fallback_from_model",
                    ""
                )
                or ""
            ) != current_model:

                continue

            fallback_model = str(
                recovery.get(
                    "fallback_model",
                    ""
                )
                or ""
            ).strip()

            if not fallback_model:

                continue

            successes[
                fallback_model
            ] = (
                successes.get(
                    fallback_model,
                    0
                )
                + 1
            )

        preferred_model = None
        preferred_successes = 0

        for model, count in successes.items():

            if count > preferred_successes:

                preferred_model = model
                preferred_successes = count

        return {
            "repeated_failure_count": (
                repeated_failure_count
            ),
            "preferred_fallback_model": (
                preferred_model
            ),
            "preferred_fallback_successes": (
                preferred_successes
            ),
            "fallback_successes": successes,
            "current_model": current_model,
            "action": action,
            "target": target,
            "capability": capability
        }

    # ---------------------------------
    # INTERNALS
    # ---------------------------------

    def _failure_event(
        self,
        workflow_id,
        step,
        result,
        phase
    ):

        if not isinstance(
            step,
            dict
        ):

            step = {}

        if not isinstance(
            result,
            dict
        ):

            result = {}

        raw_data = step.get(
            "data",
            {}
        )

        if not isinstance(
            raw_data,
            dict
        ):

            raw_data = {}

        error = self._clean_error(
            result.get(
                "error",
                ""
            )
        )

        event = {
            "timestamp": self._timestamp(),
            "workflow_id": str(
                workflow_id or ""
            ),
            "phase": str(
                phase or "initial"
            ),
            "type": str(
                step.get(
                    "type",
                    ""
                )
            ),
            "action": str(
                step.get(
                    "action",
                    ""
                )
            ),
            "target": str(
                step.get(
                    "target",
                    ""
                )
                or ""
            ),
            "provider": str(
                result.get(
                    "provider",
                    ""
                )
                or ""
            ),
            "capability": str(
                result.get(
                    "capability",
                    step.get(
                        "action",
                        ""
                    )
                )
                or ""
            ),
            "model": str(
                result.get(
                    "model",
                    raw_data.get(
                        "model",
                        ""
                    )
                )
                or ""
            ),
            "failure_type": str(
                result.get(
                    "failure_type",
                    "unknown"
                )
                or "unknown"
            ),
            "error": error
        }

        event[
            "signature"
        ] = self._signature(
            event
        )

        return event

    def _signature(
        self,
        event
    ):

        error_key = re.sub(
            r"\s+",
            " ",
            str(
                event.get(
                    "error",
                    ""
                )
            ).lower()
        ).strip()

        pieces = (
            event.get(
                "type",
                ""
            ),
            event.get(
                "action",
                ""
            ),
            event.get(
                "target",
                ""
            ),
            event.get(
                "provider",
                ""
            ),
            event.get(
                "capability",
                ""
            ),
            event.get(
                "model",
                ""
            ),
            event.get(
                "failure_type",
                ""
            ),
            error_key
        )

        return "|".join(
            str(
                piece or ""
            ).lower()
            for piece in pieces
        )

    def _clean_error(
        self,
        error
    ):

        text = str(
            error or ""
        ).strip()

        # Keep operational failure text useful while
        # avoiding accidentally persisting obvious
        # credential-like values.
        text = re.sub(
            r"(?i)(api[_ -]?key|token|password|authorization)"
            r"\s*[:=]\s*\S+",
            r"\1=[REDACTED]",
            text
        )

        if len(
            text
        ) > 500:

            text = text[
                :500
            ]

        return text

    def _empty(
        self
    ):

        return {
            "version": 1,
            "patterns": {},
            "events": [],
            "recoveries": []
        }

    def _timestamp(
        self
    ):

        return datetime.now().isoformat(
            timespec="seconds"
        )
