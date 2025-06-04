//Recupero i riferimenti HTML
const form = document.getElementById("itinerario-form");
const loading = document.getElementById("loading");
const risultato = document.getElementById("risultato");
const rispostaLlm = document.getElementById("risposta-llm");

// ✅ Carica la classifica al caricamento iniziale della pagina
document.addEventListener("DOMContentLoaded", function () {
    getTopList();
});

//Quando l'utente clicca sul pulsante "Genera Itinerario" viene eseguita questa funzione
form.addEventListener("submit", async function (e) {
    e.preventDefault(); // evita il ricaricamento della pagina

    // Mostro spinner, nascondo risultato
    loading.style.display = "block";
    risultato.style.display = "none";
    rispostaLlm.textContent = "";

    // Estraggo i valori inseriti dall'utente nel form
    const citta = document.getElementById("citta").value;
    const giorni = document.getElementById("giorni").value;

    await update_database(citta); // lambda che aggiorna il DB delle città
    await getTopList(); // lambda che restituisce la top 5 delle città più cercate

    try {
        //Invia una richiesta POST alla route / (gestita da flask), i dati vengono inviati nel body della richiesta in formato JSON
        const response = await fetch("/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ citta, giorni })
        });

        // Se il server restituisce un errore HTTP (es. 404,500) => lancio un errore
        if (!response.ok) {
            throw new Error("Errore nella risposta del server");
        }

        // Attendo la risposta dal server e la conservo in data in formato JSON
        const data = await response.json();

        // Mostro la risposta
        rispostaLlm.textContent = data.risposta || "Nessuna risposta ricevuta.";
        risultato.style.display = "block";
    } catch (err) {
        // In caso di errore nella rete o nella risposta, mostro un messaggio di errore
        rispostaLlm.textContent = "Errore: " + err.message;
        risultato.style.display = "block";
    } finally {
        // Nascondo lo spinner di caricamento
        loading.style.display = "none";
    }
});

async function update_database(citta) {
    try {
        const res = await fetch("https://u8pzmwc3j0.execute-api.us-east-1.amazonaws.com/prod/classifica", {
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
        const res = await fetch("https://u8pzmwc3j0.execute-api.us-east-1.amazonaws.com/prod/classifica");

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