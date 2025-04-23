/**
 * フォームヘルパー関数
 * フォーム送信やCSRFトークン処理のためのユーティリティ関数
 */

// 動的に作成されたフォームにCSRFトークンを追加
function addCsrfTokenToForm(form) {
    const token = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    const csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrf_token';
    csrfInput.value = token;
    form.appendChild(csrfInput);
    return form;
}

// フォームデータにCSRFトークンを追加
function addCsrfTokenToFormData(formData) {
    const token = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    formData.append('csrf_token', token);
    return formData;
}

// オブジェクトにCSRFトークンを追加
function addCsrfTokenToObject(obj) {
    const token = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    return { ...obj, csrf_token: token };
}

// 動的にフォームを作成して送信
function submitFormWithCsrf(action, method, data = {}) {
    const form = document.createElement('form');
    form.method = method;
    form.action = action;
    
    // CSRFトークンを追加
    const token = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    const csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrf_token';
    csrfInput.value = token;
    form.appendChild(csrfInput);
    
    // データをフォームに追加
    Object.keys(data).forEach(key => {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = key;
        input.value = data[key];
        form.appendChild(input);
    });
    
    // フォームをドキュメントに追加して送信
    document.body.appendChild(form);
    form.submit();
    document.body.removeChild(form);
}

// Ajaxリクエストを送信（CSRFトークン付き）
async function fetchWithCsrf(url, options = {}) {
    const token = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    // デフォルトオプションを設定
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': token
        },
        credentials: 'same-origin'
    };
    
    // オプションをマージ
    const mergedOptions = { ...defaultOptions, ...options };
    
    // ヘッダーをマージ
    if (options.headers) {
        mergedOptions.headers = { ...defaultOptions.headers, ...options.headers };
    }
    
    // リクエスト送信
    try {
        const response = await fetch(url, mergedOptions);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Fetch error:', error);
        throw error;
    }
}