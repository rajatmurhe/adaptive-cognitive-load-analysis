/* ============================================================
   LIVE DASHBOARD CONTROLLER
============================================================ */

const cliElement =
    document.getElementById("cliValue");

const startButton =
    document.getElementById("startBtn");

const stopButton =
    document.getElementById("stopBtn");

const chartStatus =
    document.getElementById("chartStatus");

const generateReportButton =
    document.getElementById("generateReportBtn");

const pdfLink =
    document.getElementById("pdfLink");

const reportStatus =
    document.getElementById("reportStatus");


/* ============================================================
   PUBLIC BACKEND
============================================================ */

const BACKEND_URL =
    "https://adaptive-cognitive-load-analysis.onrender.com";


/* ============================================================
   CHART DATA
============================================================ */

const chartLabels = [];
const chartValues = [];

let chartCounter = 0;


/* ============================================================
   CHART
============================================================ */

const chartCanvas =
    document.getElementById("cliChart");


const cliChart =
    new Chart(
        chartCanvas,
        {
            type: "line",

            data: {
                labels: chartLabels,

                datasets: [
                    {
                        label: "Cognitive Load",

                        data: chartValues,

                        borderWidth: 2,

                        pointRadius: 0,

                        tension: 0.25
                    }
                ]
            },

            options: {

                responsive: true,

                maintainAspectRatio: false,

                animation: false,

                interaction: {
                    intersect: false,
                    mode: "index"
                },

                scales: {

                    x: {
                        title: {
                            display: true,
                            text: "Session Time"
                        }
                    },

                    y: {
                        min: 0,
                        max: 100,

                        title: {
                            display: true,
                            text: "Cognitive Load"
                        }
                    }
                },

                plugins: {

                    legend: {
                        display: true
                    }
                }
            }
        }
    );


/* ============================================================
   RESET CHART
============================================================ */

function resetChart() {

    chartLabels.length = 0;

    chartValues.length = 0;

    chartCounter = 0;

    cliChart.update();

    chartStatus.textContent =
        "Session active";
}


/* ============================================================
   ADD CLI VALUE
============================================================ */

function addCLIValue(value) {

    if (
        value === null ||
        value === undefined ||
        value === "--" ||
        value === ""
    ) {
        return;
    }


    const numericValue =
        parseFloat(
            String(value).replace("%", "")
        );


    if (
        Number.isNaN(numericValue)
    ) {
        return;
    }


    chartCounter += 1;


    if (
        chartLabels.length >= 180
    ) {

        chartLabels.shift();

        chartValues.shift();
    }


    chartLabels.push(
        `${chartCounter}`
    );

    chartValues.push(
        numericValue
    );


    cliChart.update("none");
}


/* ============================================================
   WATCH CLI
============================================================ */

const cliObserver =
    new MutationObserver(
        mutations => {

            for (
                const mutation
                of mutations
            ) {

                if (
                    mutation.type ===
                    "childList"
                ) {

                    addCLIValue(
                        cliElement.textContent
                    );
                }
            }
        }
    );


cliObserver.observe(
    cliElement,
    {
        childList: true,
        subtree: true
    }
);


/* ============================================================
   START CAMERA
============================================================ */

startButton.addEventListener(
    "click",
    () => {

        resetChart();

        generateReportButton.disabled =
            true;

        pdfLink.classList.add(
            "hidden"
        );

        reportStatus.textContent =
            "Session in progress...";
    }
);


/* ============================================================
   STOP CAMERA
============================================================ */

stopButton.addEventListener(
    "click",
    () => {

        chartStatus.textContent =
            "Session complete";


        /*
         * Wait briefly so FastAPI has time
         * to finish writing the current session.
         */

        setTimeout(
            () => {

                generateReportButton.disabled =
                    false;

                reportStatus.textContent =
                    "Session completed. Report is ready to generate.";

            },
            1500
        );
    }
);


/* ============================================================
   GENERATE REPORT
============================================================ */

generateReportButton.addEventListener(
    "click",
    async () => {

        generateReportButton.disabled =
            true;

        generateReportButton.textContent =
            "Generating...";

        reportStatus.textContent =
            "Analyzing session data and generating report...";


        try {

            const response =
                await fetch(
                    `${BACKEND_URL}/report/latest`
                );


            if (!response.ok) {

                throw new Error(
                    `Server returned HTTP ${response.status}`
                );
            }


            const result =
                await response.json();


            if (
                result.status !==
                "success"
            ) {

                throw new Error(
                    result.message ||
                    "Report generation failed."
                );
            }


            const pdfUrl =
                `${BACKEND_URL}${result.pdf}`;


            pdfLink.href =
                pdfUrl;


            pdfLink.classList.remove(
                "hidden"
            );


            reportStatus.textContent =
                "Report generated successfully.";


            generateReportButton.textContent =
                "Report Generated";


        } catch (error) {

            console.error(
                "Report error:",
                error
            );


            reportStatus.textContent =
                error.message ||
                "Unable to generate report.";


            generateReportButton.disabled =
                false;


            generateReportButton.textContent =
                "Generate Report";
        }
    }
);
