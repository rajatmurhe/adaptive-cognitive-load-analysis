import csv
import os
import sys
import time
import traceback
from datetime import datetime

from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect
)

from fastapi.middleware.cors import (
    CORSMiddleware
)

from fastapi.staticfiles import (
    StaticFiles
)


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(
        0,
        PROJECT_ROOT
    )


# ============================================================
# IMPORTS
# ============================================================

from backend.cognitive_engine import (
    CognitiveEngine
)

from analysis.analysis_service import (
    generate_report_for_session,
    generate_latest_report
)


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="Adaptive Cognitive Vision API",
    description="Real-time behavioral analysis backend",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ============================================================
# DIRECTORIES
# ============================================================

DATA_DIR = os.path.join(
    PROJECT_ROOT,
    "sessions"
)

OUTPUT_DIR = os.path.join(
    PROJECT_ROOT,
    "analysis",
    "outputs"
)

os.makedirs(
    DATA_DIR,
    exist_ok=True
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# ============================================================
# STATIC REPORT FILES
# ============================================================

app.mount(
    "/outputs",
    StaticFiles(
        directory=OUTPUT_DIR
    ),
    name="outputs"
)


# ============================================================
# CURRENT SESSION STATE
# ============================================================

LATEST_SESSION_PATH = None
LATEST_REPORT_PATH = None


# ============================================================
# ROOT
# ============================================================

@app.get("/")
async def root():

    return {
        "status": "online",
        "service": "Adaptive Cognitive Vision API"
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
async def health():

    return {
        "status": "healthy"
    }


# ============================================================
# LATEST REPORT
# ============================================================

@app.get("/report/latest")
async def latest_report():

    global LATEST_SESSION_PATH
    global LATEST_REPORT_PATH

    try:

        print()
        print(
            "=========================================="
        )

        print(
            "REPORT REQUEST RECEIVED"
        )

        print(
            "=========================================="
        )

        # ----------------------------------------------------
        # If we already generated the report, use it
        # ----------------------------------------------------

        if (
            LATEST_REPORT_PATH
            and os.path.isfile(
                LATEST_REPORT_PATH
            )
        ):

            pdf_path = (
                LATEST_REPORT_PATH
            )

            print(
                f"Using existing report: {pdf_path}"
            )

        else:

            # ------------------------------------------------
            # Prefer exact session from current connection
            # ------------------------------------------------

            if (
                LATEST_SESSION_PATH
                and os.path.isfile(
                    LATEST_SESSION_PATH
                )
            ):

                session_path = (
                    LATEST_SESSION_PATH
                )

                print(
                    f"Using current session: {session_path}"
                )

            else:

                # --------------------------------------------
                # Fallback for server restart
                # --------------------------------------------

                session_files = [
                    os.path.join(
                        DATA_DIR,
                        filename
                    )

                    for filename
                    in os.listdir(DATA_DIR)

                    if (
                        filename.startswith(
                            "session_"
                        )
                        and filename.endswith(
                            ".csv"
                        )
                    )
                ]

                if not session_files:

                    raise FileNotFoundError(
                        "No completed session CSV is available."
                    )

                session_path = max(
                    session_files,
                    key=os.path.getmtime
                )

                print(
                    f"Using fallback session: {session_path}"
                )

            # ------------------------------------------------
            # Generate PDF
            # ------------------------------------------------

            pdf_path = (
                generate_report_for_session(
                    session_path
                )
            )

            LATEST_REPORT_PATH = (
                pdf_path
            )

        # ----------------------------------------------------
        # Validate PDF
        # ----------------------------------------------------

        if not pdf_path:

            raise RuntimeError(
                "Report generation returned no PDF path."
            )

        pdf_path = os.fspath(
            pdf_path
        )

        if not os.path.isfile(
            pdf_path
        ):

            raise FileNotFoundError(
                f"PDF not found: {pdf_path}"
            )

        filename = os.path.basename(
            pdf_path
        )

        print(
            f"PDF ready: {pdf_path}"
        )

        return {

            "status":
                "success",

            "pdf":
                f"/outputs/{filename}",

            "filename":
                filename,

            "message":
                "Latest session report generated successfully."
        }

    except Exception as exc:

        print()
        print(
            "REPORT GENERATION ERROR"
        )

        print(
            traceback.format_exc()
        )

        return {

            "status":
                "error",

            "message":
                str(exc)
        }


# ============================================================
# WEBSOCKET
# ============================================================

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket
):

    global LATEST_SESSION_PATH
    global LATEST_REPORT_PATH

    await websocket.accept()

    engine = CognitiveEngine()

    session_id = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    session_path = os.path.join(
        DATA_DIR,
        f"session_{session_id}.csv"
    )

    # --------------------------------------------------------
    # This is now the current session
    # --------------------------------------------------------

    LATEST_SESSION_PATH = (
        session_path
    )

    LATEST_REPORT_PATH = None

    # --------------------------------------------------------
    # Open CSV
    # --------------------------------------------------------

    csv_file = open(
        session_path,
        "w",
        newline=""
    )

    writer = csv.writer(
        csv_file
    )

    writer.writerow([
        "Time",
        "BlinkRate",
        "Stress",
        "Distraction",
        "CognitiveLoad",
        "Phase",
        "Stability",
        "AttentionSpan"
    ])

    csv_file.flush()

    print(
        f"Session started: {session_path}"
    )

    try:

        while True:

            data = (
                await websocket.receive_json()
            )

            message_type = data.get(
                "type",
                "features"
            )

            # ------------------------------------------------
            # RESET
            # ------------------------------------------------

            if message_type == "reset":

                engine.reset()

                writer.writerow([
                    time.time(),
                    0,
                    "",
                    "",
                    "",
                    "Calibrating",
                    "",
                    ""
                ])

                csv_file.flush()

                await websocket.send_json({
                    "type":
                        "reset_ack"
                })

                continue

            # ------------------------------------------------
            # IGNORE UNKNOWN
            # ------------------------------------------------

            if message_type != "features":

                continue

            # ------------------------------------------------
            # FEATURES
            # ------------------------------------------------

            blink_rate = float(
                data.get(
                    "blink_rate",
                    0
                )
            )

            gaze_deviation = float(
                data.get(
                    "gaze_deviation",
                    0
                )
            )

            head_jitter = float(
                data.get(
                    "head_jitter",
                    0
                )
            )

            # ------------------------------------------------
            # ENGINE
            # ------------------------------------------------

            result = engine.process(
                blink_rate=blink_rate,
                gaze_deviation=gaze_deviation,
                head_jitter=head_jitter
            )

            # ------------------------------------------------
            # SAVE
            # ------------------------------------------------

            if result["cli"] is None:

                writer.writerow([
                    time.time(),
                    blink_rate,
                    "",
                    "",
                    "",
                    "Calibrating",
                    "",
                    ""
                ])

            else:

                writer.writerow([
                    time.time(),
                    result["blink_rate"],
                    result["stress"],
                    result["distraction"],
                    result["cli"],
                    result["phase"],
                    result["stability"],
                    result["attention_span"]
                ])

            csv_file.flush()

            # ------------------------------------------------
            # SEND RESULT
            # ------------------------------------------------

            await websocket.send_json({

                "type":
                    "analysis",

                "data":
                    result
            })

    except WebSocketDisconnect:

        print(
            f"Session disconnected: {session_id}"
        )

    except Exception:

        print(
            "WEBSOCKET ERROR"
        )

        print(
            traceback.format_exc()
        )

    finally:

        # ----------------------------------------------------
        # CLOSE SESSION FILE FIRST
        # ----------------------------------------------------

        try:

            csv_file.flush()

            csv_file.close()

        except Exception:

            pass

        print(
            f"Session saved: {session_path}"
        )

        # ----------------------------------------------------
        # Generate report for THIS exact session
        # ----------------------------------------------------

        try:

            if os.path.isfile(
                session_path
            ):

                print(
                    "Generating session report..."
                )

                LATEST_REPORT_PATH = (
                    generate_report_for_session(
                        session_path
                    )
                )

                print(
                    f"Session report ready: {LATEST_REPORT_PATH}"
                )

        except Exception:

            print(
                "AUTOMATIC REPORT GENERATION ERROR"
            )

            print(
                traceback.format_exc()
            )
