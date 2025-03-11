/**
 * 倉庫修繕費管理システム共通JavaScript
 */

// ドキュメント読み込み完了時の処理
document.addEventListener('DOMContentLoaded', function() {
    // フラッシュメッセージの自動非表示
    const flashMessages = document.querySelectorAll('.alert-dismissible');
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            const closeButton = message.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            }
        }, 5000);
    });
    
    // テーブルの検索機能
    const tableSearchInputs = document.querySelectorAll('.table-search-input');
    tableSearchInputs.forEach(function(input) {
        input.addEventListener('keyup', function() {
            const searchText = this.value.toLowerCase();
            const tableId = this.dataset.tableTarget;
            const table = document.getElementById(tableId);
            
            if (table) {
                const rows = table.querySelectorAll('tbody tr');
                
                rows.forEach(function(row) {
                    const text = row.textContent.toLowerCase();
                    if (text.indexOf(searchText) > -1) {
                        row.style.display = '';
                    } else {
                        row.style.display = 'none';
                    }
                });
            }
        });
    });
    
    // 数値入力フィールドのフォーマット
    const numberInputs = document.querySelectorAll('input[type="number"]');
    numberInputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            if (this.value && !isNaN(this.value)) {
                // 小数点以下がある場合は最大2桁まで表示
                const value = parseFloat(this.value);
                if (value % 1 !== 0) {
                    this.value = value.toFixed(2);
                }
            }
        });
    });
    
    // 日付入力フィールドの初期値設定
    const dateInputs = document.querySelectorAll('input[type="date"]:not([value])');
    const today = new Date().toISOString().split('T')[0];
    
    dateInputs.forEach(function(input) {
        // value属性が設定されていない場合のみ今日の日付を設定
        if (!input.getAttribute('value')) {
            input.value = today;
        }
    });
    
    // ファイルアップロードのプレビュー
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(function(input) {
        input.addEventListener('change', function() {
            const previewId = this.dataset.preview;
            if (previewId) {
                const preview = document.getElementById(previewId);
                if (preview) {
                    if (this.files && this.files[0]) {
                        const reader = new FileReader();
                        
                        reader.onload = function(e) {
                            preview.src = e.target.result;
                            preview.style.display = 'block';
                        };
                        
                        reader.readAsDataURL(this.files[0]);
                    } else {
                        preview.src = '';
                        preview.style.display = 'none';
                    }
                }
            }
        });
    });
    
    // 操作者名の自動設定
    const operatorNameInput = document.getElementById('global-operator-name');
    if (operatorNameInput) {
        // ローカルストレージから操作者名を取得
        const savedOperator = localStorage.getItem('operatorName');
        if (savedOperator) {
            operatorNameInput.value = savedOperator;
        }
        
        // 操作者名が変更されたらローカルストレージに保存
        operatorNameInput.addEventListener('change', function() {
            localStorage.setItem('operatorName', this.value);
        });
        
        // フォームに操作者名を自動設定
        const forms = document.querySelectorAll('form');
        forms.forEach(function(form) {
            form.addEventListener('submit', function() {
                const operatorField = this.querySelector('[name="operator_name"]');
                if (operatorField && !operatorField.value) {
                    operatorField.value = operatorNameInput.value;
                }
            });
        });
    }
});