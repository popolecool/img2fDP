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
browser.runtime.onMessage.addListener((message) => {
  if (message.type === "applyBorderRadius") {
    applyBorderRadius(message.radius);
  } else if (message.type === "updateAutoDecodeFDP") {
    updateAutoDecodeFDP(message.autoDecode);
  }
});

// Function to apply border radius
function applyBorderRadius(radius) {
  // Apply logic to change border radius
  console.log(`Applying border radius: ${radius}`);
}

// Function to update auto decode FDP
function updateAutoDecodeFDP(autoDecode) {
  // Apply logic to update auto decode FDP
  console.log(`Updating auto decode FDP: ${autoDecode}`);
}

// Listen for web requests
browser.webRequest.onBeforeRequest.addListener(
  async (details) => {
    const url = new URL(details.url);
    if (url.pathname.endsWith(".fdp")) {
      const autoDecode = await browser.storage.local.get("autoDecodeFDP");
      if (autoDecode.autoDecodeFDP) {
        const newFileName = url.pathname.replace('.fdp', '.jpg');
        
        const response = await fetch(details.url);
        const fdpData = await response.text();
        const imageData = hexToImage(fdpData);
        const blob = new Blob([imageData], { type: "image/jpeg" });
        const objectURL = URL.createObjectURL(blob);
        
        browser.history.addUrl({
          url: objectURL,
          title: newFileName
        });
        
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
  // Conversion logic here
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