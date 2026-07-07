import { getMangaUpdatesWorks, getReviewItems } from "../api/mangaupdatesApi.js";

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

export async function loadMetadataState() {
  return loadWorks({
    status: "CONFIRMED",
    page: "1",
    pageSize: "25",
  });
}

async function loadWorks(params) {
  try {
    const { payload } = await getMangaUpdatesWorks(params);
    return payload.data || EMPTY_WORKS;
  } catch {
    return EMPTY_WORKS;
  }
}
