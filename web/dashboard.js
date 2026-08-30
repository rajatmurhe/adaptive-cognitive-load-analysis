/* ============================================================
   LIVE DASHBOARD CONTROLLER
============================================================ */


const cliElement =
    document.getElementById("cliValue");

const phaseElement =
    document.getElementById("phaseValue");

const startButton =
    document.getElementById("startBtn");

const stopButton =
    document.getElementById("stopBtn");

const chartStatus =
    document.getElementById("chartStatus");

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
   CHART DATA
============================================================ */

const chartLabels = [];
const chartValues = [];

let chartCounter = 0;

let sessionRunning = false;


/* ============================================================
   CREATE CHART
============================================================ */

const chartCanvas =
    document.getElementById(
        "cliChart"
    );


const cliChart =
    new Chart(
        chartCanvas,
        {
            type: "line",

            data: {
                labels: chartLabels,

                datasets: [
                    {
                        label:
                            "Cognitive Load",

                        data:
                            chartValues,

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

function addCLIValue(
    value
) {

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
            String(value)
                .replace("%", "")
        );


    if (
        Number.isNaN(
            numericValue
        )
    ) {
        return;
    }


    chartCounter += 1;


    /*
     * Only keep the latest 180 points.
     * This prevents the browser chart from
     * growing forever during a long session.
     */

    if (
        chartLabels.length >= 180
    ) {

        chartLabels.shift();

        chartValues.shift();
    }


    chartLabels.push(
        `${chartCounter}s`
    );

    chartValues.push(
        numericValue
    );


    cliChart.update(
        "none"
    );
}


/* ============================================================
   OBSERVE CLI
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
   CAMERA START
============================================================ */

startButton.addEventListener(
    "click",
    () => {

        sessionRunning =
            true;

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
   CAMERA STOP
============================================================ */

stopButton.addEventListener(
    "click",
    () => {

        sessionRunning =
            false;

        chartStatus.textContent =
            "Session complete";

        /*
         * Give FastAPI a moment to finish
         * writing the CSV before enabling
         * report generation.
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
                    "http://127.0.0.1:8000/report/latest"
                );


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
                "http://127.0.0.1:8000"
                +
                result.pdf;


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
