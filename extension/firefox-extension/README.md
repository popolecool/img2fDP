# Firefox Extension

This is a Firefox extension that applies a border radius to all images on web pages.

## Project Structure

```
firefox-extension
├── src
│   ├── background.js
│   ├── content.js
│   └── manifest.json
├── README.md
└── .gitignore
```

## Files

- `src/background.js`: This file contains the background script for the Firefox extension. It handles events and communicates with the content script.

- `src/content.js`: This file contains the content script for the Firefox extension. It is injected into web pages and applies the border radius to all images.

- `src/manifest.json`: This file is the manifest file for the Firefox extension. It defines the extension's metadata, permissions, and scripts.

- `.gitignore`: This file specifies which files and directories should be ignored by Git version control.

## Usage

To use this Firefox extension, follow these steps:

1. Clone or download the repository.

2. Open Firefox and navigate to `about:debugging`.

3. Click on "This Firefox" in the sidebar.

4. Click on "Load Temporary Add-on".

5. Select the `manifest.json` file from the cloned/downloaded repository.

6. The extension is now loaded and will apply a border radius to all images on web pages.

## Contributing

Contributions are welcome! If you have any ideas, suggestions, or bug reports, please open an issue or submit a pull request.

## License

This project is licensed under the [MIT License](LICENSE).
```

Please note that the usage instructions assume that the extension is loaded as a temporary add-on in Firefox for testing purposes. If you want to publish the extension to the Firefox Add-ons store, additional steps and considerations will be required.