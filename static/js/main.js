function normalize(text) {
    return (text || "").toLowerCase().trim();
}

function filterTeamCards() {
    const searchInput = document.getElementById("team-search");
    if (!searchInput) {
        return;
    }

    searchInput.addEventListener("input", () => {
        const query = normalize(searchInput.value);
        document.querySelectorAll(".team-card").forEach((card) => {
            const name = normalize(card.getAttribute("data-name"));
            card.style.display = name.includes(query) ? "" : "none";
        });
    });
}

function rebuildOptions(select, options, query) {
    select.innerHTML = "";

    options
        .filter((option) => !query || normalize(option.text).includes(query))
        .forEach((option) => {
            const optionElement = document.createElement("option");
            optionElement.value = option.value;
            optionElement.textContent = option.text;
            select.appendChild(optionElement);
        });
}

function selectFirstTeamOption(select) {
    const firstTeamIndex = Array.from(select.options).findIndex((option) => option.value);
    if (firstTeamIndex >= 0) {
        select.selectedIndex = firstTeamIndex;
    }
}

function wireComparisonAutocomplete() {
    document.querySelectorAll(".team-autocomplete").forEach((input) => {
        const targetId = input.getAttribute("data-target");
        const select = targetId ? document.getElementById(targetId) : null;
        if (!select) {
            return;
        }

        const allOptions = Array.from(select.options, (option) => ({
            value: option.value,
            text: option.textContent,
        }));

        input.addEventListener("input", () => {
            const query = normalize(input.value);
            rebuildOptions(select, allOptions, query);

            if (query) {
                selectFirstTeamOption(select);
            }
        });
    });
}

function parseNumericFilter(filterText) {
    const value = normalize(filterText);
    if (!value) {
        return () => true;
    }

    const rangeMatch = value.match(/^(-?\d+(?:\.\d+)?)\s*-\s*(-?\d+(?:\.\d+)?)$/);
    if (rangeMatch) {
        const min = Number(rangeMatch[1]);
        const max = Number(rangeMatch[2]);
        return (cellValue) => Number.isFinite(cellValue) && cellValue >= min && cellValue <= max;
    }

    const comparisonMatch = value.match(/^(<=|>=|=|<|>)(-?\d+(?:\.\d+)?)$/);
    if (comparisonMatch) {
        const operator = comparisonMatch[1];
        const target = Number(comparisonMatch[2]);
        return (cellValue) => {
            if (!Number.isFinite(cellValue)) {
                return false;
            }
            if (operator === "<") return cellValue < target;
            if (operator === "<=") return cellValue <= target;
            if (operator === ">") return cellValue > target;
            if (operator === ">=") return cellValue >= target;
            return cellValue === target;
        };
    }

    const exactValue = Number(value);
    if (!Number.isNaN(exactValue)) {
        return (cellValue) => Number.isFinite(cellValue) && cellValue === exactValue;
    }

    return () => true;
}

function readCellValue(cell, type) {
    const rawValue = cell.getAttribute("data-value") || "";
    if (type === "number") {
        if (rawValue === "") {
            return null;
        }
        const numericValue = Number(rawValue);
        return Number.isNaN(numericValue) ? null : numericValue;
    }
    return normalize(rawValue || cell.textContent);
}

function applyRawDataFilters(table, filters, summary, tournamentFilterValue, tournamentColumnIndex) {
    const rows = Array.from(table.tBodies[0].rows);
    let visibleCount = 0;

    rows.forEach((row) => {
        const matchesColumnFilters = filters.every((filter) => {
            const cell = row.cells[filter.index];
            const cellValue = readCellValue(cell, filter.type);

            if (filter.type === "number") {
                return parseNumericFilter(filter.value)(cellValue);
            }
            return cellValue.includes(normalize(filter.value));
        });
        const matchesTournamentFilter =
            !tournamentFilterValue ||
            (tournamentColumnIndex >= 0 &&
                readCellValue(row.cells[tournamentColumnIndex], "text") === tournamentFilterValue);
        const isVisible = matchesColumnFilters && matchesTournamentFilter;

        row.style.display = isVisible ? "" : "none";
        if (isVisible) {
            visibleCount += 1;
        }
    });

    if (summary) {
        summary.textContent = `${visibleCount} teams shown`;
    }
}

function sortRawDataTable(table, columnIndex, type, direction) {
    const tbody = table.tBodies[0];
    const rows = Array.from(tbody.rows);

    rows.sort((rowA, rowB) => {
        const valueA = readCellValue(rowA.cells[columnIndex], type);
        const valueB = readCellValue(rowB.cells[columnIndex], type);

        if (type === "number") {
            if (valueA === null && valueB === null) return 0;
            if (valueA === null) return 1;
            if (valueB === null) return -1;
            return direction === "asc" ? valueA - valueB : valueB - valueA;
        }

        return direction === "asc"
            ? String(valueA).localeCompare(String(valueB))
            : String(valueB).localeCompare(String(valueA));
    });

    rows.forEach((row) => tbody.appendChild(row));
}

function wireRawDataTable() {
    const table = document.querySelector("[data-raw-data-table]");
    if (!table) {
        return;
    }

    const summary = document.querySelector("[data-table-summary]");
    const filterInputs = Array.from(table.querySelectorAll(".column-filter"));
    const headers = Array.from(table.querySelectorAll(".sortable-header"));
    const tournamentFilter = document.querySelector("[data-tournament-filter]");
    const tournamentColumnIndex = filterInputs.findIndex(
        (input) => input.getAttribute("data-filter-key") === "made_tournament"
    );
    const tableState = { columnIndex: null, direction: "asc" };

    function refreshFilters() {
        const filters = filterInputs.map((filterInput, index) => ({
            index,
            type: filterInput.getAttribute("data-filter-type"),
            value: filterInput.value,
        }));
        const tournamentValue = tournamentFilter ? normalize(tournamentFilter.value) : "";
        applyRawDataFilters(table, filters, summary, tournamentValue, tournamentColumnIndex);
    }

    filterInputs.forEach((input) => {
        input.addEventListener("input", refreshFilters);
    });

    if (tournamentFilter) {
        tournamentFilter.addEventListener("change", refreshFilters);
    }

    headers.forEach((header, index) => {
        header.addEventListener("click", () => {
            const type = header.getAttribute("data-sort-type");
            const nextDirection =
                tableState.columnIndex === index && tableState.direction === "asc" ? "desc" : "asc";

            tableState.columnIndex = index;
            tableState.direction = nextDirection;

            headers.forEach((otherHeader) => {
                otherHeader.setAttribute("data-sort-direction", "");
            });
            header.setAttribute("data-sort-direction", nextDirection);

            sortRawDataTable(table, index, type, nextDirection);
        });
    });

    refreshFilters();
}

filterTeamCards();
wireComparisonAutocomplete();
wireRawDataTable();
