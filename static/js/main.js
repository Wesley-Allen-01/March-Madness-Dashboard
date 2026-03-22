// Team search filter on index page
const searchInput = document.getElementById("team-search");
if (searchInput) {
    searchInput.addEventListener("input", function () {
        const query = this.value.toLowerCase();
        document.querySelectorAll(".team-card").forEach(function (card) {
            const name = card.getAttribute("data-name") || "";
            card.style.display = name.includes(query) ? "" : "none";
        });
    });
}

// Autocomplete filter for comparison page selects
document.querySelectorAll(".team-autocomplete").forEach(function (input) {
    const targetId = input.getAttribute("data-target");
    const select = document.getElementById(targetId);
    if (!select) return;

    // Store all options
    const allOptions = Array.from(select.options).map(function (opt) {
        return { value: opt.value, text: opt.textContent };
    });

    input.addEventListener("input", function () {
        const query = this.value.toLowerCase();
        select.innerHTML = "";

        allOptions.forEach(function (opt) {
            if (!query || opt.text.toLowerCase().includes(query)) {
                const option = document.createElement("option");
                option.value = opt.value;
                option.textContent = opt.text;
                select.appendChild(option);
            }
        });

        // Auto-select first match if there's a query
        if (query && select.options.length > 0) {
            // Skip the empty "Select a team" option if present
            for (let i = 0; i < select.options.length; i++) {
                if (select.options[i].value) {
                    select.selectedIndex = i;
                    break;
                }
            }
        }
    });
});
