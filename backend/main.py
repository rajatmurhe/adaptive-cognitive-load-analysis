import csv
import os
import sys
import time
import traceback
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from cognitive_engine import CognitiveEngine
from analysis.analysis_service import generate_latest_report


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

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# STATIC OUTPUTS
# ============================================================

app.mount(
    "/outputs",
    StaticFiles(directory=OUTPUT_DIR),
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
# REPORT
# ============================================================

@app.get("/report/latest")
async def latest_report():

    try:

        print(
            "\n=========================================="
        )
        print(
            "REPORT REQUEST RECEIVED"
        )
        print(
            "=========================================="
        )

        print(
            f"Project root: {PROJECT_ROOT}"
        )

        print(
            f"Output directory: {OUTPUT_DIR}"
        )

        # ----------------------------------------------------
        # Generate report
        # ----------------------------------------------------

        pdf_path = generate_latest_report()

        print(
            f"Report generator returned: {pdf_path!r}"
        )

        # ----------------------------------------------------
        # Validate returned path
        # ----------------------------------------------------

        if pdf_path is None:

            raise RuntimeError(
                "Report generator returned None instead of a PDF path."
            )

        pdf_path = os.fspath(pdf_path)

        # ----------------------------------------------------
        # Make sure file exists
        # ----------------------------------------------------

        if not os.path.isfile(pdf_path):

            raise FileNotFoundError(
                f"Generated PDF does not exist: {pdf_path}"
            )

        # ----------------------------------------------------
        # Make sure PDF is inside public output directory
        # ----------------------------------------------------

        absolute_pdf = os.path.abspath(pdf_path)
        absolute_output = os.path.abspath(OUTPUT_DIR)

        if not absolute_pdf.startswith(
            absolute_output + os.sep
        ):

            raise RuntimeError(
                "Generated PDF is outside the public output directory."
            )

        # ----------------------------------------------------
        # URL
        # ----------------------------------------------------

        filename = os.path.basename(
            absolute_pdf
        )

        pdf_url = (
            f"/outputs/{filename}"
        )

        print(
            f"PDF ready: {absolute_pdf}"
        )

        return {
            "status": "success",
            "pdf": pdf_url,
            "filename": filename,
            "message":
                "Latest session report generated successfully."
        }

    except Exception as exc:

        print(
            "\nREPORT GENERATION ERROR"
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
        "%Y%m%d_%H%M%S"
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

    print(
        f"Session started: {session_path}"
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
            # FEATURE PACKET
            # ------------------------------------------------

            if message_type != "features":
                continue

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
            # RETURN RESULT
            # ------------------------------------------------

            await websocket.send_json({
                "type": "analysis",
                "data": result
            })

    except WebSocketDisconnect:

        print(
            f"Session disconnected: {session_id}"
        )

    except Exception as exc:

        print(
            "WebSocket error:"
        )

        print(
            traceback.format_exc()
        )

        try:
            await websocket.close()
        except Exception:
            pass

    finally:

        try:
            csv_file.flush()
            csv_file.close()
        except Exception:
            pass

        print(
            f"Session saved: {session_path}"
        )