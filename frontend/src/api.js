const BASE = import.meta.env.VITE_API_URL;

async function req(method, path, body = null, isForm = false) {
  const opts = { method, headers: {} };

  if (body && !isForm) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  } else if (body) {
    opts.body = body;
  }

  const res = await fetch(`${BASE}${path}`, opts);

  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || `HTTP ${res.status}`);
  }

  const ct = res.headers.get("content-type") || "";
  if (ct.includes("json")) return res.json();
  return res;
}

export const api = {
  status: () => req("GET", "/status"),
  dashboard: () => req("GET", "/dashboard"),

  listSuppliers: (params = "") => req("GET", `/fournisseurs${params}`),
  getSupplier: (id) => req("GET", `/fournisseurs/${id}`),
  createSupplier: (data) => req("POST", "/fournisseurs", data),
  importCSV: (file) => {
    const fd = new FormData();
    fd.append("file", file);
    return req("POST", "/fournisseurs/import-csv", fd, true);
  },
  reindexAll: () => req("POST", "/fournisseurs/reindex"),

  verifierConformite: (data) =>
    req("POST", "/demandes/verifier-conformite", data),
  createDemande: (data) => req("POST", "/demandes", data),
  uploadPDF: (file) => {
    const fd = new FormData();
    fd.append("file", file);
    return req("POST", "/demandes/pdf", fd, true);
  },
  extractPDF: (file) => {
    const fd = new FormData();
    fd.append("file", file);
    return req("POST", "/demandes/pdf-extract", fd, true);
  },
  confirmPDF: (data) => req("POST", "/demandes/pdf-confirm", data),
  listDemandes: (params = "") => req("GET", `/demandes${params}`),
  getDemande: (id) => req("GET", `/demandes/${id}`),
  updateStatut: (id, data) => req("PATCH", `/demandes/${id}/statut`, data),
  downloadPDF: (id) => req("GET", `/demandes/${id}/pdf`),
  exportCSV: () => req("GET", "/demandes/export/csv"),

  qa: (question, demand_id = null) =>
    req("POST", "/qa", { question, demand_id }),
};