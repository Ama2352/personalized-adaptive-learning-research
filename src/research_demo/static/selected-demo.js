"use strict";

let selectedCatalog;
let selectedRequest = 0;
const selectedGraphLabels = {NONE: "Tắt đồ thị", EXPERT: "Chuyên gia", LEARNED: "Học từ TRAIN"};

function selectedModelId() {
  const variant = $("selected-model").value;
  return variant === "A0" ? variant : variant + "_" + $("selected-graph").value;
}

function selectedStepTo(step) {
  $("selected-step").value = String(step);
  loadSelected().catch(fail);
}

function selectedGraphOptions() {
  const previous = $("selected-graph").value;
  const sources = selectedCatalog.models
    .filter(model => model.variant === $("selected-model").value)
    .map(model => model.graph_source);
  $("selected-graph").replaceChildren();
  option("selected-graph", sources, source => selectedGraphLabels[source]);
  if (sources.includes(previous)) $("selected-graph").value = previous;
}

async function loadSelected() {
  const request = ++selectedRequest;
  const query = new URLSearchParams({
    model: selectedModelId(),
    learner: $("selected-learner").value,
    step: $("selected-step").value
  });
  const snapshot = await get("/api/selected-replay?" + query);
  if (request !== selectedRequest) return;
  $("selected-step-label").textContent = snapshot.step + " / 209";
  $("selected-previous").disabled = snapshot.step === 0;
  $("selected-next").disabled = snapshot.step === 209;
  $("selected-probability").textContent = snapshot.probability.toFixed(6);
  $("selected-reference").textContent = "A0 ở cùng câu hỏi và lịch sử: " + snapshot.reference_probability.toFixed(6);
  $("selected-item").textContent = snapshot.item.id;
  $("selected-context").textContent = "Khái niệm " + snapshot.item.concept +
    " · độ khó " + snapshot.item.difficulty + ". Cửa sổ có " + snapshot.history_available +
    " tương tác trước, dùng " + snapshot.history_used + ".";

  $("selected-state").replaceChildren();
  for (const [concept, state] of Object.entries(snapshot.observed_concepts)) {
    tableRow("selected-state", [concept, state.observed, state.correct,
      state.last_probability === null ? "Chưa có" : state.last_probability.toFixed(6)]);
  }
  $("selected-edges").replaceChildren();
  for (const edge of snapshot.graph.edges) {
    tableRow("selected-edges", [edge.parent, edge.child, edge.weight.toFixed(3), edge.supported ? "Có" : "Chưa đủ"]);
  }
  const confidence = snapshot.graph.confidence_kind === "estimated_probability"
    ? "Trọng số từ độ ổn định dự báo trên TRAIN. "
    : "Trọng số cạnh cố định. ";
  $("selected-gate").textContent = snapshot.graph.source === "NONE"
    ? "A0 dùng nhánh KT không đồ thị."
    : confidence + (snapshot.graph.gate_kind === "learned" ? "Cổng học được. " : "Cổng cố định theo cấu hình. ") +
      "Giá trị cổng ở từng bước chưa ghi nhận trong artifact.";

  $("selected-route").replaceChildren();
  for (const event of snapshot.query_route) {
    const item = node("li");
    const button = node("button", event.step + " · " + event.item);
    button.type = "button";
    if (event.step === snapshot.step) button.setAttribute("aria-current", "step");
    button.addEventListener("click", () => selectedStepTo(event.step));
    item.append(button);
    $("selected-route").append(item);
  }
}

async function initSelected() {
  selectedCatalog = (await catalogPromise).selected_model_results;
  option("selected-model", ["A0", "A1", "A2", "A3"], variant => variant === "A3" ? "A3 · CG-AKT" : variant);
  selectedGraphOptions();
  option("selected-learner", selectedCatalog.learners.map(row => row.id),
    id => selectedCatalog.learners.find(row => row.id === id).label);
  $("selected-step").disabled = false;
  $("selected-model").addEventListener("change", () => {
    selectedGraphOptions();
    loadSelected().catch(fail);
  });
  for (const id of ["selected-graph", "selected-learner"]) {
    $(id).addEventListener("change", () => loadSelected().catch(fail));
  }
  $("selected-step").addEventListener("input", () => loadSelected().catch(fail));
  $("selected-previous").addEventListener("click", () => selectedStepTo(Math.max(0, Number($("selected-step").value) - 1)));
  $("selected-next").addEventListener("click", () => selectedStepTo(Math.min(209, Number($("selected-step").value) + 1)));
  for (const model of selectedCatalog.models) {
    tableRow("selected-metrics", [model.variant, selectedGraphLabels[model.graph_source], model.selected_epoch,
      ...["log_loss", "auc", "brier", "ece"].map(metric => model.metrics[metric].toFixed(6))]);
  }
  await loadSelected();
}

initSelected().catch(fail);
