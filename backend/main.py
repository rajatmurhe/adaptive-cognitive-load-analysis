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

from backend.cognitive_engine import CognitiveEngine

from analysis.analysis_service import (
    generate_report_for_session,
    generate_latest_report
)


# ============================================================
# FASTAPI
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
# STATIC OUTPUTS
# ============================================================

app.mount(
    "/outputs",
    StaticFiles(
        directory=OUTPUT_DIR
    ),
    name="outputs"
)


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
# FALLBACK REPORT ENDPOINT
# ============================================================

@app.get("/report/latest")
async def latest_report():

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

        pdf_path = generate_latest_report()

        if not pdf_path:
            raise RuntimeError(
                "Report generation returned no PDF path."
            )

        pdf_path = os.fspath(pdf_path)

        if not os.path.isfile(pdf_path):
            raise FileNotFoundError(
                f"Generated PDF does not exist: {pdf_path}"
            )

        filename = os.path.basename(
            pdf_path
        )

        return {
            "status": "success",
            "pdf": f"/outputs/{filename}",
            "filename": filename,
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
            "status": "error",
            "message": str(exc)
        }


# ============================================================
# WEBSOCKET
# ============================================================

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket
):

    await websocket.accept()

    engine = CognitiveEngine()

    session_id = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    session_path = os.path.join(
        DATA_DIR,
        f"session_{session_id}.csv"
    )

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

    session_finished = False

    print()
    print(
        "=========================================="
    )
    print(
        f"SESSION STARTED: {session_id}"
    )
    print(
        f"SESSION FILE: {session_path}"
    )
    print(
        "=========================================="
    )

    try:

        while True:

            data = await websocket.receive_json()

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
                    "type": "reset_ack"
                })

                continue

            # ------------------------------------------------
            # FINISH SESSION
            # ------------------------------------------------

            if message_type == "end_session":

                print(
                    f"END SESSION REQUEST: {session_id}"
                )

                # Close CSV before analysis.
                csv_file.flush()
                csv_file.close()

                session_finished = True

                # --------------------------------------------
                # Generate report for exact session
                # --------------------------------------------

                try:

                    print(
                        "Generating report for exact session..."
                    )

                    pdf_path = (
                        generate_report_for_session(
                            session_path
                        )
                    )

                    pdf_filename = (
                        os.path.basename(
                            pdf_path
                        )
                    )

                    print(
                        f"REPORT READY: {pdf_path}"
                    )

                    await websocket.send_json({

                        "type":
                            "report_ready",

                        "pdf":
                            f"/outputs/{pdf_filename}",

                        "filename":
                            pdf_filename
                    })

                except Exception as report_error:

                    print(
                        "REPORT GENERATION FAILED"
                    )

                    print(
                        traceback.format_exc()
                    )

                    await websocket.send_json({

                        "type":
                            "report_error",

                        "message":
                            str(report_error)
                    })

                # --------------------------------------------
                # Close websocket after report response
                # --------------------------------------------

                await websocket.close()

                break

            # ------------------------------------------------
            # IGNORE UNKNOWN MESSAGES
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
            # COGNITIVE ENGINE
            # ------------------------------------------------

            result = engine.process(
                blink_rate=blink_rate,
                gaze_deviation=gaze_deviation,
                head_jitter=head_jitter
            )

            # ------------------------------------------------
            # SAVE CALIBRATION
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

            # ------------------------------------------------
            # SAVE LIVE DATA
            # ------------------------------------------------

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
            # SEND LIVE RESULT
            # ------------------------------------------------

            await websocket.send_json({

                "type":
                    "analysis",

                "data":
                    result
            })

    except WebSocketDisconnect:

        print(
            f"WEBSOCKET DISCONNECTED: {session_id}"
        )

    except Exception:

        print(
            f"WEBSOCKET ERROR: {session_id}"
        )

        print(
            traceback.format_exc()
        )

    finally:

        # ----------------------------------------------------
        # Close file if it hasn't already been closed
        # ----------------------------------------------------

        if not session_finished:

            try:

                csv_file.flush()
                csv_file.close()

            except Exception:

                pass

        print(
            f"SESSION CLOSED: {session_id}"
        )
