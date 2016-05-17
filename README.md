## Flying Chrome by wire, loading pages, recording data
This readme will walk you through how to use the provided code to do the following:
<ul>
	<li> Set up Chrome for "fly by wire" operation on 1) your computer and 2) an Android device.</li>

</ul>
### Step 0. Prerequisites
<ol>
  <li>Install <a href="https://www.google.com/chrome/browser/desktop/">Google Chrome</a> on your computer.</li>
</ol>

### Step 0a. Prerequisites for running experiment on computer
<ol>
	<li>Create a directory that will serve as a separate User Profile for Chrome. e.g. </br>
  		<code>mkdir ~/chrome-profile</code></br>
  		Make a note of the name and location of this directory.</li>
  	<li>Launch Chrome from command line with arguments:</br>
  		<code>/path/to/chrome --args --remote-debugging-port=9222 --user-data-dir=/path/to/chrome-profile (use chrome-profile from step 1)</code></li>
	<li>Download and install Adblock Plus.  There are two ways to do this.</br>
		-The hard way: Clone repo and build from source (https://hg.adblockplus.org/adblockpluschrome/).
		The advantage of the hard way is that it ensures a proper apples-to-apples comparison with Adblock Minus, which you will have to build from source.</br>
		-The easy way: Install from Chrome Webstore (https://chrome.google.com/webstore/detail/adblock-plus/cfhdojbkjhnklbpkdaibdccddilifddb).  The advantage of the easy way is that it is easy.</li>
	<li>Clone and build Adblock Minus.  https://github.com/weineran/adblockminuschrome<li>
	<li>Go to chrome://extensions in your browser.</li>
	<li>Ensure that Adblock Plus is the first extension listed at the top of the list.</li>
	<li>Ensure that Adblock Minus ("Adblock QMinus") is the next extensions listed, directly beneath Adblock Plus.</li>
	<li>Ensure that the box for Developer Mode at the top of the page is unchecked</li>
</ol>

### Step 0b. Prerequisites for running experiment on phone
<ul>
	<li> Get set up for Chrome remote debugging on Android device.</br>
	  -Instructions <a href="https://developers.google.com/web/tools/chrome-devtools/debug/remote-debugging/remote-debugging?hl=en">here</a></br>
	  -Troubleshooting <a href="http://stackoverflow.com/questions/21925992/chrome-devtools-devices-does-not-detect-device-when-plugged-in">here</a></li>
	<li>Ensure that <a href="http://developer.android.com/tools/help/adb.html">`adb.exe`</a> is in your computer's PATH</li>
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

## Getting started: Loading a few pages in a row on your computer
### Step 0. Prerequisites
Same Step 0 from the phone instructions above, except that you don't need `adb`.
### Step 1. Open Chrome Canary on your computer
Run: `/path/to/chrome-canary/chrome.exe --remote-debugging-port=9222`
### Step 2. Run the script
Same as Step 4 above.
