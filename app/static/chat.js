/**
 * MindWatch 2.0 — Intelligent Support Chat Client
 */
(function () {
  const log = document.getElementById("log");
  const form = document.getElementById("chatform");
  const input = document.getElementById("msg");
  const tokenMeta = document.querySelector('meta[name="csrf"]');
  const token = tokenMeta ? tokenMeta.content : "";

  function scrollBottom() {
    log.scrollTop = log.scrollHeight;
  }

  function addMessage(text, cls, engine) {
    const bubble = document.createElement("div");
    bubble.className = "msg " + cls;

    if (engine === "crisis_safety") {
      bubble.classList.add("crisisbox");
    }

    bubble.textContent = text;

    if (cls === "bot" && engine) {
      const metaTag = document.createElement("div");
      metaTag.className = "mut";
      metaTag.style.fontSize = "11px";
      metaTag.style.marginTop = "6px";
      metaTag.style.opacity = "0.75";
      metaTag.textContent = engine === "ai" ? "✨ AI-Assisted Coping Guide" : (engine === "crisis_safety" ? "🚨 Emergency Safety Protocol" : "🛡️ Local Coping Guide");
      bubble.appendChild(metaTag);
    }

    log.appendChild(bubble);
    scrollBottom();
    return bubble;
  }

  function addResourceCards(resources) {
    if (!resources || !resources.length) return;
    const tray = document.createElement("div");
    tray.className = "msg bot crisisbox";
    tray.style.maxWidth = "95%";
    tray.style.background = "var(--danger-subtle)";
    tray.style.borderColor = "var(--danger)";

    const title = document.createElement("b");
    title.style.color = "var(--danger)";
    title.textContent = "Immediate Emergency & Support Helplines:";
    tray.appendChild(title);

    const list = document.createElement("ul");
    list.style.marginTop = "8px";
    list.style.paddingLeft = "18px";

    resources.forEach(function (r) {
      const item = document.createElement("li");
      item.style.marginBottom = "6px";
      item.innerHTML = "<strong>" + escapeHtml(r.name) + "</strong>: " + escapeHtml(r.contact);
      list.appendChild(item);
    });

    tray.appendChild(list);
    log.appendChild(tray);
    scrollBottom();
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  // Initial welcome message
  addMessage(
    "Hi, I'm MindWatch Support Assistant — an automated listener and coping guide, not a therapist or doctor. " +
    "How are you feeling today? You can share what's on your mind or tap one of the calming exercises below.",
    "bot",
    "local"
  );

  // Form submission
  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;

    addMessage(text, "me");
    input.value = "";

    // Show temporary typing indicator
    const typingIndicator = document.createElement("div");
    typingIndicator.className = "msg bot mut";
    typingIndicator.style.fontStyle = "italic";
    typingIndicator.textContent = "Listening and thinking...";
    log.appendChild(typingIndicator);
    scrollBottom();

    try {
      const r = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": token
        },
        body: JSON.stringify({ message: text })
      });

      if (typingIndicator.parentNode) {
        typingIndicator.parentNode.removeChild(typingIndicator);
      }

      const j = await r.json();
      addMessage(j.reply || "I'm here with you. Please feel free to write whenever you feel ready.", "bot", j.engine);

      if (j.resources && j.resources.length > 0) {
        addResourceCards(j.resources);
      }
    } catch (err) {
      if (typingIndicator.parentNode) {
        typingIndicator.parentNode.removeChild(typingIndicator);
      }
      addMessage("Connection error — please try sending your message again.", "bot", "local");
    }
  });

  // Quick Action Buttons
  window.triggerQuickExercise = function (keyword) {
    input.value = keyword;
    form.dispatchEvent(new Event("submit"));
  };
})();
