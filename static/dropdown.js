function populateSelect(selectId, values, defaultText) {
    const select = document.getElementById(selectId);
    if (!select) return;

    select.innerHTML = "";
    let defaultOption = new Option(defaultText, "");
    defaultOption.disabled = true;
    defaultOption.selected = true;
    select.add(defaultOption);

    values.forEach(v => select.add(new Option(v, v)));
}

document.addEventListener("DOMContentLoaded", () => {
    populateSelect("state", states, "-- Select a State --");
    populateSelect("year", years, "-- Select a Year --");
    populateSelect("race", races, "-- Select a Race --");
    populateSelect("sex", sexes, "-- Select a Sex --");

    const stateSelect = document.getElementById("state");
    const countySelect = document.getElementById("county");

    if (stateSelect && countySelect) {
        countySelect.disabled = true;

        stateSelect.addEventListener("change", function () {
            const selectedState = this.value;
            countySelect.innerHTML = "";

            if (selectedState && stateCountyMap[selectedState]) {
                countySelect.disabled = false;

                let defaultOption = new Option("-- Select a County --", "");
                defaultOption.disabled = true;
                defaultOption.selected = true;
                countySelect.add(defaultOption);

                stateCountyMap[selectedState].forEach(county => {
                    countySelect.add(new Option(county, county));
                });
            } else {
                let defaultOption = new Option("-- Select a State First --", "");
                defaultOption.disabled = true;
                defaultOption.selected = true;
                countySelect.add(defaultOption);
                countySelect.disabled = true;
            }
        });
    }
    // Handle prediction display
    if (prediction) {
        const predictionBox = document.getElementById("prediction-box");
        const predictionText = document.getElementById("prediction-text");
        predictionText.textContent = "Predicted Life Expectancy: " + prediction;
        predictionBox.style.display = "block";
    }
});
