const API_BASE = "/api"; // Prefijo de la API backend del mismo dominio.

const loginForm = document.getElementById("loginForm");
const usernameInput = document.getElementById("username");
const passwordInput = document.getElementById("password");
const loginError = document.getElementById("loginError");
const loginSection = document.getElementById("loginSection");
const dashboardSection = document.getElementById("dashboardSection");
const userRole = document.getElementById("userRole");
const centrosCount = document.getElementById("centrosCount");
const evaluacionesCount = document.getElementById("evaluacionesCount");
const logoutButton = document.getElementById("logoutButton");
const centroForm = document.getElementById("centroForm");
const evaluacionForm = document.getElementById("evaluacionForm");
const centroSelect = document.getElementById("centroSelect");
const centroMessage = document.getElementById("centroMessage");
const evaluacionMessage = document.getElementById("evaluacionMessage");
const evaluacionesList = document.getElementById("evaluacionesList");

let currentRole = "invitado"; // Rol actual del usuario en la PWA.

function setView(isAuthenticated) {
    loginSection.classList.toggle("active", !isAuthenticated);
    dashboardSection.classList.toggle("active", isAuthenticated);
    userRole.textContent = isAuthenticated ? currentRole.toUpperCase() : "Invitado";
}

async function fetchJson(url, options = {}) {
    const response = await fetch(url, options);
    if (!response.ok) {
        const error = await response.json().catch(() => ({ message: response.statusText }));
        throw new Error(error.message || "Error de red");
    }
    return response.headers.get("content-type")?.includes("application/json") ? response.json() : response;
}

async function loadDashboard() {
    const centros = await fetchJson(`${API_BASE}/centros`);
    const evaluaciones = await fetchJson(`${API_BASE}/evaluaciones`);

    centrosCount.textContent = centros.length;
    evaluacionesCount.textContent = evaluaciones.length;
    centroSelect.innerHTML = "<option value=''>Selecciona un centro</option>";

    centros.forEach((centro) => {
        centroSelect.innerHTML += `<option value="${centro.id}">${centro.razon_social}</option>`;
    });

    evaluacionesList.innerHTML = evaluaciones.map((evaluacion) => {
        return `
            <div class="list-item">
                <strong>${evaluacion.razon_social}</strong><br>
                <small>Guía: ${evaluacion.tipo_guia} • Nivel: ${evaluacion.nivel_riesgo} • Fecha: ${evaluacion.fecha}</small>
                <p>${JSON.stringify(evaluacion.datos_json)}</p>
            </div>
        `;
    }).join("");
}

loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    loginError.textContent = "";

    try {
        const data = {
            username: usernameInput.value.trim(),
            password: passwordInput.value,
        };
        const result = await fetchJson(`${API_BASE}/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });

        if (result.success) {
            currentRole = result.role;
            setView(true);
            await loadDashboard();
        } else {
            loginError.textContent = result.message;
        }
    } catch (error) {
        loginError.textContent = error.message;
    }
});

logoutButton.addEventListener("click", () => {
    currentRole = "invitado";
    setView(false);
});

centroForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    centroMessage.textContent = "";

    const body = {
        razon_social: document.getElementById("razonSocial").value.trim(),
        domicilio: document.getElementById("domicilio").value.trim(),
        actividad_principal: document.getElementById("actividadPrincipal").value.trim(),
        total_trabajadores: Number(document.getElementById("totalTrabajadores").value),
    };

    try {
        const result = await fetchJson(`${API_BASE}/centros`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });
        centroMessage.textContent = result.message;
        centroForm.reset();
        await loadDashboard();
    } catch (error) {
        centroMessage.textContent = error.message;
        centroMessage.classList.remove("success");
        centroMessage.classList.add("error");
    }
});

evaluacionForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    evaluacionMessage.textContent = "";

    const body = {
        centro_id: Number(centroSelect.value),
        tipo_guia: document.getElementById("tipoGuia").value,
        datos: {
            comentarios: document.getElementById("comentarios").value.trim(),
        },
    };

    try {
        const result = await fetchJson(`${API_BASE}/evaluacion`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });
        evaluacionMessage.textContent = result.message;
        evaluacionForm.reset();
        await loadDashboard();
    } catch (error) {
        evaluacionMessage.textContent = error.message;
        evaluacionMessage.classList.remove("success");
        evaluacionMessage.classList.add("error");
    }
});

setView(false); // Muestra el login hasta que el usuario se autentique.
