import {
    FaceLandmarker,
    FilesetResolver,
    DrawingUtils
} from "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.21/+esm";


/* ============================================================
   DOM ELEMENTS
============================================================ */

const video =
    document.getElementById("video");

const canvas =
    document.getElementById("overlay");

const ctx =
    canvas.getContext("2d");

const startBtn =
    document.getElementById("startBtn");

const stopBtn =
    document.getElementById("stopBtn");

const systemStatus =
    document.getElementById("systemStatus");

const cliValue =
    document.getElementById("cliValue");

const phaseValue =
    document.getElementById("phaseValue");

const blinkValue =
    document.getElementById("blinkValue");

const gazeValue =
    document.getElementById("gazeValue");

const jitterValue =
    document.getElementById("jitterValue");

const stabilityValue =
    document.getElementById("stabilityValue");

const calibrationText =
    document.getElementById("calibrationText");

const calibrationTime =
    document.getElementById("calibrationTime");

const progressBar =
    document.getElementById("progressBar");

const reasonText =
    document.getElementById("reasonText");

const trendText =
    document.getElementById("trendText");

const generateReportButton =
    document.getElementById(
        "generateReportBtn"
    );

const pdfLink =
    document.getElementById("pdfLink");

const reportStatus =
    document.getElementById(
        "reportStatus"
    );


/* ============================================================
   PUBLIC BACKEND
============================================================ */

const BACKEND_URL =
    "https://adaptive-cognitive-load-analysis.onrender.com";

const WEBSOCKET_URL =
    "wss://adaptive-cognitive-load-analysis.onrender.com/ws";


/* ============================================================
   APPLICATION STATE
============================================================ */

let faceLandmarker = null;

let stream = null;

let websocket = null;

let running = false;

let endingSession = false;

let reportReady = false;

let lastTimestamp = -1;


/* ============================================================
   BLINK STATE
============================================================ */

let blinkState = false;

let blinkTimes = [];


/* ============================================================
   HEAD MOVEMENT STATE
============================================================ */

let previousNose = null;


/* ============================================================
   WEBSOCKET STATE
============================================================ */

let websocketConnected = false;


/* ============================================================
   SESSION STATE
============================================================ */

let sessionStart = 0;


/* ============================================================
   FACE LANDMARKER
============================================================ */

async function initializeFaceLandmarker() {

    systemStatus.textContent =
        "Loading vision model...";


    const vision =
        await FilesetResolver.forVisionTasks(
            "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.21/wasm"
        );


    faceLandmarker =
        await FaceLandmarker.createFromOptions(
            vision,
            {
                baseOptions: {

                    modelAssetPath:
                        "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",

                    delegate:
                        "GPU"
                },

                runningMode:
                    "VIDEO",

                numFaces:
                    1,

                minFaceDetectionConfidence:
                    0.5,

                minFacePresenceConfidence:
                    0.5,

                minTrackingConfidence:
                    0.5
            }
        );


    systemStatus.textContent =
        "Vision model ready";
}


/* ============================================================
   WEBSOCKET CONNECTION
============================================================ */

function connectWebSocket() {

    return new Promise(
        (resolve, reject) => {

            websocket =
                new WebSocket(
                    WEBSOCKET_URL
                );


            websocket.onopen = () => {

                websocketConnected =
                    true;

                systemStatus.textContent =
                    "Connected to analysis server";

                resolve();
            };


            websocket.onmessage = event => {

                try {

                    const message =
                        JSON.parse(
                            event.data
                        );

                    handleServerMessage(
                        message
                    );

                } catch (error) {

                    console.error(
                        "WebSocket message error:",
                        error
                    );
                }
            };


            websocket.onerror = error => {

                console.error(
                    "WebSocket error:",
                    error
                );

                websocketConnected =
                    false;


                if (!endingSession) {

                    systemStatus.textContent =
                        "Backend connection error";
                }


                reject(
                    new Error(
                        "Could not connect to the analysis server."
                    )
                );
            };


            websocket.onclose = () => {

                websocketConnected =
                    false;


                /*
                 * Don't overwrite the report-ready
                 * status after the server closes the
                 * connection intentionally.
                 */

                if (
                    running &&
                    !endingSession &&
                    !reportReady
                ) {

                    systemStatus.textContent =
                        "Backend disconnected";
                }
            };
        }
    );
}


/* ============================================================
   SERVER MESSAGE HANDLER
============================================================ */

function handleServerMessage(message) {

    /* --------------------------------------------------------
       REPORT READY
    -------------------------------------------------------- */

    if (
        message.type ===
        "report_ready"
    ) {

        reportReady =
            true;


        const pdfUrl =
            `${BACKEND_URL}${message.pdf}`;


        if (pdfLink) {

            pdfLink.href =
                pdfUrl;

            pdfLink.classList.remove(
                "hidden"
            );
        }


        if (reportStatus) {

            reportStatus.textContent =
                "Report generated successfully.";
        }


        if (generateReportButton) {

            generateReportButton.disabled =
                false;

            generateReportButton.textContent =
                "Report Generated";
        }


        systemStatus.textContent =
            "Session complete — report ready";


        if (calibrationText) {

            calibrationText.textContent =
                "Session complete — report ready";
        }


        finishCameraCleanup();

        return;
    }


    /* --------------------------------------------------------
       REPORT ERROR
    -------------------------------------------------------- */

    if (
        message.type ===
        "report_error"
    ) {

        reportReady =
            false;


        if (reportStatus) {

            reportStatus.textContent =
                `Report generation failed: ${message.message}`;
        }


        if (generateReportButton) {

            generateReportButton.disabled =
                false;

            generateReportButton.textContent =
                "Generate Report";
        }


        systemStatus.textContent =
            "Session complete";


        finishCameraCleanup();

        return;
    }


    /* --------------------------------------------------------
       RESET ACK
    -------------------------------------------------------- */

    if (
        message.type ===
        "reset_ack"
    ) {

        return;
    }


    /* --------------------------------------------------------
       ANALYSIS RESULT
    -------------------------------------------------------- */

    if (
        message.type !==
        "analysis"
    ) {

        return;
    }


    const data =
        message.data;


    /* ========================================================
       CALIBRATION
    ======================================================== */

    if (
        data.phase ===
        "Calibrating"
    ) {

        const progress =
            Math.round(
                (
                    data.calibration_progress ||
                    0
                ) * 100
            );


        if (calibrationText) {

            calibrationText.textContent =
                "Building personalized baseline";
        }


        if (calibrationTime) {

            calibrationTime.textContent =
                `${progress} / 100%`;
        }


        if (progressBar) {

            progressBar.style.width =
                `${progress}%`;
        }


        if (cliValue) {

            cliValue.textContent =
                "--";
        }


        if (phaseValue) {

            phaseValue.textContent =
                "Calibrating";
        }


        if (blinkValue) {

            blinkValue.textContent =
                `${Math.round(data.blink_rate || 0)}/min`;
        }


        if (gazeValue) {

            gazeValue.textContent =
                Number(
                    data.gaze_deviation || 0
                ).toFixed(3);
        }


        if (jitterValue) {

            jitterValue.textContent =
                Number(
                    data.head_jitter || 0
                ).toFixed(4);
        }


        if (stabilityValue) {

            stabilityValue.textContent =
                "--";
        }


        if (reasonText) {

            reasonText.textContent =
                "Analyzing your normal behavioral pattern.";
        }


        if (trendText) {

            trendText.textContent =
                "Phase will be determined from the recent cognitive-load trend after calibration.";
        }


        return;
    }


    /* ========================================================
       LIVE ANALYSIS
    ======================================================== */

    if (cliValue) {

        cliValue.textContent =
            `${Math.round(data.cli)}%`;
    }


    if (phaseValue) {

        phaseValue.textContent =
            data.phase;
    }


    if (blinkValue) {

        blinkValue.textContent =
            `${Math.round(data.blink_rate || 0)}/min`;
    }


    if (gazeValue) {

        gazeValue.textContent =
            Number(
                data.gaze_deviation || 0
            ).toFixed(3);
    }


    if (jitterValue) {

        jitterValue.textContent =
            Number(
                data.head_jitter || 0
            ).toFixed(4);
    }


    if (stabilityValue) {

        stabilityValue.textContent =
            `${Math.round(data.stability || 0)}%`;
    }


    if (calibrationText) {

        calibrationText.textContent =
            "Calibration complete — live analysis active";
    }


    if (calibrationTime) {

        calibrationTime.textContent =
            "Complete";
    }


    if (progressBar) {

        progressBar.style.width =
            "100%";
    }


    /*
     * Explain why the current result looks the way it does.
     */

    updateExplanation(
        data
    );


    /*
     * Show that Phase is based on the rolling trend.
     */

    if (trendText) {

        trendText.textContent =
            `Current CLI: ${Math.round(data.cli)}% • Phase is based on the recent 30-sample trend.`;
    }
}


/* ============================================================
   EXPLAINABILITY
============================================================ */

function updateExplanation(data) {

    const reasons = [];


    if (
        Number(data.fatigue || 0) >
        1.5
    ) {

        reasons.push(
            "Blink activity above baseline"
        );
    }


    if (
        Number(data.distraction || 0) >
        1.5
    ) {

        reasons.push(
            "Gaze deviation above baseline"
        );
    }


    if (
        Number(data.stress || 0) >
        1.5
    ) {

        reasons.push(
            "Head movement above baseline"
        );
    }


    if (
        reasons.length === 0
    ) {

        if (reasonText) {

            reasonText.textContent =
                "Behavioral signals are within the personalized baseline range.";
        }

    } else {

        if (reasonText) {

            reasonText.textContent =
                reasons.join(
                    " • "
                );
        }
    }
}


/* ============================================================
   START CAMERA
============================================================ */

async function startCamera() {

    try {

        startBtn.disabled =
            true;

        stopBtn.disabled =
            true;


        endingSession =
            false;

        reportReady =
            false;


        resetSession();


        if (!faceLandmarker) {

            await initializeFaceLandmarker();
        }


        /*
         * Create a fresh WebSocket session.
         */

        if (
            websocket &&
            websocket.readyState !==
            WebSocket.CLOSED
        ) {

            websocket.close();
        }


        await connectWebSocket();


        /*
         * Request local webcam.
         */

        stream =
            await navigator.mediaDevices.getUserMedia(
                {
                    video: {

                        width: {
                            ideal: 1280
                        },

                        height: {
                            ideal: 720
                        },

                        facingMode:
                            "user"
                    },

                    audio: false
                }
            );


        video.srcObject =
            stream;


        await video.play();


        running =
            true;


        sessionStart =
            performance.now();


        stopBtn.disabled =
            false;


        systemStatus.textContent =
            "Live vision + analysis active";


        requestAnimationFrame(
            processFrame
        );

    } catch (error) {

        console.error(
            "Camera startup error:",
            error
        );


        systemStatus.textContent =
            "Startup error";


        reasonText.textContent =
            error.message ||
            "Unable to start camera.";


        startBtn.disabled =
            false;

        stopBtn.disabled =
            true;


        if (stream) {

            stream
                .getTracks()
                .forEach(
                    track =>
                        track.stop()
                );

            stream = null;
        }


        if (
            websocket &&
            websocket.readyState ===
            WebSocket.OPEN
        ) {

            websocket.close();
        }

        websocket = null;

        websocketConnected =
            false;
    }
}


/* ============================================================
   STOP CAMERA
============================================================ */

function stopCamera() {

    /*
     * Stop frame processing first.
     * Keep the WebSocket alive because the backend
     * must generate the report and send it back.
     */

    running =
        false;

    endingSession =
        true;


    startBtn.disabled =
        true;

    stopBtn.disabled =
        true;


    systemStatus.textContent =
        "Finalizing session report...";


    if (reportStatus) {

        reportStatus.textContent =
            "Finalizing session and generating report...";
    }


    /*
     * Tell FastAPI to finish this exact session.
     */

    if (
        websocket &&
        websocket.readyState ===
        WebSocket.OPEN
    ) {

        websocket.send(
            JSON.stringify({
                type:
                    "end_session"
            })
        );

    } else {

        /*
         * If there's no WebSocket connection,
         * just clean up locally.
         */

        finishCameraCleanup();
    }
}


/* ============================================================
   CAMERA CLEANUP
============================================================ */

function finishCameraCleanup() {

    running =
        false;


    if (stream) {

        stream
            .getTracks()
            .forEach(
                track =>
                    track.stop()
            );

        stream =
            null;
    }


    video.srcObject =
        null;


    startBtn.disabled =
        false;

    stopBtn.disabled =
        true;


    /*
     * Do not immediately destroy the websocket
     * here if the server is still closing it.
     */

    if (
        websocket &&
        websocket.readyState ===
        WebSocket.OPEN
    ) {

        websocket.close();
    }


    websocket =
        null;


    websocketConnected =
        false;


    /*
     * Do not overwrite report-ready state.
     */

    if (!reportReady) {

        systemStatus.textContent =
            "Session stopped";
    }


    /*
     * Allow a new report to be generated
     * only if a report wasn't already delivered.
     */

    if (
        generateReportButton &&
        !reportReady
    ) {

        generateReportButton.disabled =
            false;

        generateReportButton.textContent =
            "Generate Report";
    }
}


/* ============================================================
   RESET SESSION UI
============================================================ */

function resetSession() {

    blinkState =
        false;

    blinkTimes =
        [];

    previousNose =
        null;

    lastTimestamp =
        -1;


    reportReady =
        false;

    endingSession =
        false;


    if (calibrationText) {

        calibrationText.textContent =
            "Building personalized baseline";
    }


    if (calibrationTime) {

        calibrationTime.textContent =
            "0 / 60 s";
    }


    if (progressBar) {

        progressBar.style.width =
            "0%";
    }


    if (cliValue) {

        cliValue.textContent =
            "--";
    }


    if (phaseValue) {

        phaseValue.textContent =
            "Calibrating";
    }


    if (blinkValue) {

        blinkValue.textContent =
            "--";
    }


    if (gazeValue) {

        gazeValue.textContent =
            "--";
    }


    if (jitterValue) {

        jitterValue.textContent =
            "--";
    }


    if (stabilityValue) {

        stabilityValue.textContent =
            "--";
    }


    if (reasonText) {

        reasonText.textContent =
            "Establishing your personalized behavioral baseline.";
    }


    if (trendText) {

        trendText.textContent =
            "Phase will be determined from the recent cognitive-load trend after calibration.";
    }


    if (generateReportButton) {

        generateReportButton.disabled =
            true;

        generateReportButton.textContent =
            "Generate Report";
    }


    if (pdfLink) {

        pdfLink.classList.add(
            "hidden"
        );

        pdfLink.removeAttribute(
            "href"
        );
    }


    if (reportStatus) {

        reportStatus.textContent =
            "No report generated yet.";
    }
}


/* ============================================================
   GEOMETRY HELPERS
============================================================ */

function distance(a, b) {

    const dx =
        a.x - b.x;

    const dy =
        a.y - b.y;


    return Math.sqrt(
        dx * dx +
        dy * dy
    );
}


function center(points) {

    let x =
        0;

    let y =
        0;


    for (
        const point of points
    ) {

        x += point.x;

        y += point.y;
    }


    return {

        x:
            x / points.length,

        y:
            y / points.length
    };
}


function eyeAspectRatio(points) {

    const A =
        distance(
            points[1],
            points[5]
        );

    const B =
        distance(
            points[2],
            points[4]
        );

    const C =
        distance(
            points[0],
            points[3]
        );


    if (
        C === 0
    ) {

        return 0;
    }


    return (
        A + B
    ) / (
        2 * C
    );
}


/* ============================================================
   LANDMARK DRAWING
============================================================ */

function drawLandmarks(landmarks) {

    const drawingUtils =
        new DrawingUtils(
            ctx
        );


    /*
     * Full face tessellation
     */

    drawingUtils.drawConnectors(
        landmarks,

        FaceLandmarker.FACE_LANDMARKS_TESSELATION,

        {
            color:
                "#ffffff35",

            lineWidth:
                1
        }
    );


    /*
     * Face outline
     */

    drawingUtils.drawConnectors(
        landmarks,

        FaceLandmarker.FACE_LANDMARKS_FACE_OVAL,

        {
            color:
                "#8ea5b8",

            lineWidth:
                2
        }
    );


    /*
     * Eyes
     */

    drawingUtils.drawConnectors(
        landmarks,

        FaceLandmarker.FACE_LANDMARKS_LEFT_EYE,

        {
            color:
                "#39e6c5",

            lineWidth:
                3
        }
    );


    drawingUtils.drawConnectors(
        landmarks,

        FaceLandmarker.FACE_LANDMARKS_RIGHT_EYE,

        {
            color:
                "#39e6c5",

            lineWidth:
                3
        }
    );


    /*
     * Iris
     */

    drawingUtils.drawConnectors(
        landmarks,

        FaceLandmarker.FACE_LANDMARKS_LEFT_IRIS,

        {
            color:
                "#ffffff",

            lineWidth:
                3
        }
    );


    drawingUtils.drawConnectors(
        landmarks,

        FaceLandmarker.FACE_LANDMARKS_RIGHT_IRIS,

        {
            color:
                "#ffffff",

            lineWidth:
                3
        }
    );


    /*
     * Iris centers
     */

    drawIrisCenter(
        landmarks,
        [
            468,
            469,
            470,
            471,
            472
        ]
    );


    drawIrisCenter(
        landmarks,
        [
            473,
            474,
            475,
            476,
            477
        ]
    );
}


/* ============================================================
   IRIS CENTER
============================================================ */

function drawIrisCenter(
    landmarks,
    indices
) {

    const points =
        indices.map(
            index =>
                landmarks[index]
        );


    const c =
        center(points);


    const x =
        c.x * canvas.width;

    const y =
        c.y * canvas.height;


    ctx.beginPath();


    ctx.arc(
        x,
        y,
        Math.max(
            3,
            canvas.width / 320
        ),
        0,
        Math.PI * 2
    );


    ctx.fillStyle =
        "#ffffff";


    ctx.fill();
}


/* ============================================================
   MAIN FRAME LOOP
============================================================ */

function processFrame() {

    if (!running) {

        return;
    }


    if (
        video.readyState <
        HTMLMediaElement.HAVE_CURRENT_DATA
    ) {

        requestAnimationFrame(
            processFrame
        );

        return;
    }


    if (
        canvas.width !==
            video.videoWidth ||

        canvas.height !==
            video.videoHeight
    ) {

        canvas.width =
            video.videoWidth;

        canvas.height =
            video.videoHeight;
    }


    ctx.clearRect(
        0,
        0,
        canvas.width,
        canvas.height
    );


    let timestamp =
        performance.now();


    if (
        timestamp <=
        lastTimestamp
    ) {

        timestamp =
            lastTimestamp + 1;
    }


    lastTimestamp =
        timestamp;


    /* --------------------------------------------------------
       MEDIAPIPE
    -------------------------------------------------------- */

    const result =
        faceLandmarker.detectForVideo(
            video,
            timestamp
        );


    /* --------------------------------------------------------
       FACE DETECTED
    -------------------------------------------------------- */

    if (
        result.faceLandmarks &&
        result.faceLandmarks.length > 0
    ) {

        const landmarks =
            result.faceLandmarks[0];


        drawLandmarks(
            landmarks
        );


        extractAndSendFeatures(
            landmarks,
            timestamp
        );

    } else {

        if (reasonText) {

            reasonText.textContent =
                "No face detected. Please position your face inside the camera frame.";
        }
    }


    requestAnimationFrame(
        processFrame
    );
}


/* ============================================================
   FEATURE EXTRACTION
============================================================ */

function extractAndSendFeatures(
    landmarks,
    now
) {

    /* --------------------------------------------------------
       LEFT EYE
    -------------------------------------------------------- */

    const eyeIndices = [
        33,
        160,
        158,
        133,
        153,
        144
    ];


    const eye =
        eyeIndices.map(
            index =>
                landmarks[index]
        );


    /* --------------------------------------------------------
       BLINK
    -------------------------------------------------------- */

    const ear =
        eyeAspectRatio(
            eye
        );


    if (
        ear < 0.22 &&
        !blinkState
    ) {

        blinkTimes.push(
            now
        );

        blinkState =
            true;
    }


    if (
        ear > 0.25
    ) {

        blinkState =
            false;
    }


    blinkTimes =
        blinkTimes.filter(
            time =>
                now - time <
                60000
        );


    const blinkRate =
        blinkTimes.length;


    /* --------------------------------------------------------
       GAZE
    -------------------------------------------------------- */

    const irisIndices = [
        468,
        469,
        470,
        471,
        472
    ];


    const iris =
        irisIndices.map(
            index =>
                landmarks[index]
        );


    const irisCenter =
        center(iris);


    const eyeCenter =
        center(eye);


    const eyeWidth =
        distance(
            eye[0],
            eye[3]
        );


    let gazeDeviation =
        0;


    if (
        eyeWidth > 0
    ) {

        gazeDeviation =
            Math.abs(
                irisCenter.x -
                eyeCenter.x
            ) /
            eyeWidth;
    }


    /* --------------------------------------------------------
       HEAD JITTER
    -------------------------------------------------------- */

    const nose =
        landmarks[1];


    let headJitter =
        0;


    if (
        previousNose !== null
    ) {

        headJitter =
            distance(
                nose,
                previousNose
            );
    }


    previousNose = {

        x:
            nose.x,

        y:
            nose.y
    };


    /* --------------------------------------------------------
       SEND FEATURES
    -------------------------------------------------------- */

    if (
        websocketConnected &&
        websocket &&
        websocket.readyState ===
        WebSocket.OPEN
    ) {

        websocket.send(
            JSON.stringify({

                type:
                    "features",

                timestamp:
                    now,

                blink_rate:
                    blinkRate,

                gaze_deviation:
                    gazeDeviation,

                head_jitter:
                    headJitter
            })
        );
    }
}


/* ============================================================
   BUTTON EVENTS
============================================================ */

startBtn.addEventListener(
    "click",
    startCamera
);


stopBtn.addEventListener(
    "click",
    stopCamera
);
