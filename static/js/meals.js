

function $(id) {
  return document.getElementById(id);
}

function safeNumber(value, fallback = 0) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function parseJsonOrNull(raw) {
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch (_) {
    return null;
  }
}


function getSelectedIngredientIds() {
  const raw = ($("ingredient-ids")?.value || "").trim();
  if (!raw) return [];
  return raw.split(",").map(s => s.trim()).filter(Boolean);
}

function setSelectedIngredientIds(ids) {
  if ($("ingredient-ids")) {
    $("ingredient-ids").value = ids.join(",");
  }
}

function getPortionsList() {
  const raw = ($("ingredients-portions")?.value || "").trim();
  const parsed = parseJsonOrNull(raw);
  return Array.isArray(parsed) ? parsed : [];
}

function setPortionsList(portions) {
  if ($("ingredients-portions")) {
    $("ingredients-portions").value = JSON.stringify(portions || []);
  }
}

function upsertPortion(ingredientId, gramsUsed) {
  const portions = getPortionsList();
  const id = String(ingredientId);

  const grams = Math.max(0, safeNumber(gramsUsed, 0));
  const existingIdx = portions.findIndex(p => String(p.ingredient_id) === id);

  const portionObj = { ingredient_id: id, grams_used: grams };

  if (existingIdx >= 0) portions[existingIdx] = portionObj;
  else portions.push(portionObj);

  setPortionsList(portions);
}

const ingredientCache = new Map(); // id => {id,name,calories,...,serving_grams}

function renderSelectedIngredients() {
  const listEl = $("selected-ingredients-list");
  if (!listEl) return;

  const ids = getSelectedIngredientIds();

  // Empty state
  if (ids.length === 0) {
    listEl.innerHTML = `
      <li class="list-group-item text-muted">No ingredients added yet</li>
    `;
    return;
  }

  const portions = getPortionsList();
  const gramsLookup = new Map(portions.map(p => [String(p.ingredient_id), safeNumber(p.grams_used, 0)]));

  listEl.innerHTML = ids.map(id => {
    const ing = ingredientCache.get(id);
    const name = ing?.name || "Unknown ingredient";
    const grams = gramsLookup.get(id) ?? 100; // default UI grams shown
    const servingHint = ing?.serving_grams ? ` (serving: ${ing.serving_grams}g)` : "";

    return `
      <li class="list-group-item d-flex justify-content-between align-items-center">
        <div style="flex:1;">
          <div><strong>${escapeHtml(name)}</strong>${servingHint}</div>
          <small class="text-muted">Set grams used for accurate macro calculation</small>
        </div>

        <div class="d-flex align-items-center gap-2">
          <input
            type="number"
            min="0"
            step="1"
            class="form-control form-control-sm"
            style="width: 110px;"
            value="${grams}"
            data-grams-for="${id}"
            title="grams used"
          />
          <button type="button" class="btn btn-sm btn-outline-danger" data-remove-ingredient="${id}">
            Remove
          </button>
        </div>
      </li>
    `;
  }).join("");

  // Hook events: grams inputs + remove buttons
  listEl.querySelectorAll("[data-grams-for]").forEach(input => {
    input.addEventListener("change", (e) => {
      const ingId = e.target.getAttribute("data-grams-for");
      const gramsUsed = e.target.value;
      upsertPortion(ingId, gramsUsed);
    });
  });

  listEl.querySelectorAll("[data-remove-ingredient]").forEach(btn => {
    btn.addEventListener("click", (e) => {
      const ingId = e.target.getAttribute("data-remove-ingredient");
      removeSelectedIngredient(ingId);
    });
  });
}

function addSelectedIngredient(ingredient) {
  const id = String(ingredient.id);
  ingredientCache.set(id, ingredient);

  const ids = getSelectedIngredientIds();
  if (!ids.includes(id)) {
    ids.push(id);
    setSelectedIngredientIds(ids);
  }

  // Default grams to 100 if not set
  const portions = getPortionsList();
  if (!portions.some(p => String(p.ingredient_id) === id)) {
    portions.push({ ingredient_id: id, grams_used: 100 });
    setPortionsList(portions);
  }

  renderSelectedIngredients();
}

function removeSelectedIngredient(ingredientId) {
  const id = String(ingredientId);

  // Remove from ids list
  const ids = getSelectedIngredientIds().filter(x => x !== id);
  setSelectedIngredientIds(ids);

  // Remove portion entry
  const portions = getPortionsList().filter(p => String(p.ingredient_id) !== id);
  setPortionsList(portions);

  renderSelectedIngredients();
}


function escapeHtml(str) {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function runIngredientSearch(query) {
  const trimmed = (query || "").trim();
  const resultsEl = $("ingredient-results");
  if (!resultsEl) return;

  if (!trimmed) {
    resultsEl.innerHTML = "";
    return;
  }

  resultsEl.innerHTML = `<li class="list-group-item text-muted">Searching...</li>`;

  try {
    const data = await apiRequest(`/api/ingredients/search?query=${encodeURIComponent(trimmed)}`);
    const results = Array.isArray(data.results) ? data.results : [];

    if (results.length === 0) {
      resultsEl.innerHTML = `<li class="list-group-item text-muted">No results</li>`;
      return;
    }

    resultsEl.innerHTML = results.map(r => `
      <li class="list-group-item d-flex justify-content-between align-items-center">
        <div>
          <strong>${escapeHtml(r.name)}</strong>
          <div class="text-muted small">${safeNumber(r.calories, 0)} kcal</div>
        </div>
        <button type="button" class="btn btn-sm btn-outline-primary" data-add-ingredient="${escapeHtml(r.id)}">
          Add
        </button>
      </li>
    `).join("");

    // attach add handlers
    resultsEl.querySelectorAll("[data-add-ingredient]").forEach(btn => {
      btn.addEventListener("click", () => {
        const ingId = btn.getAttribute("data-add-ingredient");
        const ingredient = results.find(x => String(x.id) === String(ingId));
        if (ingredient) addSelectedIngredient(ingredient);
      });
    });
  } catch (err) {
    resultsEl.innerHTML = `<li class="list-group-item text-danger">${escapeHtml(err.message)}</li>`;
  }
}

async function handleAddMealSubmit(e) {
  e.preventDefault();

  const name = ($("name")?.value || "").trim();
  const description = ($("description")?.value || "").trim();

  if (!name) {
    alert("Meal name is required");
    return;
  }

  const ingredientIds = getSelectedIngredientIds();
  const payload = { name, description };

  if (ingredientIds.length > 0) {
    payload.ingredient_ids = ingredientIds;

    const portions = getPortionsList();
    if (Array.isArray(portions) && portions.length) {
      payload.ingredients_portions = portions;
    }
  } else {
    // Manual macros path
    payload.calories = safeNumber($("calories")?.value, 0);
    payload.protein = safeNumber($("protein")?.value, 0);
    payload.fat = safeNumber($("fat")?.value, 0);
    payload.carbs = safeNumber($("carbs")?.value, 0);
  }

  try {
    await apiRequest("/api/meals", { method: "POST", json: payload });
    window.location.href = "/my_meals";
  } catch (err) {
    alert(err.message);
  }
}


async function logMeal(mealId) {
  try {
    await apiRequest(`/api/meals/${mealId}/log`, { method: "POST" });
    window.location.reload();
  } catch (err) {
    alert(err.message);
  }
}

async function unlogMeal(mealId) {
  try {
    await apiRequest(`/api/meals/${mealId}/unlog`, { method: "POST" });
    window.location.reload();
  } catch (err) {
    alert(err.message);
  }
}

async function deleteMeal(mealId) {
  if (!confirm("Are you sure?")) return;

  try {
    await apiRequest(`/api/meals/${mealId}`, { method: "DELETE" });
    window.location.reload();
  } catch (err) {
    alert(err.message);
  }
}


document.addEventListener("DOMContentLoaded", () => {
  // Expose to global for inline onclick usage
  window.logMeal = logMeal;
  window.unlogMeal = unlogMeal;
  window.deleteMeal = deleteMeal;

  // Add meal page:
  const addMealForm = $("addMealForm");
  if (addMealForm) {
    addMealForm.addEventListener("submit", handleAddMealSubmit);

    // Ingredient search button + Enter key
    const searchInput = $("ingredient-search");
    const searchBtn = $("ingredient-search-btn");

    if (searchBtn) {
      searchBtn.addEventListener("click", () => runIngredientSearch(searchInput?.value || ""));
    }
    if (searchInput) {
      searchInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          runIngredientSearch(searchInput.value);
        }
      });
    }

    // Render selected ingredients on load (in case hidden fields already have values)
    renderSelectedIngredients();
  }
});
