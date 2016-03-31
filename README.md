## Getting started: Loading a few pages in a row on your phone
### Step 0. Prerequisites
<ul>
  <li> Install <a href="https://www.google.com/chrome/browser/canary.html">Chrome Canary</a>.  (You can try regular Chrome or Chrome Beta, but those browsers don't seem to work for me.)</li>
  <li> Get set up for Chrome remote debugging.</br>
  Instructions <a href="https://developers.google.com/web/tools/chrome-devtools/debug/remote-debugging/remote-debugging?hl=en">here</a></br>
  Troubleshooting <a href="http://stackoverflow.com/questions/21925992/chrome-devtools-devices-does-not-detect-device-when-plugged-in">here</a></li>
  <li>Ensure that <a href="http://developer.android.com/tools/help/adb.html">`adb.exe`</a> is in your PATH</li>
</ul>

### Step 1. Plug in your phone
Plug your phone into your computer via USB.
### Step 2. Open a Chrome tab on your phone
Self explanatory.
### Step 3. Open Chrome Canary on your computer
Open Chrome Canary and navigate to `chrome://inspect/`</br>
Confirm that you see your phone's Chrome tab listed here.
### Step 4. Run the script
Run: `python chrome-automation-WebSocket.py 5 ./url_list.txt ./`</br>
You may be prompted for a little additional info while the script is running.</br>
The script will look in the file `url_list.txt` for a list of URLs to load.</br>
It will load each URL in the list and collect data for `5` seconds before loading the next URL in the list.</br>
Data from each page load will be saved in a separate file in the output directory: `./`</br>
For more info, you can run: `python chrome-automation-WebSocket.py -h`
