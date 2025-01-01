// background.js

// Listen for the extension installation or upgrade event
browser.runtime.onInstalled.addListener((details) => {
  if (details.reason === "install") {
    console.log("Extension installed");
  } else if (details.reason === "update") {
    console.log("Extension updated");
  }
});

// Handle messages from the content script
browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "applyBorderRadius") {
    browser.tabs.query({ active: true, currentWindow: true }).then((tabs) => {
      browser.tabs.sendMessage(tabs[0].id, {
        type: "applyBorderRadius",
        radius: message.radius,
      });
    });
    sendResponse({ success: true });
  }
});

// Listen for web requests
browser.webRequest.onBeforeRequest.addListener(
  async (details) => {
    const url = new URL(details.url);
    if (url.pathname.endsWith(".fdp")) {
      const autoDecode = await browser.storage.local.get("autoDecodeFDP");
      if (autoDecode.autoDecodeFDP) {
        const response = await fetch(details.url);
        const fdpData = await response.text();
        const imageData = hexToImage(fdpData);
        const blob = new Blob([imageData], { type: "image/jpeg" });
        const objectURL = URL.createObjectURL(blob);
        return { redirectUrl: objectURL };
      }
    }
  },
  { urls: ["<all_urls>"] },
  ["blocking"]
);

// Function to convert FDP to image (JavaScript version of the Python code)
function hexToImage(fdpData) {
  const hexLines = fdpData.split("\n");
  const isCompressed = hexLines[0].includes("x");

  let hexData = hexLines;
  if (isCompressed) {
    hexData = hexLines.map(decompressHexLine);
  }

  const height = hexData.length;
  const width = hexData[0].split(" ").length;
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d");
  const imageData = ctx.createImageData(width, height);

  for (let y = 0; y < height; y++) {
    const hexValues = hexData[y].split(" ");
    for (let x = 0; x < width; x++) {
      const hexColor = hexValues[x];
      const r = parseInt(hexColor.slice(0, 2), 16);
      const g = parseInt(hexColor.slice(2, 4), 16);
      const b = parseInt(hexColor.slice(4, 6), 16);
      const index = (y * width + x) * 4;
      imageData.data[index] = r;
      imageData.data[index + 1] = g;
      imageData.data[index + 2] = b;
      imageData.data[index + 3] = 255; // Alpha channel
    }
  }

  ctx.putImageData(imageData, 0, 0);
  return canvas.toDataURL("image/jpeg");
}

// Function to decompress hex line (JavaScript version of the Python code)
function decompressHexLine(compressedLine) {
  const decompressed = [];
  const tokens = compressedLine.trim().split(" ");
  tokens.forEach((token) => {
    if (token.includes("x")) {
      const [count, value] = token.split("x");
      for (let i = 0; i < parseInt(count, 10); i++) {
        decompressed.push(value);
      }
    } else {
      decompressed.push(token);
    }
  });
  return decompressed.join(" ");
}