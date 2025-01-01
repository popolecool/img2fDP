// content.js

// Function to apply border radius to all images on the web page
function applyBorderRadiusToImages() {
  const images = document.getElementsByTagName('img');
  for (let i = 0; i < images.length; i++) {
    images[i].style.borderRadius = '10px'; // Change the border radius value as per your requirement
  }
}

// Execute the function when the web page finishes loading
window.addEventListener('load', applyBorderRadiusToImages);