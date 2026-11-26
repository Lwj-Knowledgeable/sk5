<template>
	<div id="logs" style="font-family: monospace;"></div>
</template>

<script>
	const eventSource = new EventSource("/stream_log");
	eventSource.onmessage = (e) => {
	    document.getElementById("logs").innerHTML += e.data + "<br>";
		
	};
</script>

<style>
</style>