PAGE="""<!DOCTYPE html><html><head>
<style>
.button {
    display: block;
    width: 195px;
    height: 25px;
    background: #4E9CAF;
    padding: 10px;
    text-align: center;
    border-radius: 5px;
    color: white;
    font-weight: bold;
}
</style>
<title>Backyard Sentry</title></head>
<body><h1>Backyard Sentry Video Feed</h1>
<form>
<p><a href="stop_streaming" class="button">Stop Streaming</a></p>
</form>
<img src="stream.mjpg" width="1280" height="720" />
</body></html>"""

STOPPED_PAGE="""<!DOCTYPE html><html><head>
<style>
.button {
    display: block;
    width: 195px;
    height: 25px;
    background: #4E9CAF;
    padding: 10px;
    text-align: center;
    border-radius: 5px;
    color: white;
    font-weight: bold;
}
</style>
<title>Squirrel Sentry</title></head>
<body><h1>Squirrel Sentry</h1>
<p>Streaming stopped.</p>
<form>
<p><a href="start_streaming" class="button">Start Streaming</a></p>
</form>
</body></html>"""

