// ============================================================
// DATALINK AI - DASHBOARD.JS
// ============================================================


// ============================================================
// USER / SESSION
// ============================================================

const storedUser =
    localStorage.getItem("productmind_user");

let user = null;

try {
    user = storedUser
        ? JSON.parse(storedUser)
        : null;
} catch (error) {
    console.error(
        "Could not read stored user:",
        error
    );
}

if (!user) {
    window.location.href = "login.html";
}


// ============================================================
// DOM READY
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        initializeDashboard();

    }
);


// ============================================================
// INITIALIZE DASHBOARD
// ============================================================

function initializeDashboard() {

    const nameElement = document.getElementById("userName");
    if (nameElement && user) nameElement.textContent = user.name || user.email || "User";

    setupLogout();

    setupUpload();

    loadFiles();

}


// ============================================================
// LOGOUT
// ============================================================

function setupLogout() {

    const logoutButton =
        document.getElementById("logoutButton") ||
        document.getElementById("logoutBtn") ||
        document.getElementById("logout-button") ||
        document.querySelector(".logout-button") ||
        document.querySelector(".logout-btn");

    if (!logoutButton) {
        return;
    }

    logoutButton.addEventListener(
        "click",
        async function () {

            try {

                const response =
                    await fetch(
                        "/api/auth/logout",
                        {
                            method: "POST"
                        }
                    );

                if (response.ok) {

                    console.log(
                        "Logout successful"
                    );

                }

            } catch (error) {

                console.error(
                    "Logout request error:",
                    error
                );

            }

            localStorage.removeItem("productmind_user");
            localStorage.removeItem("user");

            window.location.href =
                "login.html";
        }
    );
}


// ============================================================
// UPLOAD
// ============================================================

function setupUpload() {

    const uploadForm =
        document.getElementById("uploadForm") ||
        document.getElementById("dashboard-upload-form");

    const fileInput =
        document.getElementById(
            "fileInput"
        ) ||
        document.getElementById(
            "dashboard-file-input"
        );

    const uploadMessage =
        document.getElementById("uploadMessage") ||
        document.getElementById("upload-message") ||
        document.getElementById("uploadStatus");

    if (!uploadForm || !fileInput) {
        console.error("Upload form or file input is missing from dashboard.html");
        return;
    }

    fileInput.addEventListener("change", function () {
        const label = document.getElementById("fileName");
        if (label) label.textContent = fileInput.files && fileInput.files[0] ? fileInput.files[0].name : "";
    });

    uploadForm.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();

            if (
                !fileInput.files ||
                fileInput.files.length === 0
            ) {

                showMessage(
                    uploadMessage,
                    "Please select a CSV or Excel file."
                );

                return;
            }

            const file =
                fileInput.files[0];

            const filename =
                file.name.toLowerCase();

            const validExtension =
                filename.endsWith(".csv") ||
                filename.endsWith(".xlsx") ||
                filename.endsWith(".xls");

            if (!validExtension) {

                showMessage(
                    uploadMessage,
                    "Only CSV, XLSX and XLS files are allowed."
                );

                return;
            }

            showMessage(
                uploadMessage,
                "Uploading file...",
                true
            );

            const formData =
                new FormData();

            formData.append(
                "file",
                file
            );

            formData.append(
                "user_id",
                user.id
            );

            try {

                const response =
                    await fetch(
                        "/api/files/upload",
                        {
                            method: "POST",
                            body: formData
                        }
                    );

                const data =
                    await response.json();

                if (
                    !response.ok ||
                    !data.success
                ) {

                    showMessage(
                        uploadMessage,
                        data.message ||
                        "File upload failed."
                    );

                    return;
                }

                showMessage(
                    uploadMessage,
                    "File uploaded successfully.",
                    true
                );

                fileInput.value = "";

                await loadFiles();

            } catch (error) {

                console.error(
                    "Upload error:",
                    error
                );

                showMessage(
                    uploadMessage,
                    "Could not connect to the backend."
                );
            }
        }
    );
}


// ============================================================
// LOAD FILES
// ============================================================

async function loadFiles() {

    const filesContainer =
        document.getElementById(
            "filesList"
        ) ||
        document.getElementById(
            "files-list"
        ) ||
        document.getElementById(
            "uploadedFiles"
        );

    try {

        const response =
            await fetch(
                `/api/files/list?user_id=${encodeURIComponent(user.id)}`
            );

        const data =
            await response.json();

        if (
            !response.ok ||
            !data.success
        ) {

            throw new Error(
                data.message ||
                "Could not load files."
            );
        }

        displayFiles(
            data.files || [],
            filesContainer
        );

    } catch (error) {

        console.error(
            "Load files error:",
            error
        );

        if (filesContainer) {

            filesContainer.innerHTML = `
                <div class="error-message">
                    Could not load uploaded files.
                </div>
            `;
        }
    }
}


// ============================================================
// DISPLAY FILES
// ============================================================

function displayFiles(
    files,
    container
) {

    if (!container) {
        return;
    }

    if (!files || files.length === 0) {

        container.innerHTML = `
            <div class="empty-state">
                No datasets uploaded yet.
            </div>
        `;

        return;
    }

    let html = "";

    files.forEach(
        function (file) {

            const size =
                formatFileSize(
                    file.size
                );

            html += `
                <div class="file-item">

                    <div class="file-info">

                        <strong>
                            ${escapeHtml(
                                file.name
                            )}
                        </strong>

                        <span>
                            ${escapeHtml(
                                file.type
                                    .toUpperCase()
                            )}
                            ·
                            ${size}
                        </span>

                        ${
                            file.uploaded_at
                                ? `
                                    <small>
                                        ${escapeHtml(
                                            file.uploaded_at
                                        )}
                                    </small>
                                  `
                                : ""
                        }

                    </div>

                    <div class="file-actions">

                        <button
                            type="button"
                            onclick="analyzeFile(${file.id})"
                        >
                            Analyze
                        </button>

                    </div>

                </div>
            `;
        }
    );

    container.innerHTML = html;
}


// ============================================================
// ANALYZE FILE
// ============================================================

async function analyzeFile(
    fileId
) {

    const analysisCard =
        document.getElementById(
            "analysisCard"
        );

    if (analysisCard) {

        analysisCard.style.display =
            "block";

        analysisCard.scrollIntoView({
            behavior: "smooth"
        });
    }

    const analysisFileName =
        document.getElementById(
            "analysisFileName"
        );

    if (analysisFileName) {

        analysisFileName.textContent =
            "Analyzing dataset...";
    }

    try {

        const response =
            await fetch(
                `/api/files/${fileId}/analyze?user_id=${encodeURIComponent(user.id)}`
            );

        const data =
            await response.json();

        if (
            !response.ok ||
            !data.success
        ) {

            alert(
                data.message ||
                "Analysis failed."
            );

            return;
        }

        displayAnalysis(
            data
        );

        await loadQualityReport(
            fileId
        );

        createCleaningControls(
            fileId,
            data
        );

        await loadEmptyColumns(
            fileId
        );

    } catch (error) {

        console.error(
            "Analysis error:",
            error
        );

        alert(
            "Could not analyze dataset."
        );
    }
}


// ============================================================
// DISPLAY ANALYSIS
// ============================================================

function displayAnalysis(
    data
) {

    const analysisCard =
        document.getElementById(
            "analysisCard"
        );

    if (analysisCard) {

        analysisCard.style.display =
            "block";
    }

    const analysisFileName =
        document.getElementById(
            "analysisFileName"
        );

    if (analysisFileName) {

        analysisFileName.textContent =
            data.file?.name ||
            "Dataset Analysis";
    }

    const summary =
        data.summary || {};

    setText(
        "rowCount",
        summary.rows ?? 0
    );

    setText(
        "columnCount",
        summary.columns ?? 0
    );

    setText(
        "missingCount",
        summary.missing_values ?? 0
    );

    setText(
        "duplicateCount",
        summary.duplicate_rows ?? 0
    );

    setText(
        "numericCount",
        summary.numeric_columns ?? 0
    );

    setText(
        "textCount",
        summary.text_columns ?? 0
    );

    setText(
        "dateCount",
        summary.date_columns ?? 0
    );

    setText(
        "otherCount",
        summary.other_columns ?? 0
    );

    displayPreview(
        data.preview || []
    );

    displayColumnDetails(
        data.columns || []
    );
}


// ============================================================
// DISPLAY PREVIEW
// ============================================================

function displayPreview(
    preview
) {

    const previewContainer =
        document.getElementById(
            "previewContainer"
        ) ||
        document.getElementById(
            "dataPreview"
        );

    if (!previewContainer) {
        return;
    }

    if (
        !preview ||
        preview.length === 0
    ) {

        previewContainer.innerHTML = `
            <p>No preview data available.</p>
        `;

        return;
    }

    const columns =
        Object.keys(
            preview[0]
        );

    let html = `
        <div class="table-container">

            <table>

                <thead>

                    <tr>
    `;

    columns.forEach(
        function (column) {

            html += `
                <th>
                    ${escapeHtml(
                        column
                    )}
                </th>
            `;
        }
    );

    html += `
                    </tr>

                </thead>

                <tbody>
    `;

    preview.forEach(
        function (row) {

            html += `
                <tr>
            `;

            columns.forEach(
                function (column) {

                    const value =
                        row[column];

                    html += `
                        <td>
                            ${escapeHtml(
                                formatCellValue(
                                    value
                                )
                            )}
                        </td>
                    `;
                }
            );

            html += `
                </tr>
            `;
        }
    );

    html += `
                </tbody>

            </table>

        </div>
    `;

    previewContainer.innerHTML =
        html;
}


// ============================================================
// DISPLAY COLUMN DETAILS
// ============================================================

function displayColumnDetails(
    columns
) {

    const container =
        document.getElementById(
            "columnDetails"
        ) ||
        document.getElementById(
            "columnsContainer"
        );

    if (!container) {
        return;
    }

    if (
        !columns ||
        columns.length === 0
    ) {

        container.innerHTML =
            "<p>No column details available.</p>";

        return;
    }

    let html = `
        <div class="table-container">

            <table>

                <thead>

                    <tr>

                        <th>
                            Column
                        </th>

                        <th>
                            Type
                        </th>

                        <th>
                            Missing
                        </th>

                        <th>
                            Unique
                        </th>

                    </tr>

                </thead>

                <tbody>
    `;

    columns.forEach(
        function (column) {

            html += `
                <tr>

                    <td>
                        ${escapeHtml(
                            column.name
                        )}
                    </td>

                    <td>
                        ${escapeHtml(
                            column.type
                        )}
                    </td>

                    <td>
                        ${column.missing}
                    </td>

                    <td>
                        ${column.unique}
                    </td>

                </tr>
            `;
        }
    );

    html += `
                </tbody>

            </table>

        </div>
    `;

    container.innerHTML =
        html;
}


// ============================================================
// LOAD QUALITY REPORT
// ============================================================

async function loadQualityReport(
    fileId
) {

    try {

        const response =
            await fetch(
                `/api/files/${fileId}/quality?user_id=${encodeURIComponent(user.id)}`
            );

        const data =
            await response.json();

        if (
            !response.ok ||
            !data.success
        ) {

            console.error(
                "Quality report error:",
                data.message
            );

            return;
        }

        displayQualityReport(
            data.quality
        );

    } catch (error) {

        console.error(
            "Quality report error:",
            error
        );
    }
}


// ============================================================
// DISPLAY QUALITY REPORT
// ============================================================

function displayQualityReport(
    quality
) {

    const container =
        document.getElementById(
            "qualityReport"
        );

    if (!container) {
        return;
    }

    if (!quality) {

        container.innerHTML =
            "<p>No quality report available.</p>";

        return;
    }

    const score =
        quality.quality_score ??
        quality.score ??
        "N/A";

    const totalMissing =
        quality.total_missing ??
        quality.missing_values ??
        0;

    const duplicateRows =
        quality.duplicate_rows ??
        0;

    const emptyColumns =
        quality.empty_columns ??
        0;

    let recommendationsHtml = "";

    const recommendations =
        quality.recommendations ||
        [];

    if (
        Array.isArray(
            recommendations
        ) &&
        recommendations.length > 0
    ) {

        recommendationsHtml = `
            <div class="quality-recommendations">

                <h4>
                    Recommendations
                </h4>

                <ul>
        `;

        recommendations.forEach(
            function (recommendation) {

                recommendationsHtml += `
                    <li>
                        ${escapeHtml(
                            recommendation
                        )}
                    </li>
                `;
            }
        );

        recommendationsHtml += `
                </ul>

            </div>
        `;
    }

    container.innerHTML = `
        <div class="quality-summary">

            <h3>
                Data Quality
            </h3>

            <div class="quality-grid">

                <div>
                    <strong>
                        Quality Score
                    </strong>

                    <span>
                        ${escapeHtml(
                            String(score)
                        )}
                    </span>
                </div>

                <div>
                    <strong>
                        Missing Values
                    </strong>

                    <span>
                        ${totalMissing}
                    </span>
                </div>

                <div>
                    <strong>
                        Duplicate Rows
                    </strong>

                    <span>
                        ${duplicateRows}
                    </span>
                </div>

                <div>
                    <strong>
                        Empty Columns
                    </strong>

                    <span>
                        ${emptyColumns}
                    </span>
                </div>

            </div>

            ${recommendationsHtml}

        </div>
    `;
}


// ============================================================
// CREATE CLEANING CONTROLS
// ============================================================

function createCleaningControls(
    fileId,
    data
) {

    const analysisCard =
        document.getElementById(
            "analysisCard"
        );

    if (!analysisCard) {
        return;
    }

    let container =
        document.getElementById(
            "cleaningControls"
        );

    if (!container) {

        container =
            document.createElement(
                "div"
            );

        container.id =
            "cleaningControls";

        container.style.marginTop =
            "20px";

        analysisCard.appendChild(
            container
        );
    }

    const summary =
        data.summary || {};

    const missing =
        summary.missing_values || 0;

    const duplicates =
        summary.duplicate_rows || 0;

    container.innerHTML = `
        <div class="cleaning-section">

            <h3>
                Data Cleaning
            </h3>

            <!-- ========================================= -->
            <!-- MISSING VALUES                            -->
            <!-- ========================================= -->

            <div class="cleaning-tool">

                <h4>
                    Missing Values
                </h4>

                <p>
                    Detected:
                    <strong>
                        ${missing}
                    </strong>
                </p>

                <label for="missingStrategy">
                    Cleaning Method
                </label>

                <select
                    id="missingStrategy"
                >

                    <option value="mean">
                        Mean
                    </option>

                    <option value="median">
                        Median
                    </option>

                    <option value="mode">
                        Mode
                    </option>

                    <option value="custom">
                        Custom Value
                    </option>

                    <option value="drop_rows">
                        Drop Rows
                    </option>

                </select>

                <input
                    type="text"
                    id="customMissingValue"
                    placeholder="Custom value"
                    style="display:none;"
                />

                <button
                    type="button"
                    id="cleanMissingButton"
                    onclick="cleanMissingValues(${fileId})"
                >
                    Clean Missing Values
                </button>

                <div
                    id="missingCleaningResult"
                    style="margin-top:10px;"
                ></div>

            </div>


            <!-- ========================================= -->
            <!-- DUPLICATES                                -->
            <!-- ========================================= -->

            <div class="cleaning-tool">

                <h4>
                    Duplicate Rows
                </h4>

                <p>
                    Detected:
                    <strong>
                        ${duplicates}
                    </strong>
                </p>

                <button
                    type="button"
                    id="cleanDuplicatesButton"
                    onclick="cleanDuplicateRows(${fileId})"
                >
                    Remove Duplicate Rows
                </button>

                <div
                    id="duplicateCleaningResult"
                    style="margin-top:10px;"
                ></div>

            </div>

        </div>
    `;

    const strategySelect =
        document.getElementById(
            "missingStrategy"
        );

    const customInput =
        document.getElementById(
            "customMissingValue"
        );

    if (
        strategySelect &&
        customInput
    ) {

        strategySelect.addEventListener(
            "change",
            function () {

                if (
                    strategySelect.value ===
                    "custom"
                ) {

                    customInput.style.display =
                        "block";

                } else {

                    customInput.style.display =
                        "none";
                }
            }
        );
    }
}


// ============================================================
// CLEAN MISSING VALUES
// ============================================================

async function cleanMissingValues(
    fileId
) {

    const strategySelect =
        document.getElementById(
            "missingStrategy"
        );

    const customInput =
        document.getElementById(
            "customMissingValue"
        );

    const button =
        document.getElementById(
            "cleanMissingButton"
        );

    const resultContainer =
        document.getElementById(
            "missingCleaningResult"
        );

    if (!strategySelect) {
        return;
    }

    const strategy =
        strategySelect.value;

    const customValue =
        customInput
            ? customInput.value
            : null;

    if (
        strategy === "custom" &&
        !customValue
    ) {

        alert(
            "Please enter a custom value."
        );

        return;
    }

    if (button) {

        button.disabled =
            true;

        button.textContent =
            "Cleaning...";
    }

    try {

        const response =
            await fetch(
                `/api/files/${fileId}/clean-missing?user_id=${encodeURIComponent(user.id)}`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        user_id: user.id,
                        strategy: strategy,
                        custom_value:
                            customValue
                    })
                }
            );

        const data =
            await response.json();

        if (
            !response.ok ||
            !data.success
        ) {

            throw new Error(
                data.message ||
                "Could not clean missing values."
            );
        }

        const summary =
            data.summary || {};

        if (resultContainer) {

            resultContainer.innerHTML = `
                <div class="success-message">

                    <strong>
                        Missing-value cleaning completed.
                    </strong>

                    <br><br>

                    Strategy:
                    ${escapeHtml(
                        String(
                            summary.strategy ||
                            strategy
                        )
                    )}

                    <br>

                    Missing values fixed:
                    ${summary.fixed_missing ?? 0}

                    <br>

                    Remaining missing:
                    ${summary.remaining_missing ?? 0}

                    <br>

                    Cleaned file:
                    <strong>
                        ${escapeHtml(
                            data.cleaned_file?.filename ||
                            ""
                        )}
                    </strong>

                </div>
            `;
        }

        if (button) {

            button.textContent =
                "Missing Values Cleaned";

            button.disabled =
                true;
        }

    } catch (error) {

        console.error(
            "Missing-value cleaning error:",
            error
        );

        if (resultContainer) {

            resultContainer.innerHTML = `
                <div class="error-message">
                    ${escapeHtml(
                        error.message ||
                        "Could not clean missing values."
                    )}
                </div>
            `;
        }

        if (button) {

            button.disabled =
                false;

            button.textContent =
                "Clean Missing Values";
        }
    }
}


// ============================================================
// CLEAN DUPLICATE ROWS
// ============================================================

async function cleanDuplicateRows(
    fileId
) {

    const button =
        document.getElementById(
            "cleanDuplicatesButton"
        );

    const resultContainer =
        document.getElementById(
            "duplicateCleaningResult"
        );

    if (button) {

        button.disabled =
            true;

        button.textContent =
            "Removing Duplicates...";
    }

    try {

        const response =
            await fetch(
                `/api/files/${fileId}/clean-duplicates?user_id=${encodeURIComponent(user.id)}`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        user_id: user.id
                    })
                }
            );

        const data =
            await response.json();

        if (
            !response.ok ||
            !data.success
        ) {

            throw new Error(
                data.message ||
                "Could not remove duplicate rows."
            );
        }

        const summary =
            data.summary || {};

        if (resultContainer) {

            resultContainer.innerHTML = `
                <div class="success-message">

                    <strong>
                        Duplicate cleaning completed.
                    </strong>

                    <br><br>

                    Original rows:
                    ${summary.original_rows ?? 0}

                    <br>

                    Duplicates removed:
                    ${summary.duplicates_removed ?? 0}

                    <br>

                    Final rows:
                    ${summary.final_rows ?? 0}

                    <br>

                    Cleaned file:
                    <strong>
                        ${escapeHtml(
                            data.cleaned_file?.filename ||
                            ""
                        )}
                    </strong>

                </div>
            `;
        }

        if (button) {

            button.textContent =
                "Duplicates Removed";

            button.disabled =
                true;
        }

    } catch (error) {

        console.error(
            "Duplicate cleaning error:",
            error
        );

        if (resultContainer) {

            resultContainer.innerHTML = `
                <div class="error-message">
                    ${escapeHtml(
                        error.message ||
                        "Could not remove duplicate rows."
                    )}
                </div>
            `;
        }

        if (button) {

            button.disabled =
                false;

            button.textContent =
                "Remove Duplicate Rows";
        }
    }
}


// ============================================================
// EMPTY COLUMN DETECTION
// ============================================================

async function loadEmptyColumns(
    fileId
) {

    try {

        const response =
            await fetch(
                `/api/files/${fileId}/empty-columns?user_id=${encodeURIComponent(user.id)}`
            );

        const data =
            await response.json();

        if (
            !response.ok ||
            !data.success
        ) {

            throw new Error(
                data.message ||
                "Could not detect empty columns."
            );
        }

        displayEmptyColumns(
            data
        );

    } catch (error) {

        console.error(
            "Empty column detection error:",
            error
        );

        const container =
            document.getElementById(
                "emptyColumnsSection"
            );

        if (container) {

            container.innerHTML = `
                <div class="error-message">
                    Could not detect empty columns.
                </div>
            `;
        }
    }
}


// ============================================================
// DISPLAY EMPTY COLUMNS
// ============================================================

function displayEmptyColumns(
    data
) {

    const analysisCard =
        document.getElementById(
            "analysisCard"
        );

    if (!analysisCard) {
        return;
    }

    let section =
        document.getElementById(
            "emptyColumnsSection"
        );

    if (!section) {

        section =
            document.createElement(
                "div"
            );

        section.id =
            "emptyColumnsSection";

        section.style.marginTop =
            "20px";

        analysisCard.appendChild(
            section
        );
    }

    const emptyColumns =
        data.empty_columns || [];

    if (
        emptyColumns.length === 0
    ) {

        section.innerHTML = `
            <div class="cleaning-section">

                <h3>
                    Empty Columns
                </h3>

                <p>
                    No completely empty columns were found.
                </p>

            </div>
        `;

        return;
    }

    let columnsHtml = "";

    emptyColumns.forEach(
        function (column) {

            columnsHtml += `
                <tr>

                    <td>
                        ${escapeHtml(
                            column.name
                        )}
                    </td>

                    <td>
                        ${column.missing}
                    </td>

                    <td>
                        ${column.percentage}%
                    </td>

                </tr>
            `;
        }
    );

    section.innerHTML = `
        <div class="cleaning-section">

            <h3>
                Empty Columns
            </h3>

            <p>
                Found
                <strong>
                    ${emptyColumns.length}
                </strong>
                completely empty column(s).
            </p>

            <div class="table-container">

                <table>

                    <thead>

                        <tr>

                            <th>
                                Column
                            </th>

                            <th>
                                Missing Values
                            </th>

                            <th>
                                Empty %
                            </th>

                        </tr>

                    </thead>

                    <tbody>

                        ${columnsHtml}

                    </tbody>

                </table>

            </div>

            <button
                type="button"
                id="cleanEmptyColumnsButton"
                onclick="cleanEmptyColumns(${data.file.id})"
            >
                Remove Empty Columns
            </button>

            <div
                id="emptyColumnsResult"
                style="margin-top:12px;"
            ></div>

        </div>
    `;
}


// ============================================================
// CLEAN EMPTY COLUMNS
// ============================================================

async function cleanEmptyColumns(
    fileId
) {

    const button =
        document.getElementById(
            "cleanEmptyColumnsButton"
        );

    const resultContainer =
        document.getElementById(
            "emptyColumnsResult"
        );

    if (button) {

        button.disabled =
            true;

        button.textContent =
            "Removing Empty Columns...";
    }

    try {

        const response =
            await fetch(
                `/api/files/${fileId}/clean-empty-columns?user_id=${encodeURIComponent(user.id)}`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        user_id: user.id
                    })
                }
            );

        const data =
            await response.json();

        if (
            !response.ok ||
            !data.success
        ) {

            throw new Error(
                data.message ||
                "Could not clean empty columns."
            );
        }

        const summary =
            data.summary || {};

        if (resultContainer) {

            resultContainer.innerHTML = `
                <div class="success-message">

                    <strong>
                        Empty-column cleaning completed.
                    </strong>

                    <br><br>

                    Original columns:
                    ${summary.original_columns ?? 0}

                    <br>

                    Empty columns found:
                    ${summary.empty_columns_found ?? 0}

                    <br>

                    Columns removed:
                    ${summary.columns_removed ?? 0}

                    <br>

                    Final columns:
                    ${summary.final_columns ?? 0}

                    <br><br>

                    Cleaned file:
                    <strong>
                        ${escapeHtml(
                            data.cleaned_file?.filename ||
                            ""
                        )}
                    </strong>

                </div>
            `;
        }

        if (button) {

            button.textContent =
                "Empty Columns Removed";

            button.disabled =
                true;
        }

    } catch (error) {

        console.error(
            "Empty column cleaning error:",
            error
        );

        if (resultContainer) {

            resultContainer.innerHTML = `
                <div class="error-message">

                    ${escapeHtml(
                        error.message ||
                        "Could not clean empty columns."
                    )}

                </div>
            `;
        }

        if (button) {

            button.disabled =
                false;

            button.textContent =
                "Remove Empty Columns";
        }
    }
}


// ============================================================
// UTILITY - SET TEXT
// ============================================================

function setText(
    elementId,
    value
) {

    const element =
        document.getElementById(
            elementId
        );

    if (element) {

        element.textContent =
            value ?? 0;
    }
}


// ============================================================
// UTILITY - SHOW MESSAGE
// ============================================================

function showMessage(
    element,
    message,
    success = false
) {

    if (!element) {
        return;
    }

    element.textContent =
        message;

    element.classList.remove(
        "success-message",
        "error-message"
    );

    element.classList.add(
        success
            ? "success-message"
            : "error-message"
    );
}


// ============================================================
// UTILITY - FILE SIZE
// ============================================================

function formatFileSize(
    bytes
) {

    if (
        bytes === null ||
        bytes === undefined
    ) {

        return "Unknown size";
    }

    if (bytes === 0) {
        return "0 Bytes";
    }

    const units = [
        "Bytes",
        "KB",
        "MB",
        "GB"
    ];

    const index =
        Math.floor(
            Math.log(bytes) /
            Math.log(1024)
        );

    const size =
        bytes /
        Math.pow(
            1024,
            index
        );

    return (
        size.toFixed(
            index === 0 ? 0 : 2
        )
        +
        " "
        +
        units[index]
    );
}


// ============================================================
// UTILITY - FORMAT CELL VALUE
// ============================================================

function formatCellValue(
    value
) {

    if (
        value === null ||
        value === undefined
    ) {

        return "";
    }

    if (
        typeof value === "object"
    ) {

        try {

            return JSON.stringify(
                value
            );

        } catch (error) {

            return String(
                value
            );
        }
    }

    return String(
        value
    );
}


// ============================================================
// UTILITY - HTML ESCAPE
// ============================================================

function escapeHtml(
    value
) {

    if (
        value === null ||
        value === undefined
    ) {

        return "";
    }

    return String(
        value
    )
        .replace(
            /&/g,
            "&amp;"
        )
        .replace(
            /</g,
            "&lt;"
        )
        .replace(
            />/g,
            "&gt;"
        )
        .replace(
            /"/g,
            "&quot;"
        )
        .replace(
            /'/g,
            "&#039;"
        );
}