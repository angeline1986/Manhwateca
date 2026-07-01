export function clampPage(page, totalPages) {
  return Math.min(Math.max(Number(page) || 1, 1), Math.max(Number(totalPages) || 1, 1));
}

