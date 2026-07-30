import { $, base64UrlToArrayBuffer, showError, setupClipboard } from './utils.js';

document.addEventListener('DOMContentLoaded', async () => {
  const container = $('#password-container');
  const errorSecure = container ? container.dataset.errorSecure : 'SnapPass requires a secure context (HTTPS) to decrypt secrets.';
  const errorMissing = container ? container.dataset.errorMissing : 'Missing encryption key in URL fragment. Cannot decrypt secret.';
  const errorFailed = container ? container.dataset.errorFailed : 'Failed to decrypt the secret. The link may be broken or the key is invalid.';

  if (!window.isSecureContext) {
    showError(errorSecure);
    $('#loading').classList.add('hidden');
    return;
  }

  const hash = window.location.hash.substring(1);
  if (!hash) {
    showError(errorMissing);
    $('#loading').classList.add('hidden');
    return;
  }

  try {
    // 1. Read encrypted payload from the DOM script tag
    const payloadEl = $('#encrypted-payload');
    if (!payloadEl) {
      throw new Error('Encrypted payload not found in document.');
    }
    
    // Trim quotes and whitespace that might be there from templating
    let payloadBase64Url = payloadEl.textContent.trim();
    if (payloadBase64Url.startsWith('"') && payloadBase64Url.endsWith('"')) {
      payloadBase64Url = payloadBase64Url.substring(1, payloadBase64Url.length - 1);
    }
    
    if (!payloadBase64Url) {
      throw new Error('Encrypted payload is empty.');
    }

    // 2. Decode the payload back to ArrayBuffer
    const combinedBuffer = base64UrlToArrayBuffer(payloadBase64Url);
    const combined = new Uint8Array(combinedBuffer);
    
    if (combined.length < 12) {
      throw new Error('Invalid encrypted payload length.');
    }

    const iv = combined.slice(0, 12);
    const cipherText = combined.slice(12);

    // 3. Decode the AES Key from the URL hash
    const keyBuffer = base64UrlToArrayBuffer(hash);
    const key = await crypto.subtle.importKey(
      'raw',
      keyBuffer,
      'AES-GCM',
      false,
      ['decrypt']
    );

    // 4. Decrypt
    const decryptedBuffer = await crypto.subtle.decrypt(
      { name: 'AES-GCM', iv: iv },
      key,
      cipherText
    );

    const decryptedText = new TextDecoder().decode(decryptedBuffer);

    // 5. Display
    $('#loading').classList.add('hidden');
    $('#password-container').classList.remove('hidden');
    
    const textEl = $('#password-text');
    textEl.value = decryptedText;
    
    setupClipboard('#copy-btn', () => textEl.value);
    
    // Accessibility: Focus on the decrypted text
    textEl.focus();

  } catch (err) {
    console.error(err);
    showError(errorFailed);
    $('#loading').classList.add('hidden');
  }
});
