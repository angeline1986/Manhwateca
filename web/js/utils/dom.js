export function byId(id) {
  return document.getElementById(id);
}

export function setText(element, value) {
  if (element) element.textContent = value ?? "";
}

