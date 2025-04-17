import os
import openpyxl
from datetime import datetime
from app.utils.excel_template import create_inspection_template

def generate_inspection_format(forklifts):
    """
    フォークリフト一覧から定期自主検査記録表のExcelファイルを生成する
    
    Args:
        forklifts: フォークリフトのリスト
        
    Returns:
        生成されたExcelファイルのパス
    """
    # テンプレートファイルのパスを取得
    template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'templates')
    template_path = os.path.join(template_dir, 'forklift_inspection_template.xlsx')
    
    # テンプレートが存在しない場合は作成
    if not os.path.exists(template_path):
        template_path = create_inspection_template()
    
    # 出力ファイルのパスを設定
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'generated')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = os.path.join(output_dir, f'forklift_inspection_{timestamp}.xlsx')
    
    # テンプレートを読み込む
    template_wb = openpyxl.load_workbook(template_path)
    template_ws = template_wb.active
    
    # 稼働中のフォークリフトのみを対象とする
    active_forklifts = [f for f in forklifts if f.asset_status == 'active']
    
    # テンプレートシートを削除
    if 'テンプレート' in template_wb.sheetnames:
        template_wb.remove(template_wb['テンプレート'])
    
    # フォークリフトごとにシートを作成
    for i, forklift in enumerate(active_forklifts):
        # シート名は管理番号を使用
        sheet_name = forklift.management_number
        # シート名の長さ制限（31文字）
        if len(sheet_name) > 31:
            sheet_name = sheet_name[:28] + "..."
        
        # 既に同名のシートがある場合は連番を付ける
        if sheet_name in template_wb.sheetnames:
            j = 1
            while f"{sheet_name}_{j}" in template_wb.sheetnames and j < 100:
                j += 1
            sheet_name = f"{sheet_name}_{j}"
        
        # 新しいシートを作成
        if i == 0:
            ws = template_wb.create_sheet(sheet_name, 0)
        else:
            ws = template_wb.create_sheet(sheet_name)
        
        # テンプレートからスタイルをコピー
        for row in range(1, 17):
            for col in range(1, 11):
                src_cell = template_ws.cell(row=row, column=col)
                dst_cell = ws.cell(row=row, column=col)
                
                # セルの値とスタイルをコピー
                dst_cell.value = src_cell.value
                if src_cell.has_style:
                    dst_cell.font = src_cell.font
                    dst_cell.border = src_cell.border
                    dst_cell.fill = src_cell.fill
                    dst_cell.alignment = src_cell.alignment
        
        # マージセルをコピー
        for merged_cell_range in template_ws.merged_cells.ranges:
            ws.merge_cells(str(merged_cell_range))
        
        # フォークリフトデータを埋め込む
        ws.cell(row=3, column=1).value = forklift.management_number
        ws.cell(row=3, column=2).value = forklift.manufacturer
        ws.cell(row=3, column=3).value = forklift.model
        ws.cell(row=3, column=4).value = forklift.serial_number
        ws.cell(row=3, column=5).value = forklift.manufacture_date.strftime('%Y-%m-%d') if forklift.manufacture_date else ""
        ws.cell(row=3, column=6).value = f"{forklift.load_capacity}kg"
        ws.cell(row=3, column=7).value = f"{forklift.lift_height}mm"
        ws.cell(row=3, column=8).value = forklift.power_source_name
        ws.cell(row=3, column=9).value = f"{forklift.warehouse_group} {forklift.warehouse_number} {forklift.floor}"
        ws.cell(row=3, column=10).value = forklift.operator
        
        # 列幅の調整
        ws.column_dimensions['A'].width = 40
        for col in range(2, 11):
            ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 12
        
        # 行の高さ調整
        ws.row_dimensions[1].height = 30
        for row in range(2, 17):
            ws.row_dimensions[row].height = 20
    
    # ファイルを保存
    template_wb.save(output_path)
    
    # 相対パスを返す（静的ファイルとしてアクセスするため）
    relative_path = os.path.join('static', 'generated', os.path.basename(output_path))
    return relative_path