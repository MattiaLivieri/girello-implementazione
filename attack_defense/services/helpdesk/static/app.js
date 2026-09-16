"use strict";

// Il token appartiene alla scheda; il server ne verifica la validita'.
let token = sessionStorage.getItem("helpdesk-token");
let currentTicket = null;
let activeQuery = null;
let busy = false;

const access = document.getElementById("access");
const desk = document.getElementById("desk");
const message = document.getElementById("message");
const authForm = document.getElementById("auth-form");
const ticketForm = document.getElementById("ticket-form");
const searchForm = document.getElementById("search-form");
const tickets = document.getElementById("tickets");
const detail = document.getElementById("ticket-detail");
const statusButton = document.getElementById("change-status");

function report(text, error = false) {
  message.textContent = text;
  message.classList.toggle("error", error);
}

function hideTicket() {
  currentTicket = null;
  detail.hidden = true;
  for (const id of ["ticket-title", "ticket-meta", "ticket-body"]) {
    document.getElementById(id).textContent = "";
  }
}

function clearSession() {
  token = null;
  activeQuery = null;
  sessionStorage.removeItem("helpdesk-token");
  access.hidden = false;
  desk.hidden = true;
  document.getElementById("identity").textContent = "";
  document.getElementById("results").textContent = "";
  tickets.replaceChildren();
  ticketForm.reset();
  searchForm.reset();
  hideTicket();
}

async function runAction(action) {
  // Una sola operazione alla volta evita doppi invii e risposte fuori ordine.
  if (busy) return;
  busy = true;
  document.getElementById("access-fields").disabled = true;
  document.getElementById("desk-fields").disabled = true;
  report("");

  try {
    await action();
  } catch (error) {
    report(error.message, true);
  } finally {
    busy = false;
    document.getElementById("access-fields").disabled = false;
    document.getElementById("desk-fields").disabled = false;
  }
}

async function api(path, method = "GET", body = undefined) {
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(body);
  }

  let response;
  try {
    response = await fetch(`/api/v1${path}`, {method, headers, body});
  } catch (_) {
    throw new Error("Servizio non raggiungibile. Riprova tra poco.");
  }

  if (!response.ok) {
    if (response.status === 401) clearSession();
    const data = await response.json().catch(() => ({}));
    throw new Error(data.error || `Errore HTTP ${response.status}`);
  }

  // Il logout restituisce 204, quindi non contiene JSON da leggere.
  return response.status === 204 ? null : response.json();
}

function statusLabel(status) {
  return status === "open" ? "Aperto" : "Chiuso";
}

function showTicket(ticket) {
  currentTicket = ticket;
  document.getElementById("ticket-title").textContent = ticket.title;
  document.getElementById("ticket-meta").textContent =
    `ID ${ticket.id} · ${statusLabel(ticket.status)} · ${ticket.created_at} UTC`;
  // Titolo e contenuto sono testo: non interpretiamo HTML ricevuto dal servizio.
  document.getElementById("ticket-body").textContent = ticket.body;
  statusButton.textContent = ticket.status === "open" ? "Chiudi ticket" : "Riapri ticket";
  detail.hidden = false;
  document.getElementById("ticket-title").focus();
}

async function loadTickets() {
  tickets.replaceChildren();
  const results = document.getElementById("results");
  results.textContent = "Caricamento...";
  const path = activeQuery === null
    ? "/tickets"
    : `/tickets/search?${new URLSearchParams({q: activeQuery})}`;

  let data;
  try {
    data = await api(path);
  } catch (error) {
    results.textContent = "Elenco non disponibile. Riprova con Cerca o Mostra tutti.";
    throw error;
  }

  results.textContent = data.tickets.length
    ? `Ticket mostrati: ${data.tickets.length}, dai piu' recenti (massimo 50).`
    : activeQuery === null ? "Non hai ancora ticket." : "Nessun risultato.";

  for (const item of data.tickets) {
    const row = document.createElement("tr");
    for (const value of [item.title, statusLabel(item.status), item.created_at, item.id]) {
      const cell = document.createElement("td");
      cell.textContent = value;
      row.append(cell);
    }

    const cell = document.createElement("td");
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = "Apri";
    button.addEventListener("click", () => runAction(async () => {
      hideTicket();
      showTicket(await api(`/tickets/${encodeURIComponent(item.id)}`));
    }));
    cell.append(button);
    row.append(cell);
    tickets.append(row);
  }
}

async function showDesk(user) {
  document.getElementById("identity").textContent =
    `${user.username} · utente ${user.id}`;
  access.hidden = true;
  desk.hidden = false;
  await loadTickets();
}

authForm.addEventListener("submit", event => {
  event.preventDefault();
  // Leggiamo i campi prima che runAction disabiliti il modulo.
  const values = Object.fromEntries(new FormData(authForm));
  const register = event.submitter?.value === "register";

  runAction(async () => {
    // Contiamo i caratteri Unicode, come fa il server.
    const length = Array.from(values.password).length;
    if (length < 8 || length > 128) {
      throw new Error("Password: da 8 a 128 caratteri.");
    }
    if (register) {
      await api("/register", "POST", values);
      authForm.elements.password.value = "";
      report("Account creato. Inserisci la password e premi Accedi.");
      return;
    }

    const data = await api("/login", "POST", values);
    token = data.token;
    sessionStorage.setItem("helpdesk-token", token);
    authForm.reset();
    await showDesk(data.user);
    report("Accesso effettuato.");
  });
});

ticketForm.addEventListener("submit", event => {
  event.preventDefault();
  const values = Object.fromEntries(new FormData(ticketForm));

  runAction(async () => {
    if (!values.title.trim() || Array.from(values.title).length > 120) {
      throw new Error("Titolo: da 1 a 120 caratteri, non solo spazi.");
    }
    const size = new TextEncoder().encode(values.body).length;
    if (size < 1 || size > 16 * 1024) {
      throw new Error("Il contenuto deve avere da 1 byte a 16 KiB.");
    }

    const ticket = await api("/tickets", "POST", values);
    ticketForm.reset();
    searchForm.reset();
    activeQuery = null;
    await loadTickets();
    showTicket(ticket);
    report("Ticket creato.");
  });
});

searchForm.addEventListener("submit", event => {
  event.preventDefault();
  const q = searchForm.elements.q.value;
  runAction(async () => {
    if (Array.from(q).length < 1 || Array.from(q).length > 256) {
      throw new Error("Ricerca: da 1 a 256 caratteri.");
    }
    // Conserviamo il testo esatto inserito, inclusi spazi e maiuscole.
    activeQuery = q;
    hideTicket();
    await loadTickets();
  });
});

document.getElementById("show-all").addEventListener("click", () => runAction(async () => {
  activeQuery = null;
  searchForm.reset();
  hideTicket();
  await loadTickets();
}));

statusButton.addEventListener("click", () => runAction(async () => {
  if (!currentTicket) return;
  const status = currentTicket.status === "open" ? "closed" : "open";
  const updated = await api(
    `/tickets/${encodeURIComponent(currentTicket.id)}`, "PATCH", {status}
  );
  // PATCH restituisce solo il riepilogo: conserviamo il contenuto gia' letto.
  showTicket({...currentTicket, ...updated});
  await loadTickets();
  report(status === "closed" ? "Ticket chiuso." : "Ticket riaperto.");
}));

document.getElementById("hide-detail").addEventListener("click", hideTicket);

document.getElementById("logout").addEventListener("click", () => runAction(async () => {
  await api("/logout", "POST");
  clearSession();
  report("Sessione terminata.");
}));

if (token) {
  // Al ricaricamento verifichiamo il token prima di mostrare i dati dell'utente.
  runAction(async () => showDesk(await api("/me")));
}
