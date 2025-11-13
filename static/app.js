let tick = 0;
let videoStream = null;

async function start() {
    try {
        // Disable the start button to prevent multiple clicks
        event.target.disabled = true;

        // Request webcam access
        videoStream = await navigator.mediaDevices.getUserMedia({ 
            video: true, 
            audio: false 
        });
        
        // Create a video element to display the webcam feed
        let videoElement = document.createElement('video');
        videoElement.srcObject = videoStream;
        videoElement.autoplay = true;
        videoElement.style.width = '640px';
        videoElement.style.height = '480px';
        
        // Add the video to the page
        document.getElementById('thing').appendChild(videoElement);
        
        // Start sending ticks every half a second
        setInterval(async () => {
            tick++;
            const response = await fetch("/", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ tick })
            });

            const data = await response.json();
            console.log(data);

            display_response(data);
        }, 500);
        
    } catch (error) {
        console.error("Error accessing webcam:", error);
        alert("Could not access webcam. Please allow camera permissions.");
    }
}

function display_response(data) {
    let div = document.getElementById("display");
    div.textContent = data.message;
}