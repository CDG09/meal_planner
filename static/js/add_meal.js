

function byId(id) {
  return document.getElementById(id);
}

function num(v) {
  const n = Number(v);
  return Number.isFinite(n) ? n : 0;
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderSearchResults(results) {
  const list = byId("ingredient-results");
  list.innerHTML = "";

  if (!results || results.length === 0) {
    list.innerHTML = `<li class="list-group-item text-muted">No results</li>`;
    return;
  }

  for (const r of results) {
    const li = document.createElement("li");
    li.className = "list-group-item d-flex justify-content-between align-items-center";

    li.innerHTML = `
      <div>
        <strong>${escapeHtml(r.name)}</strong><br>
        <small class="text-muted">
          ${Number(r.calories || 0).toFixed(0)} kcal —
          P ${Number(r.protein || 0).toFixed(1)} /
          F ${Number(r.fat || 0).toFixed(1)} /
          C ${Number(r.carbs || 0).toFixed(1)}
        </small>
      </div>
      <button type="button" class="btn btn-sm btn-primary">Add</button>
    `;

    li.querySelector("button").addEventListener("click", () => addSelectedIngredient(r));
    list.appendChild(li);
  }
}

// ---- Selected ingredient state ----
const selected = new Map();

function syncHiddenInputs() {
  byId("ingredient-ids").value = Array.from(selected.keys()).join(",");

  const portions = Array.from(selected.entries()).map(([id, obj]) => ({
    ingredient_id: id,
    grams_used: obj.grams_used,
  }));
  byId("ingredients-portions").value = JSON.stringify(portions);
}

function recalcAndFillMacros() {
  // If there are ingredients selected, calculate scaled totals and write into inputs.
  if (selected.size === 0) return;

  let totals = { calories: 0, protein: 0, fat: 0, carbs: 0 };

  for (const [, obj] of selected.entries()) {
    const ing = obj.ingredient;

    const perServingCals = num(ing.calories);
    const perServingP = num(ing.protein);
    const perServingF = num(ing.fat);
    const perServingC = num(ing.carbs);

    const servingGrams = num(ing.serving_grams || 100) || 100;
    const gramsUsed = num(obj.grams_used);

    const mult = servingGrams > 0 ? (gramsUsed / servingGrams) : 0;

    totals.calories += perServingCals * mult;
    totals.protein += perServingP * mult;
    totals.fat += perServingF * mult;
    totals.carbs += perServingC * mult;
  }

  byId("calories").value = totals.calories.toFixed(1);
  byId("protein").value = totals.protein.toFixed(1);
  byId("fat").value = totals.fat.toFixed(1);
  byId("carbs").value = totals.carbs.toFixed(1);

  byId("calories").readOnly = true;
  byId("protein").readOnly = true;
  byId("fat").readOnly = true;
  byId("carbs").readOnly = true;
}

function setMacrosEditableIfNoIngredients() {
  const ro = selected.size > 0;
  byId("calories").readOnly = ro;
  byId("protein").readOnly = ro;
  byId("fat").readOnly = ro;
  byId("carbs").readOnly = ro;

  if (!ro) {

  }
}

function renderSelectedIngredients() {
  const ul = byId("selected-ingredients-list");
  ul.innerHTML = "";

  if (selected.size === 0) {
    ul.innerHTML = `<li class="list-group-item text-muted">No ingredients added yet</li>`;
    syncHiddenInputs();
    setMacrosEditableIfNoIngredients();
    return;
  }

  for (const [id, obj] of selected.entries()) {
    const ing = obj.ingredient;

    const li = document.createElement("li");
    li.className = "list-group-item d-flex justify-content-between align-items-center";

    li.innerHTML = `
      <div class="me-2">
        <strong>${escapeHtml(ing.name)}</strong>
        <div class="text-muted small">
          ${Number(ing.calories || 0).toFixed(0)} kcal (per serving) •
          serving grams: ${Number(ing.serving_grams || 100).toFixed(0)}g
        </div>
      </div>

      <div class="d-flex gap-2 align-items-center">
        <input type="number" min="0" step="1" class="form-control form-control-sm" style="width:110px"
               value="${obj.grams_used}" aria-label="grams used">
        <button type="button" class="btn btn-sm btn-outline-danger">Remove</button>
      </div>
    `;

    const gramsInput = li.querySelector("input");
    gramsInput.addEventListener("input", () => {
      obj.grams_used = Math.max(0, num(gramsInput.value));
      syncHiddenInputs();
      recalcAndFillMacros();
    });

    li.querySelector("button").addEventListener("click", () => {
      selected.delete(id);
      renderSelectedIngredients();
      if (selected.size === 0) setMacrosEditableIfNoIngredients();
      else recalcAndFillMacros();
    });

    ul.appendChild(li);
  }

  syncHiddenInputs();
  recalcAndFillMacros();
}

function addSelectedIngredient(ingredient) {
  const id = String(ingredient.id);

  if (!selected.has(id)) {
    const defaultGrams = num(ingredient.serving_grams || 100) || 100;
    selected.set(id, { ingredient, grams_used: defaultGrams });
  }

  renderSelectedIngredients();
}

// ---- API calls ----
async function searchIngredients(query) {
  const res = await apiRequest(`/api/ingredients/search?query=${encodeURIComponent(query)}`);
  return res.results || [];
}

function csvToList(s) {
  return (s || "").split(",").map(x => x.trim()).filter(Boolean);
}

function safeJsonParse(s, fallback) {
  try { return JSON.parse(s); } catch { return fallback; }
}

async function handleAddMealSubmit(e) {
  e.preventDefault();

  const name = (byId("name").value || "").trim();
  const description = (byId("description").value || "").trim();

  if (!name) {
    alert("Meal name is required");
    return;
  }

  const ingredientIds = csvToList(byId("ingredient-ids").value);
  const portions = safeJsonParse(byId("ingredients-portions").value || "[]", []);

  const payload = { name, description };

  if (ingredientIds.length > 0) {
    payload.ingredient_ids = ingredientIds;
    payload.ingredients_portions = Array.isArray(portions) ? portions : [];
  } else {
    payload.calories = num(byId("calories").value);
    payload.protein = num(byId("protein").value);
    payload.fat = num(byId("fat").value);
    payload.carbs = num(byId("carbs").value);
  }

  try {
    await apiRequest("/api/meals", { method: "POST", json: payload });
    window.location.href = "/my_meals";
  } catch (err) {
    alert(err.message);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const searchInput = byId("ingredient-search");
  const searchBtn = byId("ingredient-search-btn");

  if (searchInput && searchBtn) {
    searchBtn.addEventListener("click", async () => {
      const q = (searchInput.value || "").trim();
      if (!q) {
        renderSearchResults([]);
        return;
      }

      try {
        const results = await searchIngredients(q);
        renderSearchResults(results);
      } catch (err) {
        alert(err.message);
        renderSearchResults([]);
      }
    });

    searchInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        searchBtn.click();
      }
    });
  }

  const form = byId("addMealForm");
  if (form) form.addEventListener("submit", handleAddMealSubmit);

  renderSelectedIngredients();
});
