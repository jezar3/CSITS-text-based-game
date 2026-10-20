To download the ready-to-play executable, open the **Releases** section on the right side of the GitHub page and download the `.exe`.

Run `dist\EmberfallChronicles.exe` to launch the game in its own window. Background music starts automatically; use the Music button to turn it off or back on. The packaged executable includes the music track.

Use the arrow keys or number keys to choose a hero. The window adjusts the game text to fit the current window size. Press F11 for fullscreen (Esc restores the window). The start screen recommends headphones for the best experience. In combat, press A to attack, S for your special, P for a potion, or F to flee. For other prompts, type your response in the input box and press Enter. Selecting or copying text does not pause the animations.

To rebuild the executable from this folder, include the music file with PyInstaller:

```powershell
pyinstaller --noconfirm --clean --onefile --windowed --name EmberfallChronicles --add-data "Rókatánc.mp3;." window_game.py
```
