// 1. Generate or Retrieve Session ID
let username = localStorage.getItem("rag_username");
if (!username) {
    username = "User_" + Math.floor(Math.random() * 10000);
    localStorage.setItem("rag_username", username);
}
document.getElementById("username").innerText = username;

async function sendMessage() {
    const input = document.getElementById("userInput");
    const text = input.value;
    if (!text) return;

    // Add User Message
    addMessage(text, "user");
    input.value = "";

    // Send to Backend
    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: { 
                "Content-Type": "application/json",
                "X-User-ID": username 
            },
            body: JSON.stringify({ message: text })
        });
        const data = await response.json();
        addMessage(data.response, "bot");
    } catch (e) {
        addMessage("Error connecting to agent.", "bot");
    }
}

async function uploadFile() {
    const fileInput = document.getElementById("fileInput");
    const file = fileInput.files[0];
    if (!file) return alert("Please select a file");

    const formData = new FormData();
    formData.append("file", file);

    addMessage("Uploading and indexing...", "bot");

    try {
        const res = await fetch("/upload", {
            method: "POST",
            headers: { "X-User-ID": username },
            body: formData
        });
        const data = await res.json();
        addMessage(data.message, "bot");
    } catch (e) {
        addMessage("Upload failed.", "bot");
    }
}

async function showGraph() {
    try {
        const res = await fetch("/visualize", {
            headers: { "X-User-ID": username }
        });
        const data = await res.json();
        
        if (data.url) {
            document.getElementById("graph-frame").src = data.url;
            document.getElementById("graphModal").style.display = "block";
        } else {
            alert("No graph data found! Upload a file first.");
        }
    } catch (e) {
        console.error(e);
    }
}

function closeGraph() {
    document.getElementById("graphModal").style.display = "none";
}

function addMessage(text, sender) {
    const div = document.createElement("div");
    div.className = `message ${sender}`;
    div.innerText = text;
    document.getElementById("chatBox").appendChild(div);
}