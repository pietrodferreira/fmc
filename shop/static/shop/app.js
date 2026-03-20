(function () {
  function isNumberInput(el) {
    return el && el.classList && el.classList.contains("qty-input");
  }

  function clampQuantity(input) {
    const min = input.getAttribute("min");
    const step = input.getAttribute("step");

    const minVal = min === null ? 0 : Number(min);
    const stepVal = step === null ? 1 : Number(step);

    let v = Number(input.value);
    if (!Number.isFinite(v)) v = minVal;
    if (v < minVal) v = minVal;

    // Normaliza para múltiplos do step (p/ manter inteiro, etc).
    if (stepVal > 0) {
      v = Math.round(v / stepVal) * stepVal;
    }

    // Evita valores decimais em campos que representam quantidade.
    if (Number.isInteger(minVal) && Number.isInteger(stepVal)) {
      v = Math.round(v);
    }

    input.value = String(v);
  }

  document.addEventListener("input", function (e) {
    const t = e.target;
    if (isNumberInput(t)) {
      // Só normaliza quando o usuário sai do campo (reduz “luta” com digitação).
    }
  });

  document.addEventListener("blur", function (e) {
    const t = e.target;
    if (isNumberInput(t)) clampQuantity(t);
  });
})();

