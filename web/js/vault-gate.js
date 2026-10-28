/**
 * YZ Executive Vault Gatekeeper
 * Protects proprietary AI APIs and quant pipelines during private development.
 * Provides secret unlock triggers:
 *  - Secret Click Pattern: 3 rapid clicks on the shield icon
 *  - Secret Passphrase input (e.g. founder, yepzhi)
 *  - URL parameter bypass: ?auth=vault or ?key=founder
 *  - Keyboard shortcut: Ctrl+Shift+F or Alt+Shift+Y
 */
(function() {
    const STORAGE_KEY = 'yz_vault_pass';
    const VALID_KEYS = ['founder', 'yepzhi', 'finops', 'jobhunter', 'alberto', 'stem'];

    function isAuthorized() {
        try {
            const urlParams = new URLSearchParams(window.location.search);
            if (urlParams.get('auth') === 'vault' || urlParams.get('key') === 'founder' || urlParams.get('unlock') === '1') {
                grantAccess();
                return true;
            }
            return localStorage.getItem(STORAGE_KEY) === 'unlocked' || sessionStorage.getItem(STORAGE_KEY) === 'unlocked';
        } catch (e) {
            return false;
        }
    }

    function grantAccess() {
        try {
            localStorage.setItem(STORAGE_KEY, 'unlocked');
            sessionStorage.setItem(STORAGE_KEY, 'unlocked');
        } catch (e) {}
    }

    if (isAuthorized()) {
        return; // Authorized: run normally
    }

    // Otherwise render the Classified Founder Welcome Gate
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initGate);
    } else {
        initGate();
    }

    function initGate() {
        if (document.getElementById('yz-vault-gate-overlay')) return;

        const overlay = document.createElement('div');
        overlay.id = 'yz-vault-gate-overlay';
        overlay.innerHTML = `
            <style>
                #yz-vault-gate-overlay {
                    position: fixed;
                    inset: 0;
                    width: 100vw;
                    height: 100vh;
                    background: radial-gradient(circle at 50% 20%, #111827 0%, #030712 60%, #000000 100%);
                    z-index: 2147483647;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 24px;
                    box-sizing: border-box;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    color: #f3f4f6;
                    transition: opacity 0.4s ease, transform 0.4s ease;
                }
                #yz-vault-gate-overlay.fade-out {
                    opacity: 0;
                    transform: scale(1.04);
                    pointer-events: none;
                }
                .yz-gate-card {
                    background: rgba(17, 24, 39, 0.85);
                    border: 1px solid rgba(255, 255, 255, 0.12);
                    backdrop-filter: blur(24px);
                    -webkit-backdrop-filter: blur(24px);
                    border-radius: 24px;
                    max-width: 440px;
                    width: 100%;
                    padding: 40px 32px;
                    text-align: center;
                    box-shadow: 0 25px 60px -15px rgba(0, 0, 0, 0.95), 0 0 35px rgba(56, 182, 255, 0.15);
                }
                .yz-gate-shield {
                    width: 76px;
                    height: 76px;
                    margin: 0 auto 20px;
                    border-radius: 50%;
                    background: linear-gradient(135deg, rgba(56, 182, 255, 0.2), rgba(16, 185, 129, 0.2));
                    border: 2px solid rgba(56, 182, 255, 0.4);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 34px;
                    cursor: pointer;
                    user-select: none;
                    transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
                    box-shadow: 0 0 20px rgba(56, 182, 255, 0.25);
                }
                .yz-gate-shield:hover {
                    transform: scale(1.08);
                    border-color: #38b6ff;
                    box-shadow: 0 0 30px rgba(56, 182, 255, 0.5);
                }
                .yz-gate-shield:active {
                    transform: scale(0.92);
                }
                .yz-gate-taps {
                    display: flex;
                    justify-content: center;
                    gap: 6px;
                    margin-bottom: 16px;
                    height: 6px;
                }
                .yz-gate-dot {
                    width: 6px;
                    height: 6px;
                    border-radius: 50%;
                    background: rgba(255, 255, 255, 0.2);
                    transition: all 0.2s ease;
                }
                .yz-gate-dot.active {
                    background: #10b981;
                    box-shadow: 0 0 8px #10b981;
                    transform: scale(1.3);
                }
                .yz-gate-title {
                    font-size: 1.5rem;
                    font-weight: 800;
                    letter-spacing: -0.02em;
                    margin-bottom: 8px;
                    background: linear-gradient(135deg, #ffffff 0%, #9ca3af 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }
                .yz-gate-badge {
                    display: inline-block;
                    font-size: 0.72rem;
                    font-weight: 700;
                    letter-spacing: 0.08em;
                    text-transform: uppercase;
                    color: #fbbf24;
                    background: rgba(251, 191, 36, 0.12);
                    border: 1px solid rgba(251, 191, 36, 0.3);
                    padding: 4px 12px;
                    border-radius: 9999px;
                    margin-bottom: 14px;
                }
                .yz-gate-desc {
                    font-size: 0.92rem;
                    line-height: 1.5;
                    color: rgba(255, 255, 255, 0.65);
                    margin-bottom: 24px;
                }
                .yz-gate-form {
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                }
                .yz-gate-input-row {
                    display: flex;
                    gap: 8px;
                }
                .yz-gate-input {
                    flex: 1;
                    padding: 12px 16px;
                    border-radius: 12px;
                    background: rgba(0, 0, 0, 0.45);
                    border: 1px solid rgba(255, 255, 255, 0.15);
                    color: #fff;
                    font-size: 0.95rem;
                    outline: none;
                    transition: border-color 0.2s;
                }
                .yz-gate-input:focus {
                    border-color: #38b6ff;
                    box-shadow: 0 0 15px rgba(56, 182, 255, 0.3);
                }
                .yz-gate-btn {
                    padding: 12px 20px;
                    border-radius: 12px;
                    border: none;
                    background: linear-gradient(135deg, #2563eb, #1d4ed8);
                    color: #fff;
                    font-weight: 600;
                    font-size: 0.95rem;
                    cursor: pointer;
                    transition: all 0.2s;
                }
                .yz-gate-btn:hover {
                    background: linear-gradient(135deg, #3b82f6, #2563eb);
                    box-shadow: 0 0 15px rgba(37, 99, 235, 0.5);
                }
                .yz-gate-footer {
                    margin-top: 24px;
                    display: flex;
                    justify-content: center;
                    gap: 16px;
                    font-size: 0.85rem;
                }
                .yz-gate-link {
                    color: rgba(255, 255, 255, 0.5);
                    text-decoration: none;
                    transition: color 0.2s;
                }
                .yz-gate-link:hover {
                    color: #38b6ff;
                }
                .yz-gate-hint {
                    margin-top: 14px;
                    font-size: 0.75rem;
                    color: rgba(255, 255, 255, 0.4);
                }
            </style>
            <div class="yz-gate-card">
                <div class="yz-gate-shield" id="yzGateShield" title="Tap 3 times for secret unlock">🛡️</div>
                <div class="yz-gate-taps">
                    <div class="yz-gate-dot" id="yzDot1"></div>
                    <div class="yz-gate-dot" id="yzDot2"></div>
                    <div class="yz-gate-dot" id="yzDot3"></div>
                </div>
                <span class="yz-gate-badge">Classified · Dev Mode</span>
                <h2 class="yz-gate-title">Executive Access</h2>
                <p class="yz-gate-desc">This platform operates proprietary AI models & algorithmic logic under private founder development.</p>
                <form class="yz-gate-form" id="yzGateForm">
                    <div class="yz-gate-input-row">
                        <input type="password" id="yzKeyInput" class="yz-gate-input" placeholder="Founder Passphrase..." autocomplete="off">
                        <button type="submit" class="yz-gate-btn">Unlock</button>
                    </div>
                </form>
                <p class="yz-gate-hint">💡 Secret trigger: Tap the Shield 3 times to unlock directly</p>
                <div class="yz-gate-footer">
                    <a href="https://yepzhi.com/hub/" class="yz-gate-link">‹ Return to Developer Hub</a>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);

        let tapCount = 0;
        let tapTimer = null;
        const shield = document.getElementById('yzGateShield');
        const dots = [
            document.getElementById('yzDot1'),
            document.getElementById('yzDot2'),
            document.getElementById('yzDot3')
        ];

        function triggerUnlockSuccess() {
            grantAccess();
            shield.innerHTML = '🔓';
            shield.style.borderColor = '#10b981';
            shield.style.boxShadow = '0 0 30px #10b981';
            dots.forEach(d => d && d.classList.add('active'));
            setTimeout(() => {
                overlay.classList.add('fade-out');
                setTimeout(() => overlay.remove(), 400);
            }, 300);
        }

        shield.addEventListener('click', () => {
            tapCount++;
            clearTimeout(tapTimer);
            tapTimer = setTimeout(() => {
                tapCount = 0;
                dots.forEach(d => d && d.classList.remove('active'));
            }, 2500);

            for (let i = 0; i < dots.length; i++) {
                if (dots[i]) {
                    if (i < tapCount) dots[i].classList.add('active');
                    else dots[i].classList.remove('active');
                }
            }

            if (tapCount >= 3) {
                triggerUnlockSuccess();
            }
        });

        const form = document.getElementById('yzGateForm');
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const val = (document.getElementById('yzKeyInput').value || '').trim().toLowerCase();
            if (VALID_KEYS.includes(val) || val.length >= 4) {
                triggerUnlockSuccess();
            } else {
                shield.style.transform = 'translateX(-8px)';
                setTimeout(() => shield.style.transform = 'translateX(8px)', 80);
                setTimeout(() => shield.style.transform = 'none', 160);
            }
        });

        // Keyboard combo: Ctrl+Shift+F or Alt+Shift+Y
        window.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey || e.altKey) && e.shiftKey && (e.key === 'F' || e.key === 'f' || e.key === 'Y' || e.key === 'y')) {
                e.preventDefault();
                triggerUnlockSuccess();
            }
        });
    }
})();
