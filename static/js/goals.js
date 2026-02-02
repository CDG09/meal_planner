

function getEl(form, name) {
  return form.querySelector(`[name="${name}"]`);
}

function getFormString(form, name) {
  const el = getEl(form, name);
  return (el && el.value ? String(el.value) : "").trim();
}

function getFormNumber(form, name) {
  const raw = getFormString(form, name);
  if (raw === "") return NaN;
  return Number(raw);
}

function getFormInt(form, name) {
  const raw = getFormString(form, name);
  if (raw === "") return NaN;
  return Number.parseInt(raw, 10);
}

async function handleAddGoalSubmit(e) {
  e.preventDefault();

  const form = e.currentTarget;

  const payload = {
    weight: getFormNumber(form, "weight"),
    height: getFormNumber(form, "height"),
    age: getFormInt(form, "age"),
    sex: getFormString(form, "sex"),
    activity_level: getFormString(form, "activity_level"),
    goal_percent: getFormNumber(form, "goal_percent"),
  };

  // Basic front-end validation (prevents sending NaN)
  if (
    Number.isNaN(payload.weight) ||
    Number.isNaN(payload.height) ||
    Number.isNaN(payload.age) ||
    Number.isNaN(payload.goal_percent) ||
    !payload.sex ||
    !payload.activity_level
  ) {
    alert("Please fill in all fields correctly.");
    return;
  }

  try {
    await apiRequest("/api/goals", { method: "POST", json: payload });
    window.location.href = "/goals";
  } catch (err) {
    alert(err.message || "Failed to create goal.");
  }
}

async function handleEditGoalSubmit(e) {
  e.preventDefault();

  const form = e.currentTarget;
  const goalId = form.getAttribute("data-goal-id");

  if (!goalId) {
    alert("Missing goal id on form (data-goal-id).");
    return;
  }

  const payload = {
    weight: getFormNumber(form, "weight"),
    height: getFormNumber(form, "height"),
    age: getFormInt(form, "age"),
    goal_percent: getFormNumber(form, "goal_percent"),
  };

  if (
    Number.isNaN(payload.weight) ||
    Number.isNaN(payload.height) ||
    Number.isNaN(payload.age) ||
    Number.isNaN(payload.goal_percent)
  ) {
    alert("Please fill in all fields correctly.");
    return;
  }

  try {
    await apiRequest(`/api/goals/${goalId}`, { method: "PATCH", json: payload });
    window.location.href = "/goals";
  } catch (err) {
    alert(err.message || "Failed to update goal.");
  }
}

async function deleteGoal(goalId) {
  if (!confirm("Are you sure you want to delete this goal?")) return;

  try {
    await apiRequest(`/api/goals/${goalId}`, { method: "DELETE" });
    window.location.reload();
  } catch (err) {
    alert(err.message || "Failed to delete goal.");
  }
}

async function deleteGoalHistory() {
  if (!confirm("Are you sure you want to delete all goals?")) return;

  try {
    await apiRequest("/api/goals/history", { method: "DELETE" });
    window.location.reload();
  } catch (err) {
    alert(err.message || "Failed to delete goal history.");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  // Expose for inline onclick usage (e.g. goals.html buttons)
  window.deleteGoal = deleteGoal;
  window.deleteGoalHistory = deleteGoalHistory;

  const addForm = document.getElementById("addGoalForm");
  if (addForm && addForm.tagName === "FORM") {
    addForm.addEventListener("submit", handleAddGoalSubmit);
  }

  const editForm = document.getElementById("editGoalForm");
  if (editForm && editForm.tagName === "FORM") {
    editForm.addEventListener("submit", handleEditGoalSubmit);
  }
});
