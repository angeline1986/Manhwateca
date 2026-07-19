import { getMangaUpdatesWorks, getReviewItems } from "../api/mangaupdatesApi.js";
import { getMetadataStatus, getSyncCandidates } from "../api/notionApi.js";

const EMPTY_WORKS = { kpis: {}, items: [], pagination: {} };

export async function loadReviewState() {
  try {
    const { payload } = await getReviewItems();
    return { summary: payload.summary || {}, items: payload.items || [] };
  } catch {
    return { summary: {}, items: [] };
  }
}

export async function loadWorksState(page) {
  return loadWorks({
    status: "WITHOUT_ID",
    page: String(page),
    pageSize: "5",
  });
}

/**
 * Carrega as obras para a tela de "Atualizar Metadados".
 * Agora utiliza o status METADATA_PENDING para trazer apenas obras 
 * que já possuem ID confirmado, mas ainda faltam dados oficiais (capa/URL).
 */
export async function loadMetadataState() {
  return loadWorks({
    status: "METADATA_PENDING", // Alterado de "CONFIRMED" para "METADATA_PENDING"
    page: "1",
    pageSize: "25",
  });
}

export async function loadNotionMetadataState() {
  const [metadata, candidates] = await Promise.all([
    loadNotionMetadataStatus(),
    loadNotionSyncCandidates(),
  ]);
  return { ...metadata, candidates };
}

async function loadNotionMetadataStatus() {
  try {
    const { payload } = await getMetadataStatus();
    return payload || {};
  } catch {
    return {};
  }
}

async function loadNotionSyncCandidates() {
  try {
    const { payload } = await getSyncCandidates();
    return payload || { items: [], summary: {} };
  } catch {
    return { items: [], summary: {} };
  }
}

async function loadWorks(params) {
  try {
    const { payload } = await getMangaUpdatesWorks(params);
    return payload.data || EMPTY_WORKS;
  } catch {
    return EMPTY_WORKS;
  }
}
