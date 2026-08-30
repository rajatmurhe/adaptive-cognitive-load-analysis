import {
    FaceLandmarker,
    FilesetResolver,
    DrawingUtils
} from "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.21/+esm";


/* ============================================================
   DOM
============================================================ */

const video = document.getElementById("video");
const canvas = document.getElementById("overlay");
const ctx = canvas.getContext("2d");

const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");

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


/* ============================================================
   APPLICATION STATE
============================================================ */

let faceLandmarker = null;
let stream = null;
let websocket = null;

let running = false;

let lastTimestamp = -1;


/* ============================================================
   BLINK STATE
============================================================ */

let blinkState = false;

let blinkTimes = [];


/* ============================================================
   HEAD STATE
============================================================ */

let previousNose = null;


/* ============================================================
   WEBSOCKET STATE
============================================================ */

let websocketConnected = false;


/* ============================================================
   SESSION
============================================================ */

let sessionStart = 0;


/* ============================================================
   MEDIA PIPE INITIALIZATION
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
                    "ws://127.0.0.1:8000/ws"
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

                systemStatus.textContent =
                    "Backend connection error";

                reject(
                    new Error(
                        "Could not connect to FastAPI backend."
                    )
                );
            };


            websocket.onclose = () => {

                websocketConnected =
                    false;

                if (running) {

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

    if (
        message.type ===
        "reset_ack"
    ) {

        return;
    }


    if (
        message.type !==
        "analysis"
    ) {

        return;
    }


    const data =
        message.data;


    /* --------------------------------------------------------
       CALIBRATION
    -------------------------------------------------------- */

    if (
        data.phase ===
        "Calibrating"
    ) {

        const progress =
            Math.round(
                (
                    data.calibration_progress
                    || 0
                ) * 100
            );


        calibrationText.textContent =
            "Building personalized baseline";


        calibrationTime.textContent =
            `${progress}%`;


        progressBar.style.width =
            `${progress}%`;


        cliValue.textContent =
            "--";


        phaseValue.textContent =
            "Calibrating";


        blinkValue.textContent =
            `${Math.round(data.blink_rate)}/min`;


        gazeValue.textContent =
            Number(
                data.gaze_deviation || 0
            ).toFixed(3);


        jitterValue.textContent =
            Number(
                data.head_jitter || 0
            ).toFixed(4);


        stabilityValue.textContent =
            "--";


        reasonText.textContent =
            "Analyzing your normal behavioral pattern.";

        return;
    }


    /* --------------------------------------------------------
       LIVE ANALYSIS
    -------------------------------------------------------- */

    calibrationText.textContent =
        "Calibration complete — live analysis active";


    calibrationTime.textContent =
        "Complete";


    progressBar.style.width =
        "100%";


    cliValue.textContent =
        `${Math.round(data.cli)}%`;


    phaseValue.textContent =
        data.phase;


    blinkValue.textContent =
        `${Math.round(data.blink_rate)}/min`;


    gazeValue.textContent =
        Number(
            data.gaze_deviation
        ).toFixed(3);


    jitterValue.textContent =
        Number(
            data.head_jitter
        ).toFixed(4);


    stabilityValue.textContent =
        `${Math.round(data.stability)}%`;


    updateExplanation(
        data
    );
}


/* ============================================================
   EXPLAINABILITY
============================================================ */

function updateExplanation(data) {

    const reasons = [];


    if (
        data.fatigue >
        1.5
    ) {

        reasons.push(
            "Blink activity above baseline"
        );
    }


    if (
        data.distraction >
        1.5
    ) {

        reasons.push(
            "Gaze deviation above baseline"
        );
    }


    if (
        data.stress >
        1.5
    ) {

        reasons.push(
            "Head movement above baseline"
        );
    }


    if (
        reasons.length === 0
    ) {

        reasonText.textContent =
            "Behavioral signals are within the personalized baseline range.";

    } else {

        reasonText.textContent =
            reasons.join(
                " • "
            );
    }
}


/* ============================================================
   CAMERA START
============================================================ */

async function startCamera() {

    try {

        startBtn.disabled =
            true;


        if (!faceLandmarker) {

            await initializeFaceLandmarker();
        }


        /*
         * Connect to Python backend.
         */

        if (
            !websocketConnected
        ) {

            await connectWebSocket();
        }


        /*
         * Request browser camera.
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


        resetSession();


        running =
            true;


        sessionStart =
            performance.now();


        startBtn.disabled =
            true;

        stopBtn.disabled =
            false;


        systemStatus.textContent =
            "Live vision + analysis active";


        requestAnimationFrame(
            processFrame
        );


    } catch (error) {

        console.error(
            error
        );


        systemStatus.textContent =
            "Startup error";


        reasonText.textContent =
            error.message;


        startBtn.disabled =
            false;
    }
}


/* ============================================================
   CAMERA STOP
============================================================ */

function stopCamera() {

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


    startBtn.disabled =
        false;

    stopBtn.disabled =
        true;


    systemStatus.textContent =
        "Session stopped";


    calibrationText.textContent =
        "Start the camera to begin";


    calibrationTime.textContent =
        "0 / 60 s";
}


/* ============================================================
   RESET
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


    calibrationText.textContent =
        "Building personalized baseline";


    calibrationTime.textContent =
        "0 / 60 s";


    progressBar.style.width =
        "0%";


    cliValue.textContent =
        "--";


    phaseValue.textContent =
        "Calibrating";


    blinkValue.textContent =
        "--";


    gazeValue.textContent =
        "--";


    jitterValue.textContent =
        "--";


    stabilityValue.textContent =
        "--";


    reasonText.textContent =
        "Establishing your personalized behavioral baseline.";
}


/* ============================================================
   GEOMETRY
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
   DRAW LANDMARKS
============================================================ */

function drawLandmarks(landmarks) {

    const drawingUtils =
        new DrawingUtils(
            ctx
        );


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
       FACE FOUND
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

        reasonText.textContent =
            "No face detected. Please position your face inside the camera frame.";
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

    /*
     * LEFT EYE
     */

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
       SEND FEATURES TO PYTHON
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
   BUTTONS
============================================================ */

startBtn.addEventListener(
    "click",
    startCamera
);


stopBtn.addEventListener(
    "click",
    stopCamera
);