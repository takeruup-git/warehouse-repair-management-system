// CSRF保護のためのAjaxセットアップ
document.addEventListener('DOMContentLoaded', function() {
    // CSRFトークンを取得
    function getCsrfToken() {
        return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    }
    
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