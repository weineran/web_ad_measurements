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
	<li>Download and install Adblock Plus.  There are two ways to do this.</br>
		-The hard way: Clone repo and build from source (https://hg.adblockplus.org/adblockpluschrome/).
		The advantage of the hard way is that it ensures a proper apples-to-apples comparison with Adblock Minus, which you will have to build from source.</br>
		-The easy way: Install from Chrome Webstore (https://chrome.google.com/webstore/detail/adblock-plus/cfhdojbkjhnklbpkdaibdccddilifddb).  The advantage of the easy way is that it is easy.</li>
	<li>Clone and build Adblock Minus.  https://github.com/weineran/adblockminuschrome</li>
</ol>

### Step 0b. Prerequisites for running experiment on phone
<ol>
	<li> Get set up for Chrome remote debugging on Android device.</br>
	  -Instructions <a href="https://developers.google.com/web/tools/chrome-devtools/debug/remote-debugging/remote-debugging?hl=en">here</a></br>
	  -Troubleshooting <a href="http://stackoverflow.com/questions/21925992/chrome-devtools-devices-does-not-detect-device-when-plugged-in">here</a></li>
	<li>Ensure that <a href="http://developer.android.com/tools/help/adb.html">`adb.exe`</a> is in your computer's PATH</li>
	<li>Download and install Block This! on your phone (https://block-this.com/).</li>
	<li>Run Block This! on your phone and tap the Start button.  When your phone asks if you want to allow the VPN, tap yes.</li>
	<li>Look up the dimensions for your phone screen in pixels and make a note.  For an explanation, see the section on Brittleness below.</li>
</ol>

## Running an experiment on your computer
<ol>
	<li>Launch Chrome from command line with arguments:</br>
  		<code>/path/to/chrome --args --remote-debugging-port=9222 --user-data-dir=/path/to/chrome-profile</code></br>    (use the chrome-profile directory you created in Step 0a)</br></br>
  		If you're not sure what <code>path/to/chrome</code> should be, you can try the following</br>
  		Mac: <code>open -a Google\ Chrome</code></br>(not exactly a path, but whatever)</br>
  		Windows: <code>"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"</code></li>
	<li>Go to <code>chrome://extensions</code> in your browser.</li>
	<li>Ensure that Adblock Plus is the first extension listed at the top of the list.  Ensure that the box is unchecked so that the extension is initially disabled.  NOTE: The list is alphabetical.  If there are other extensions listed above Adblock Plus, you will have to remove them by clicking the trash can icon.  For an explanation, see the section on Brittleness below.</li>
	<li>Ensure that Adblock Minus ("Adblock QMinus") is the next extensions listed, directly beneath Adblock Plus.  Ensure that the box is checked so that the extension is initially enabled.</li>
	<li>Ensure that the box for Developer Mode at the top of the page is unchecked</li>
	<li>Make a directory to hold the data collected from the page loads.  e.g.</br>
		<code>mkdir ~/page-load-data</code></li>
	<li>Try a quick test run of the experiment:</br>
		<code>python run-page-loads-ABM.py 5 2 url_lists/news-3.json /path/to/data/ 9222</code></br></br>
		For an explanation of the arguments, you can run:</br>
		<code>python run-page-loads-ABM.py -h</code></li>
	<li>What you should see:</br>
		<ul>
			<li>The measurement script will prompt you with several questions.  Your answers to these questions will determine things like whether the script is driving your phone or your computer and file-naming conventions for the output data files.  One thing to note: When you are asked "What would you like to measure?" you should select "1. Ads"</li>
			<li>Chrome will automatically enable/disable Adblock Plus and Adblock Minus.</li>
			<li>Chrome will load each website in <code>url_lists/news-3.json</code> twice with Adblock Plus and twice with Adblock Minus, alternating between the two.</li>
			<li>Each page load should last about 5 seconds.</li>
			<li>Between each page load, Chrome will automatically navigate to <code>chrome://net-internals/#dns</code> and flush the browser's internal DNS cache.</li>
			<li>At the end, your specified data directory should have a subdirectory called <code>raw/</code> and a subdirectory called <code>summaries/</code>.  Each should contain a file for each page load performed.</li>
		</ul></li>
	<li>If that worked, then you can try running the full experiment:
		<code>python run-page-loads-ABM.py 15 5 url_lists/all-15.json /path/to/data/ 9222</code></li>
</ol>

## Running an experiment on your phone
<ol>
	<li>Plug your phone into your computer via USB.</li>
	<li>If prompted, allow the USB Debugging connection.  (You may have to return to Developer Options and re-enable USB Debugging.)</li>
	<li>Open a Chrome tab on your phone.</li>
	<li>On your computer, navigate to `chrome://inspect/`</br>
		Confirm that you see your phone's Chrome tab is listed here.</li>
	<li>Try a quick test run of the experiment:</br>
		<code>python run-page-loads-ABM.py 5 2 url_lists/news-3.json /path/to/data/ 9222</code></br></br>
	</li>
	
</ol>
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

