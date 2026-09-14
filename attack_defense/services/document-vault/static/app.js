"use strict";

// La scheda conserva il token; il server ne controlla la validita' a ogni richiesta.
let token = sessionStorage.getItem("vault-token");
const access = document.getElementById("access");
const vault = document.getElementById("vault");
const message = document.getElementById("message");

function report(text, error = false) {
  message.textContent = text;
  message.classList.toggle("error", error);
}

function clearSession() {
  token = null;
  sessionStorage.removeItem("vault-token");
  access.hidden = false;
  vault.hidden = true;
}

async function api(path, method = "GET", body = undefined) {
  // Tutte le operazioni usano la stessa API e la stessa sessione Bearer.
  const headers = {};

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  // Per l'upload il browser imposta Content-Type e separatori del multipart.
  if (body !== undefined && !(body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(body);
  }

  const response = await fetch(`/api/v1${path}`, {method, headers, body});

  if (!response.ok) {
    if (response.status === 401) {
      clearSession();
    }

    const data = await response.json().catch(() => ({}));
    throw new Error(data.error || `Errore HTTP ${response.status}`);
  }

  return response;
}

async function download(item) {
  // Fetch aggiunge il Bearer; il link temporaneo salva i byte ricevuti.
  const response = await api(
    `/documents/download?file=${encodeURIComponent(item.id)}`
  );

  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement("a");

  link.href = url;
  link.download = item.name;

  document.body.append(link);
  link.click();
  link.remove();

  // Lascia al browser il tempo di avviare il download prima del rilascio.
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

async function refreshDocuments() {
  const response = await api("/documents");
  const data = await response.json();
  const tableBody = document.getElementById("documents");

  tableBody.replaceChildren();
  document.getElementById("empty").hidden = data.documents.length > 0;

  for (const item of data.documents) {
    const row = document.createElement("tr");

    // I metadati vengono inseriti come testo, senza interpretare HTML.
    for (const value of [item.name, item.id, item.size]) {
      const cell = document.createElement("td");
      cell.textContent = value;
      row.append(cell);
    }

    const actionsCell = document.createElement("td");
    const button = document.createElement("button");

    button.textContent = "Scarica";
    button.addEventListener("click", () =>
      download(item).catch(error => report(error.message, true))
    );

    actionsCell.append(button);
    row.append(actionsCell);
    tableBody.append(row);
  }
}

async function showVault(user) {
  document.getElementById("identity").textContent =
    `${user.username} · utente ${user.id}`;

  access.hidden = true;
  vault.hidden = false;

  await refreshDocuments();
}

document.getElementById("auth-form").addEventListener("submit", async event => {
  event.preventDefault();
  const form = event.currentTarget;
  const values = Object.fromEntries(new FormData(form));

  try {
    // Dopo la registrazione eseguiamo il normale login previsto dall'API.
    if (event.submitter?.value === "register") {
      await api("/register", "POST", values);
    }

    const response = await api("/login", "POST", values);
    const data = await response.json();

    token = data.token;
    sessionStorage.setItem("vault-token", token);

    form.reset();
    await showVault(data.user);
    report("Accesso effettuato.");
  } catch (error) {
    report(error.message, true);
  }
});

document.getElementById("upload-form").addEventListener("submit", async event => {
  event.preventDefault();
  const form = event.currentTarget;

  try {
    await api("/documents", "POST", new FormData(form));

    form.reset();
    await refreshDocuments();
    report("Documento caricato.");
  } catch (error) {
    report(error.message, true);
  }
});

document.getElementById("logout").addEventListener("click", async () => {
  try {
    await api("/logout", "POST");
    clearSession();
    report("Sessione terminata.");
  } catch (error) {
    report(error.message, true);
  }
});

if (token) {
  // Al ricaricamento della pagina verifichiamo la sessione prima di mostrare i dati.
  api("/me")
    .then(response => response.json())
    .then(showVault)
    .catch(error => report(error.message, true));
}
