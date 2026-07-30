import { $, arrayBufferToBase64Url, showError, setupClipboard } from './utils.js';

document.addEventListener('DOMContentLoaded', () => {
  const btn = $('#submitBtn');
  if (!btn) return;

  const errorSecure = btn.dataset.errorSecure || 'SnapPass requires a secure context (HTTPS) to generate encryption keys securely.';
  const errorGeneric = btn.dataset.errorGeneric || 'An error occurred while encrypting or saving the secret.';
  const textDefault = btn.dataset.textDefault || 'Generate URL';
  const textLoading = btn.dataset.textLoading || 'Generating...';

  if (!window.isSecureContext) {
    showError(errorSecure);
    btn.disabled = true;
    return;
  }

  const form = $('#password_create');
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      btn.disabled = true;
      btn.textContent = textLoading;

      const password = $('#password').value;
      const ttlStr = $('#ttl').value.toLowerCase();
      
      const timeConversion = {
        'two weeks': 1209600,
        'week': 604800,
        'day': 86400,
        'hour': 3600
      };
      const ttl = timeConversion[ttlStr] || 604800;

      try {
        // 1. Generate AES-128-GCM Key
        const key = await crypto.subtle.generateKey(
          { name: 'AES-GCM', length: 128 },
          true,
          ['encrypt']
        );

        // Export key to include in hash
        const exportedKey = await crypto.subtle.exportKey('raw', key);
        const keyBase64Url = arrayBufferToBase64Url(exportedKey);

        // 2. Encrypt the password
        const iv = crypto.getRandomValues(new Uint8Array(12));
        const encodedPassword = new TextEncoder().encode(password);
        
        const cipherText = await crypto.subtle.encrypt(
          { name: 'AES-GCM', iv: iv },
          key,
          encodedPassword
        );

        // 3. Combine IV and CipherText
        const combined = new Uint8Array(iv.length + cipherText.byteLength);
        combined.set(iv, 0);
        combined.set(new Uint8Array(cipherText), iv.length);

        // 4. Send encrypted payload to server
        const payloadBase64Url = arrayBufferToBase64Url(combined.buffer);
        
        const response = await fetch('/api/set_password/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          body: JSON.stringify({
            password: payloadBase64Url,
            ttl: ttl
          })
        });

        if (!response.ok) {
          let errMsg = 'Server returned an error';
          try {
            const errData = await response.json();
            if (errData.error) errMsg = errData.error;
            else if (errData.title) errMsg = errData.title;
          } catch(e) {}
          throw new Error(errMsg);
        }

        const data = await response.json();
        
        // 5. Construct full URL with Hash
        const fullLink = data.link + '#' + keyBase64Url;
        
        // 6. Display to user
        form.classList.add('hidden');
        $('#result-container').classList.remove('hidden');
        
        const linkInput = $('#password-link');
        linkInput.value = fullLink;
        
        // Setup clipboard
        setupClipboard('#copy-btn', () => linkInput.value);
        
        // Focus the link for accessibility
        linkInput.focus();

        // Auto-copy to clipboard for convenience
        const copyBtn = $('#copy-btn');
        if (copyBtn) {
          copyBtn.click();
        }

      } catch (err) {
        console.error(err);
        const msg = err.message === 'Server returned an error' ? errorGeneric : err.message;
        showError(msg);
        btn.disabled = false;
        btn.textContent = textDefault;
      }
    });
  }
});
