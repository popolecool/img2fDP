// background.js

// This file contains the background script for the Firefox extension.
// It handles events and communicates with the content script.

// Listen for the extension installation or upgrade event
browser.runtime.onInstalled.addListener((details) => {
  if (details.reason === "install") {
    // Extension was installed, do any necessary setup here
    console.log("Extension installed");
  } else if (details.reason === "update") {
    // Extension was updated, handle any necessary updates here
    console.log("Extension updated");
  }
});

// Handle messages from the content script
browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "applyBorderRadius") {
    // Apply border radius to all images on the web page
    const images = document.querySelectorAll("img");
    images.forEach((image) => {
      image.style.borderRadius = "10px";
    });
    sendResponse({ success: true });
  }
});