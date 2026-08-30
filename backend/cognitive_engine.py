import time
from collections import deque
from statistics import mean, pstdev


class CognitiveEngine:
    """
    Real-time cognitive-state engine.

    Receives behavioral features from the browser:
        - blink_rate
        - gaze_deviation
        - head_jitter

    Performs:
        - baseline calibration
        - normalization
        - weighted CLI calculation
        - temporal phase detection
        - stability estimation
        - attention-span tracking
    """

    CALIBRATION_TIME = 60

    CLI_WINDOW = 30
    STABILITY_WINDOW = 30

    def __init__(self):
        self.reset()

    def reset(self):
        self.session_start = time.time()

        self.calibrating = True

        self.blink_samples = []
        self.gaze_samples = []
        self.jitter_samples = []

        self.baseline_blink = 1.0
        self.baseline_gaze = 1.0
        self.baseline_jitter = 1.0

        self.cli_history = deque(maxlen=self.CLI_WINDOW)
        self.cli_full_history = []

        self.phase = "Calibrating"

        self.focus_start = None
        self.max_focus_duration = 0.0

        self.latest = {
            "cli": None,
            "phase": "Calibrating",
            "blink_rate": 0.0,
            "gaze_deviation": 0.0,
            "head_jitter": 0.0,
            "stability": 100.0,
            "attention_span": 0.0,
            "fatigue": 0.0,
            "distraction": 0.0,
            "stress": 0.0,
            "calibration_progress": 0.0,
        }

    @staticmethod
    def safe_mean(values):
        return mean(values) if values else 0.0

    @staticmethod
    def clamp(value, low, high):
        return max(low, min(high, value))

    def process(self, blink_rate, gaze_deviation, head_jitter):
        """
        Process one feature packet.
        """

        now = time.time()

        elapsed = now - self.session_start

        # -----------------------------------------------------
        # Calibration
        # -----------------------------------------------------

        if self.calibrating:

            self.blink_samples.append(float(blink_rate))
            self.gaze_samples.append(float(gaze_deviation))
            self.jitter_samples.append(float(head_jitter))

            progress = self.clamp(
                elapsed / self.CALIBRATION_TIME,
                0.0,
                1.0
            )

            self.latest.update({
                "cli": None,
                "phase": "Calibrating",
                "blink_rate": float(blink_rate),
                "gaze_deviation": float(gaze_deviation),
                "head_jitter": float(head_jitter),
                "stability": 100.0,
                "attention_span": 0.0,
                "calibration_progress": progress
            })

            if elapsed >= self.CALIBRATION_TIME:

                self.baseline_blink = (
                    self.safe_mean(self.blink_samples)
                    + 1e-5
                )

                self.baseline_gaze = (
                    self.safe_mean(self.gaze_samples)
                    + 1e-5
                )

                self.baseline_jitter = (
                    self.safe_mean(self.jitter_samples)
                    + 1e-5
                )

                self.calibrating = False

                self.phase = "Warm-up"

            return self.latest.copy()

        # -----------------------------------------------------
        # Normalize behavioral signals
        # -----------------------------------------------------

        fatigue = (
            float(blink_rate)
            / self.baseline_blink
        )

        distraction = (
            float(gaze_deviation)
            / self.baseline_gaze
        )

        stress = (
            float(head_jitter)
            / self.baseline_jitter
        )

        # -----------------------------------------------------
        # Cognitive Load Index
        # Same weighted structure as your project
        # -----------------------------------------------------

        cli = round(
            (
                0.4 * fatigue
                + 0.3 * distraction
                + 0.3 * stress
            ) * 50
        )

        cli = int(
            self.clamp(cli, 0, 100)
        )

        # -----------------------------------------------------
        # Temporal history
        # -----------------------------------------------------

        self.cli_history.append(cli)
        self.cli_full_history.append(cli)

        # -----------------------------------------------------
        # Stability
        # Rolling-window standard deviation
        # -----------------------------------------------------

        recent_cli = self.cli_full_history[
            -self.STABILITY_WINDOW:
        ]

        if len(recent_cli) >= 5:

            std = pstdev(recent_cli)

            stability = self.clamp(
                100 - (std * 2),
                0,
                100
            )

        else:
            stability = 100.0

        # -----------------------------------------------------
        # Phase detection
        # -----------------------------------------------------

        if len(self.cli_history) >= self.CLI_WINDOW:

            avg_cli = mean(self.cli_history)

            if avg_cli < 30:
                self.phase = "Warm-up"

            elif avg_cli < 55:
                self.phase = "Focused"

            elif avg_cli < 75:
                self.phase = "Overload"

            else:
                self.phase = "Fatigue"

        # -----------------------------------------------------
        # Attention span
        # -----------------------------------------------------

        if self.phase == "Focused":

            if self.focus_start is None:
                self.focus_start = now

            current_focus = (
                now - self.focus_start
            )

            self.max_focus_duration = max(
                self.max_focus_duration,
                current_focus
            )

        else:

            self.focus_start = None

        # -----------------------------------------------------
        # Store latest result
        # -----------------------------------------------------

        self.latest = {
            "cli": cli,
            "phase": self.phase,

            "blink_rate": round(
                float(blink_rate), 2
            ),

            "gaze_deviation": round(
                float(gaze_deviation), 4
            ),

            "head_jitter": round(
                float(head_jitter), 6
            ),

            "stability": round(
                stability, 1
            ),

            "attention_span": round(
                self.max_focus_duration, 1
            ),

            "fatigue": round(
                fatigue, 3
            ),

            "distraction": round(
                distraction, 3
            ),

            "stress": round(
                stress, 3
            ),

            "calibration_progress": 1.0
        }

        return self.latest.copy()
