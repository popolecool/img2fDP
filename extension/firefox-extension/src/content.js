// content.js

// Function to apply border radius to all images
function applyBorderRadius(radius) {
  const images = document.querySelectorAll("img");
  images.forEach((image) => {
    image.style.borderRadius = `${radius}px`;
  });
}

// Listen for messages from the background script
browser.runtime.onMessage.addListener((message) => {
  if (message.type === "applyBorderRadius") {
    applyBorderRadius(message.radius);
  }
});