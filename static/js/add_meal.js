document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById("ingredient-search");
    const resultsList = document.getElementById("ingredient-results");
    const hiddenInput = document.getElementById("ingredient-ids");

    const selectedList = document.getElementById("selected-ingredients-list");
    const caloriesInput = document.getElementById("calories");
    const proteinInput = document.getElementById("protein");
    const fatInput = document.getElementById("fat");
    const carbsInput = document.getElementById("carbs");

    let selectedIngredients = [];
    let selectedIngredientData = {};
    let debounceTimer = null;

    // Sync selected ingredient IDs and full data to hidden inputs
    function updateHiddenInputs() {
        hiddenInput.value = selectedIngredients.join(',');
    }

    function toggleMacroInputs(disabled) {
        caloriesInput.disabled = disabled;
        proteinInput.disabled = disabled;
        fatInput.disabled = disabled;
        carbsInput.disabled = disabled;
    }

    function recalculateMacros() {
        let calories = 0, protein = 0, fat = 0, carbs = 0;

        Object.values(selectedIngredientData).forEach(food => {
            calories += food.calories || 0;
            protein += food.protein || 0;
            fat += food.fat || 0;
            carbs += food.carbs || 0;
        });

        caloriesInput.value = calories.toFixed(0);
        proteinInput.value = protein.toFixed(1);
        fatInput.value = fat.toFixed(1);
        carbsInput.value = carbs.toFixed(1);
    }

    function renderSelectedIngredients() {
        selectedList.innerHTML = "";

        if (selectedIngredients.length === 0) {
            const empty = document.createElement("li");
            empty.classList.add("list-group-item", "text-muted");
            empty.textContent = "No ingredients added yet";
            selectedList.appendChild(empty);
            updateHiddenInputs();
            toggleMacroInputs(false);
            return;
        }

        toggleMacroInputs(true);

        selectedIngredients.forEach(id => {
            const food = selectedIngredientData[id];
            if (!food) return;

            const li = document.createElement("li");
            li.classList.add("list-group-item", "d-flex", "justify-content-between", "align-items-center");

            const textWrap = document.createElement("div");
            textWrap.classList.add("me-3");

            const name = document.createElement("div");
            name.innerHTML = `<strong>${food.name}</strong>`;

            const macros = document.createElement("div");
            macros.classList.add("text-muted", "small");
            macros.textContent = `Calories: ${food.calories} | P ${food.protein} | F ${food.fat} | C ${food.carbs}`;

            textWrap.appendChild(name);
            textWrap.appendChild(macros);

            const btn = document.createElement("button");
            btn.classList.add("btn", "btn-sm", "btn-outline-danger");
            btn.textContent = "Remove";

            btn.addEventListener("click", () => {
                selectedIngredients = selectedIngredients.filter(i => i !== id);
                delete selectedIngredientData[id];

                renderSelectedIngredients();
                recalculateMacros();
                updateHiddenInputs();
            });

            li.appendChild(textWrap);
            li.appendChild(btn);
            selectedList.appendChild(li);
        });
    }

    function renderResults(foods) {
        resultsList.innerHTML = "";

        foods.forEach(food => {
            const id = food.id;

            const li = document.createElement("li");
            li.classList.add("list-group-item", "d-flex", "justify-content-between", "align-items-center");

            const textWrap = document.createElement("div");
            textWrap.classList.add("me-3");

            const name = document.createElement("div");
            name.innerHTML = `<strong>${food.name}</strong>`;

            const macros = document.createElement("div");
            macros.classList.add("text-muted", "small");
            macros.textContent = `Calories: ${food.calories} | P ${food.protein} | F ${food.fat} | C ${food.carbs}`;

            textWrap.appendChild(name);
            textWrap.appendChild(macros);

            const btn = document.createElement("button");
            btn.classList.add("btn", "btn-sm");

            if (selectedIngredients.includes(id)) {
                btn.classList.add("btn-secondary");
                btn.textContent = "Added";
                btn.disabled = true;
            } else {
                btn.classList.add("btn-success");
                btn.textContent = "Add";

                btn.addEventListener("click", () => {
                    selectedIngredients.push(id);
                    selectedIngredientData[id] = food;

                    renderSelectedIngredients();
                    recalculateMacros();
                    updateHiddenInputs();
                    renderResults(foods); // re-render to update Add buttons
                });
            }

            li.appendChild(textWrap);
            li.appendChild(btn);
            resultsList.appendChild(li);
        });
    }

    async function searchIngredients(query) {
        if (!query || query.length < 2) {
            resultsList.innerHTML = "";
            return;
        }

        try {
            const response = await fetch(`/search_ingredient?query=${encodeURIComponent(query)}`);
            if (!response.ok) return;

            const data = await response.json();
            renderResults(data.results || []);
        } catch (err) {
            console.error("Ingredient search failed:", err);
        }
    }

    searchInput.addEventListener("input", () => {
        clearTimeout(debounceTimer);
        const query = searchInput.value.trim();

        debounceTimer = setTimeout(() => {
            searchIngredients(query);
        }, 300);
    });
    renderSelectedIngredients();
});













