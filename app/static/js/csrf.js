// CSRF保護のためのAjaxセットアップ
document.addEventListener('DOMContentLoaded', function() {
    // CSRFトークンを取得（メタタグまたはCookieから）
    function getCsrfToken() {
        // まずメタタグから取得を試みる
        const metaToken = document.querySelector('meta[name="csrf-token"]');
        if (metaToken) {
            return metaToken.getAttribute('content');
        }
        
        // メタタグがない場合はCookieから取得
        return getCsrfTokenFromCookie();
    }
    
    // CookieからCSRFトークンを取得
    function getCsrfTokenFromCookie() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrf_token') {
                return decodeURIComponent(value);
            }
        }
        return '';
    }
    
    // すべてのフォームにCSRFトークンを追加
    function addCsrfTokenToForms() {
        const token = getCsrfToken();
        if (!token) return;
        
        const forms = document.querySelectorAll('form[method="post"], form[method="POST"]');
        forms.forEach(form => {
            // すでにCSRFトークンがある場合はスキップ
            if (form.querySelector('input[name="csrf_token"]')) return;
            
            const csrfInput = document.createElement('input');
            csrfInput.type = 'hidden';
            csrfInput.name = 'csrf_token';
            csrfInput.value = token;
            form.appendChild(csrfInput);
        });
    }
    
    // ページ読み込み時にすべてのフォームにCSRFトークンを追加
    addCsrfTokenToForms();
    
    // 動的に追加されるフォームのために定期的にチェック
    setInterval(addCsrfTokenToForms, 1000);
    
    // Ajaxリクエスト前にCSRFトークンをヘッダーに追加
    let oldXHROpen = window.XMLHttpRequest.prototype.open;
    window.XMLHttpRequest.prototype.open = function(method, url) {
        let xhr = this;
        oldXHROpen.apply(xhr, arguments);
        
        if (method.toLowerCase() === 'post' || method.toLowerCase() === 'put' || method.toLowerCase() === 'delete') {
            xhr.setRequestHeader('X-CSRFToken', getCsrfToken());
        }
    };
    
    // フェッチAPIを使用する場合のCSRFトークン追加
    const originalFetch = window.fetch;
    window.fetch = function(url, options = {}) {
        if (options.method && (options.method.toLowerCase() === 'post' || 
                              options.method.toLowerCase() === 'put' || 
                              options.method.toLowerCase() === 'delete')) {
            if (!options.headers) {
                options.headers = {};
            }
            
            // ヘッダーがHeadersオブジェクトの場合
            if (options.headers instanceof Headers) {
                options.headers.append('X-CSRFToken', getCsrfToken());
            } else {
                // 通常のオブジェクトの場合
                options.headers['X-CSRFToken'] = getCsrfToken();
            }
        }
        
        return originalFetch.call(this, url, options);
    };
});