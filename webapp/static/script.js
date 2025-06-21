// Recupero i riferimenti HTML
const form = document.getElementById("itinerario-form");
const loading = document.getElementById("loading");
const risultato = document.getElementById("risultato");
const rispostaLlm = document.getElementById("risposta-llm");
const config_file = await fetch("/static/config.json");
const config_json = await response.json();
const apiUrl = config.API_URL;

//✅ Carica la classifica al caricamento iniziale della pagina
document.addEventListener("DOMContentLoaded", function () {
    getTopList();
});

form.addEventListener("submit", async function (e) {
    e.preventDefault();

    loading.style.display = "block";
    risultato.style.display = "none";
    rispostaLlm.textContent = "";

    const citta = document.getElementById("citta").value;
    const giorni = document.getElementById("giorni").value;
    const email = document.getElementById("email").value;

    await updateDatabase(citta);
    await getTopList();

    await requestItinerary(citta, giorni, email);
});

async function requestItinerary(citta, giorni, email) {
    try {
        //const response = await fetch("https://g1sscb2q89.execute-api.us-east-1.amazonaws.com/prod/richiesta-itinerario", {
        const response = await fetch(`${apiUrl}/richiesta-itinerario`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ citta, giorni, email })
        });

        if (!response.ok) throw new Error("Errore nel richiedere l'itinerario");

        const data = await response.json();
        const requestId = data.request_id;

        const intervalId = setInterval(async () => {
            try {
                //const resultResponse = await fetch(`https://g1sscb2q89.execute-api.us-east-1.amazonaws.com/prod/risultato-itinerario?requestId=${requestId}`);
                const resultResponse = await fetch(`${apiUrl}/risultato-itinerario?requestId=${requestId}`);
                if (!resultResponse.ok) throw new Error("Errore nel recupero risultato");

                const resultData = await resultResponse.json();

                if (resultData.status === "completed") {
                    clearInterval(intervalId);
                    rispostaLlm.textContent = resultData.risposta || "Nessuna risposta.";
                    risultato.style.display = "block";
                    loading.style.display = "none";
                } else if (resultData.status === "failed") {
                    clearInterval(intervalId);
                    rispostaLlm.textContent = "Errore nella generazione dell'itinerario.";
                    risultato.style.display = "block";
                    loading.style.display = "none";
                }
            } catch (err) {
                clearInterval(intervalId);
                rispostaLlm.textContent = "Errore durante il polling: " + err.message;
                risultato.style.display = "block";
                loading.style.display = "none";
            }
        }, 5000);

    } catch (err) {
        rispostaLlm.textContent = "Errore: " + err.message;
        risultato.style.display = "block";
        loading.style.display = "none";
    }
}

async function updateDatabase(citta) {
    try {
        //const res = await fetch("https://g1sscb2q89.execute-api.us-east-1.amazonaws.com/prod/classifica", {
        const res = await fetch(`${apiUrl}/classifica`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ citta })
        });

        if (!res.ok) {
            console.warn("Aggiornamento classifica fallito");
            return;
        }

        const result = await res.json();
        console.log("Classifica aggiornata:", result);

    } catch (error) {
        console.error("Errore nell’aggiornamento classifica:", error);
    }
}

async function getTopList() {
    try {
        //const res = await fetch("https://g1sscb2q89.execute-api.us-east-1.amazonaws.com/prod/classifica");
        const res = await fetch(`${apiUrl}/classifica`);
        if (!res.ok) {
            console.warn("Impossibile recuperare la classifica.");
            return;
        }

        const classifica = await res.json();

        const lista = document.getElementById("lista-classifica");
        lista.innerHTML = "";

        classifica.forEach((item, index) => {
            const li = document.createElement("li");
            li.className = "list-group-item d-flex justify-content-between align-items-center";
            li.innerHTML = `
                <span>${index + 1}. ${item.city}</span>
                <span class="badge bg-primary rounded-pill">${item.count}</span>
            `;
            lista.appendChild(li);
        });

    } catch (error) {
        console.error("Errore nel recupero della classifica:", error);
    }
}