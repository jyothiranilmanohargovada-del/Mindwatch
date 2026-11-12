/**
 * MindWatch 2.0 — Interactive Assessment Wizard
 * Supports one-question-per-screen, progress tracking, and validation.
 */
document.addEventListener("DOMContentLoaded", function () {
  const wizardForm = document.getElementById("wizardForm");
  if (!wizardForm) return;

  const steps = document.querySelectorAll(".wizard-step");
  const totalSteps = steps.length;
  let currentStep = 0;

  const progressBar = document.getElementById("progressBar");
  const progressText = document.getElementById("progressText");
  const prevBtn = document.getElementById("prevBtn");
  const nextBtn = document.getElementById("nextBtn");
  const skipBtn = document.getElementById("skipBtn");

  function updateView() {
    steps.forEach((step, idx) => {
      step.classList.toggle("active", idx === currentStep);
    });

    const percent = Math.round(((currentStep + 1) / totalSteps) * 100);
    if (progressBar) progressBar.style.width = percent + "%";
    if (progressText) progressText.textContent = `Question ${currentStep + 1} of ${totalSteps} (${percent}%)`;

    // Button states
    if (prevBtn) {
      prevBtn.style.display = currentStep === 0 ? "none" : "inline-flex";
    }

    if (nextBtn) {
      if (currentStep === totalSteps - 1) {
        nextBtn.textContent = "Complete Assessment →";
        nextBtn.classList.remove("btn-secondary");
        nextBtn.classList.add("btn-primary");
      } else {
        nextBtn.textContent = "Next Question →";
      }
    }
  }

  // Handle radio option card clicks
  document.querySelectorAll(".option-card").forEach(card => {
    card.addEventListener("click", function (e) {
      const radio = this.querySelector('input[type="radio"]');
      if (radio) {
        radio.checked = true;
        const parent = this.closest(".option-cards");
        parent.querySelectorAll(".option-card").forEach(c => c.classList.remove("selected"));
        this.classList.add("selected");
      }
    });
  });

  if (nextBtn) {
    nextBtn.addEventListener("click", function () {
      const currentInputs = steps[currentStep].querySelectorAll('input[type="radio"]');
      const isAnswered = Array.from(currentInputs).some(r => r.checked);

      if (!isAnswered) {
        alert("Please select an answer to continue.");
        return;
      }

      if (currentStep < totalSteps - 1) {
        currentStep++;
        updateView();
      } else {
        wizardForm.submit();
      }
    });
  }

  if (prevBtn) {
    prevBtn.addEventListener("click", function () {
      if (currentStep > 0) {
        currentStep--;
        updateView();
      }
    });
  }

  if (skipBtn) {
    skipBtn.addEventListener("click", function () {
      // Default to 0 (Not at all) if skipped
      const firstOption = steps[currentStep].querySelector('input[type="radio"][value="0"]');
      if (firstOption) firstOption.checked = true;

      if (currentStep < totalSteps - 1) {
        currentStep++;
        updateView();
      } else {
        wizardForm.submit();
      }
    });
  }

  updateView();
});
