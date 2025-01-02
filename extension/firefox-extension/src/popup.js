// popup.js

document.getElementById("apply").addEventListener("click", () => {
  const radius = document.getElementById("radius").value;
  browser.runtime.sendMessage({
    type: "applyBorderRadius",
    radius: radius,
  });
});

document.getElementById("autoDecodeFDP").addEventListener("change", (event) => {
  const autoDecode = event.target.checked;
  browser.storage.local.set({ autoDecodeFDP: autoDecode }).then(() => {
    browser.runtime.sendMessage({
      type: "updateAutoDecodeFDP",
      autoDecode: autoDecode,
    });
  });
});

// Initialiser l'état de la case à cocher en fonction de la valeur stockée
document.addEventListener("DOMContentLoaded", () => {
  browser.storage.local.get("autoDecodeFDP").then((result) => {
    document.getElementById("autoDecodeFDP").checked = result.autoDecodeFDP || false;
  });
});