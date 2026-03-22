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

filterTeamCards();
wireComparisonAutocomplete();
