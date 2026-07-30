export const $ = (selector) => document.querySelector(selector);

export function arrayBufferToBase64Url(buffer) {
  let binary = '';
  const bytes = new Uint8Array(buffer);
  const len = bytes.byteLength;
  for (let i = 0; i < len; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  const base64 = window.btoa(binary);
  return base64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

export function base64UrlToArrayBuffer(base64url) {
  const base64 = base64url.replace(/-/g, '+').replace(/_/g, '/');
  // Pad with '=' if necessary
  const padded = base64.padEnd(base64.length + (4 - (base64.length % 4)) % 4, '=');
  const binary_string = window.atob(padded);
  const len = binary_string.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binary_string.charCodeAt(i);
  }
  return bytes.buffer;
}

export function showError(msg) {
  const container = $('#error-container');
  if (container) {
    container.textContent = msg;
    container.classList.remove('hidden');
  }
}

export function setupClipboard(buttonSelector, textFn) {
  const btn = $(buttonSelector);
  if (!btn) return;
  
  btn.addEventListener('click', async () => {
    try {
      const text = textFn();
      await navigator.clipboard.writeText(text);
      const originalText = btn.textContent;
      const copiedText = btn.dataset.textCopied || 'Copied!';
      btn.textContent = copiedText;
      setTimeout(() => {
        btn.textContent = originalText;
      }, 2000);
    } catch (err) {
      console.error('Failed to copy: ', err);
      const errorCopy = btn.dataset.errorCopy || 'Failed to copy to clipboard.';
      showError(errorCopy);
    }
  });
}
