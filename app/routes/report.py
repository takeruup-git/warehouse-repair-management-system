from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_file
from app.models import db
from app.models.forklift import Forklift, ForkliftRepair
from app.models.facility import Facility, FacilityRepair
from app.models.other_repair import OtherRepair
from app.models.master import Budget
from sqlalchemy import func, extract
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from config import Config

report_bp = Blueprint('report', __name__)

# 日本語フォントの登録
try:
    pdfmetrics.registerFont(TTFont('MSGothic', 'msgothic.ttc'))
except:
    # フォントが見つからない場合はデフォルトフォントを使用
    pass

@report_bp.route('/')
def index():
    return render_template('report/index.html')

@report_bp.route('/monthly_cost', methods=['GET', 'POST'])
def monthly_cost():
    if request.method == 'POST':
        try:
            # フィルター条件を取得
            year = int(request.form.get('year', Config.CURRENT_DATE.year))
            month = request.form.get('month')
            if month:
                month = int(month)
            
            asset_type = request.form.get('asset_type')
            target_id = request.form.get('target_id')
            if target_id:
                target_id = int(target_id)
            
            # エクスポート形式を取得
            export_format = request.form.get('export_format', 'excel')
            
            # クエリを構築
            if asset_type == 'forklift':
                query = db.session.query(
                    ForkliftRepair.repair_date,
                    ForkliftRepair.target_management_number,
                    ForkliftRepair.repair_item,
                    ForkliftRepair.repair_cost,
                    ForkliftRepair.repair_reason,
                    ForkliftRepair.hour_meter
                ).filter(
                    extract('year', ForkliftRepair.repair_date) == year
                )
                
                if month:
                    query = query.filter(extract('month', ForkliftRepair.repair_date) == month)
                
                if target_id:
                    query = query.filter(ForkliftRepair.forklift_id == target_id)
                
                repairs = query.order_by(ForkliftRepair.repair_date).all()
                
                # データフレームを作成
                data = []
                for repair in repairs:
                    data.append({
                        '修繕日': repair.repair_date.strftime('%Y-%m-%d'),
                        '管理番号': repair.target_management_number,
                        '修繕項目': repair.repair_item,
                        '修繕費用': repair.repair_cost,
                        '修繕理由': Config.REPAIR_REASON_NAMES.get(repair.repair_reason, repair.repair_reason),
                        'アワーメーター': repair.hour_meter
                    })
                
                # 合計を計算
                total_cost = sum(repair.repair_cost for repair in repairs)
                
                # 予算を取得
                budget = Budget.query.filter_by(year=year, asset_type='forklift').first()
                budget_amount = budget.amount if budget else 0
                
                # 予算消化率を計算
                if budget_amount > 0:
                    budget_usage_rate = (total_cost / budget_amount) * 100
                else:
                    budget_usage_rate = 0
                
                # タイトルを設定
                title = f'{year}年'
                if month:
                    title += f'{month}月'
                title += 'フォークリフト修繕費'
                
                if target_id:
                    forklift = Forklift.query.get(target_id)
                    if forklift:
                        title += f' - {forklift.management_number}'
                
            elif asset_type == 'facility':
                query = db.session.query(
                    FacilityRepair.repair_date,
                    FacilityRepair.target_warehouse_number,
                    FacilityRepair.floor,
                    FacilityRepair.repair_item,
                    FacilityRepair.repair_cost,
                    FacilityRepair.repair_reason
                ).filter(
                    extract('year', FacilityRepair.repair_date) == year
                )
                
                if month:
                    query = query.filter(extract('month', FacilityRepair.repair_date) == month)
                
                if target_id:
                    query = query.filter(FacilityRepair.facility_id == target_id)
                
                repairs = query.order_by(FacilityRepair.repair_date).all()
                
                # データフレームを作成
                data = []
                for repair in repairs:
                    data.append({
                        '修繕日': repair.repair_date.strftime('%Y-%m-%d'),
                        '倉庫番号': repair.target_warehouse_number,
                        '階層': repair.floor,
                        '修繕項目': repair.repair_item,
                        '修繕費用': repair.repair_cost,
                        '修繕理由': Config.REPAIR_REASON_NAMES.get(repair.repair_reason, repair.repair_reason)
                    })
                
                # 合計を計算
                total_cost = sum(repair.repair_cost for repair in repairs)
                
                # 予算を取得
                budget = Budget.query.filter_by(year=year, asset_type='facility').first()
                budget_amount = budget.amount if budget else 0
                
                # 予算消化率を計算
                if budget_amount > 0:
                    budget_usage_rate = (total_cost / budget_amount) * 100
                else:
                    budget_usage_rate = 0
                
                # タイトルを設定
                title = f'{year}年'
                if month:
                    title += f'{month}月'
                title += '倉庫施設修繕費'
                
                if target_id:
                    facility = Facility.query.get(target_id)
                    if facility:
                        title += f' - {facility.warehouse_number}'
                
            else:  # other
                query = db.session.query(
                    OtherRepair.repair_date,
                    OtherRepair.target_name,
                    OtherRepair.category,
                    OtherRepair.repair_cost,
                    OtherRepair.contractor
                ).filter(
                    extract('year', OtherRepair.repair_date) == year
                )
                
                if month:
                    query = query.filter(extract('month', OtherRepair.repair_date) == month)
                
                repairs = query.order_by(OtherRepair.repair_date).all()
                
                # データフレームを作成
                data = []
                for repair in repairs:
                    data.append({
                        '修繕日': repair.repair_date.strftime('%Y-%m-%d'),
                        '対象名': repair.target_name,
                        'カテゴリ': repair.category,
                        '修繕費用': repair.repair_cost,
                        '業者': repair.contractor
                    })
                
                # 合計を計算
                total_cost = sum(repair.repair_cost for repair in repairs)
                
                # 予算を取得
                budget = Budget.query.filter_by(year=year, asset_type='other').first()
                budget_amount = budget.amount if budget else 0
                
                # 予算消化率を計算
                if budget_amount > 0:
                    budget_usage_rate = (total_cost / budget_amount) * 100
                else:
                    budget_usage_rate = 0
                
                # タイトルを設定
                title = f'{year}年'
                if month:
                    title += f'{month}月'
                title += 'その他修繕費'
            
            # データフレームを作成
            df = pd.DataFrame(data)
            
            if export_format == 'excel':
                # Excelファイルを作成
                output = BytesIO()
                
                # Excelファイルに書き込み
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, sheet_name='修繕費', index=False)
                    
                    # シートを取得
                    worksheet = writer.sheets['修繕費']
                    workbook = writer.book
                    
                    # 列幅を調整
                    for i, col in enumerate(df.columns):
                        column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
                        worksheet.set_column(i, i, column_width)
                    
                    # 合計行を追加
                    row = len(df) + 2
                    worksheet.write(row, 0, '合計')
                    
                    # 修繕費用の列を特定
                    cost_col = None
                    for i, col in enumerate(df.columns):
                        if '修繕費用' in col:
                            cost_col = i
                            break
                    
                    if cost_col is not None:
                        worksheet.write(row, cost_col, total_cost)
                    
                    # 予算情報を追加
                    row += 2
                    worksheet.write(row, 0, '年間予算')
                    if cost_col is not None:
                        worksheet.write(row, cost_col, budget_amount)
                    
                    row += 1
                    worksheet.write(row, 0, '予算消化率')
                    if cost_col is not None:
                        worksheet.write(row, cost_col, f'{budget_usage_rate:.2f}%')
                    
                    # タイトルを追加
                    title_format = workbook.add_format({'bold': True, 'font_size': 14})
                    worksheet.write(0, 0, title, title_format)
                    
                    # データを1行下にずらす
                    for i in range(len(df) + 5, 0, -1):
                        for j in range(len(df.columns)):
                            cell_value = worksheet.table[i - 1][j].value
                            worksheet.write(i, j, cell_value)
                    
                    # ヘッダーを再設定
                    header_format = workbook.add_format({'bold': True, 'bg_color': '#D9D9D9'})
                    for i, col in enumerate(df.columns):
                        worksheet.write(1, i, col, header_format)
                
                output.seek(0)
                
                # ファイル名を設定
                filename = f"monthly_cost_{asset_type}_{year}"
                if month:
                    filename += f"_{month}"
                filename += f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                
                return send_file(
                    output,
                    as_attachment=True,
                    download_name=filename,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                
            elif export_format == 'pdf':
                # PDFファイルを作成
                output = BytesIO()
                
                # A4横向き
                c = canvas.Canvas(output, pagesize=landscape(A4))
                
                # 日本語フォントを設定
                try:
                    c.setFont('MSGothic', 10)
                except:
                    # フォントが見つからない場合はデフォルトフォントを使用
                    c.setFont('Helvetica', 10)
                
                # タイトル
                c.setFont('MSGothic', 16)
                c.drawString(30 * mm, 200 * mm, title)
                
                # 日付
                c.setFont('MSGothic', 10)
                c.drawString(30 * mm, 190 * mm, f'出力日: {datetime.now().strftime("%Y-%m-%d")}')
                
                # ヘッダー
                headers = list(df.columns)
                header_widths = [25] * len(headers)  # 各列の幅を25mmに設定
                
                x = 30 * mm
                y = 180 * mm
                
                for i, header in enumerate(headers):
                    c.drawString(x, y, header)
                    x += header_widths[i] * mm
                
                # データ
                y -= 10 * mm
                
                for _, row in df.iterrows():
                    x = 30 * mm
                    
                    for i, col in enumerate(df.columns):
                        c.drawString(x, y, str(row[col]))
                        x += header_widths[i] * mm
                    
                    y -= 7 * mm
                    
                    # ページをまたぐ場合は新しいページを作成
                    if y < 30 * mm:
                        c.showPage()
                        
                        # 新しいページのヘッダー
                        c.setFont('MSGothic', 16)
                        c.drawString(30 * mm, 200 * mm, title)
                        
                        c.setFont('MSGothic', 10)
                        c.drawString(30 * mm, 190 * mm, f'出力日: {datetime.now().strftime("%Y-%m-%d")}')
                        
                        x = 30 * mm
                        y = 180 * mm
                        
                        for i, header in enumerate(headers):
                            c.drawString(x, y, header)
                            x += header_widths[i] * mm
                        
                        y -= 10 * mm
                
                # 合計
                y -= 10 * mm
                c.drawString(30 * mm, y, '合計')
                
                # 修繕費用の列を特定
                cost_col = None
                for i, col in enumerate(df.columns):
                    if '修繕費用' in col:
                        cost_col = i
                        break
                
                if cost_col is not None:
                    x = 30 * mm
                    for i in range(cost_col + 1):
                        x += header_widths[i] * mm
                    c.drawString(x, y, f'{total_cost:,}円')
                
                # 予算情報
                y -= 10 * mm
                c.drawString(30 * mm, y, '年間予算')
                
                if cost_col is not None:
                    x = 30 * mm
                    for i in range(cost_col + 1):
                        x += header_widths[i] * mm
                    c.drawString(x, y, f'{budget_amount:,}円')
                
                y -= 7 * mm
                c.drawString(30 * mm, y, '予算消化率')
                
                if cost_col is not None:
                    x = 30 * mm
                    for i in range(cost_col + 1):
                        x += header_widths[i] * mm
                    c.drawString(x, y, f'{budget_usage_rate:.2f}%')
                
                c.save()
                
                output.seek(0)
                
                # ファイル名を設定
                filename = f"monthly_cost_{asset_type}_{year}"
                if month:
                    filename += f"_{month}"
                filename += f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                
                return send_file(
                    output,
                    as_attachment=True,
                    download_name=filename,
                    mimetype='application/pdf'
                )
            
        except Exception as e:
            flash(f'レポート生成中にエラーが発生しました: {str(e)}', 'danger')
    
    # フォークリフト一覧を取得
    forklifts = Forklift.query.all()
    
    # 倉庫施設一覧を取得
    facilities = Facility.query.all()
    
    # 年のリストを作成
    current_year = Config.CURRENT_DATE.year
    years = list(range(current_year - 5, current_year + 1))
    
    return render_template('report/monthly_cost.html',
                          forklifts=forklifts,
                          facilities=facilities,
                          years=years,
                          asset_types=Config.ASSET_TYPE_NAMES)

@report_bp.route('/vehicle_history', methods=['GET', 'POST'])
def vehicle_history():
    if request.method == 'POST':
        try:
            # フィルター条件を取得
            forklift_id = int(request.form['forklift_id'])
            repair_target_type = request.form.get('repair_target_type')
            
            start_date = None
            end_date = None
            if request.form.get('start_date'):
                start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
            if request.form.get('end_date'):
                end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
            
            # エクスポート形式を取得
            export_format = request.form.get('export_format', 'excel')
            
            # フォークリフト情報を取得
            forklift = Forklift.query.get_or_404(forklift_id)
            
            # クエリを構築
            query = ForkliftRepair.query.filter(ForkliftRepair.forklift_id == forklift_id)
            
            if repair_target_type:
                query = query.filter(ForkliftRepair.repair_target_type == repair_target_type)
            
            if start_date:
                query = query.filter(ForkliftRepair.repair_date >= start_date)
            
            if end_date:
                query = query.filter(ForkliftRepair.repair_date <= end_date)
            
            # 結果を取得
            repairs = query.order_by(ForkliftRepair.repair_date).all()
            
            # データフレームを作成
            data = []
            for repair in repairs:
                data.append({
                    '修繕日': repair.repair_date.strftime('%Y-%m-%d'),
                    '修繕対象種別': Config.REPAIR_TARGET_TYPE_NAMES.get(repair.repair_target_type, repair.repair_target_type),
                    '修繕項目': repair.repair_item,
                    '修繕費用': repair.repair_cost,
                    '修繕理由': Config.REPAIR_REASON_NAMES.get(repair.repair_reason, repair.repair_reason),
                    'アワーメーター': repair.hour_meter,
                    '業者': repair.contractor,
                    '備考': repair.notes or ''
                })
            
            df = pd.DataFrame(data)
            
            # タイトルを設定
            title = f'フォークリフト修繕履歴 - {forklift.management_number}'
            
            if export_format == 'excel':
                # Excelファイルを作成
                output = BytesIO()
                
                # Excelファイルに書き込み
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, sheet_name='修繕履歴', index=False)
                    
                    # シートを取得
                    worksheet = writer.sheets['修繕履歴']
                    workbook = writer.book
                    
                    # 列幅を調整
                    for i, col in enumerate(df.columns):
                        column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
                        worksheet.set_column(i, i, column_width)
                    
                    # フォークリフト情報を追加
                    info_sheet = workbook.add_worksheet('フォークリフト情報')
                    
                    info_sheet.write(0, 0, 'フォークリフト情報')
                    info_sheet.write(1, 0, '管理番号')
                    info_sheet.write(1, 1, forklift.management_number)
                    info_sheet.write(2, 0, 'メーカー')
                    info_sheet.write(2, 1, forklift.manufacturer)
                    info_sheet.write(3, 0, 'タイプ')
                    info_sheet.write(3, 1, forklift.type_name)
                    info_sheet.write(4, 0, '動力')
                    info_sheet.write(4, 1, forklift.power_source_name)
                    info_sheet.write(5, 0, '機種')
                    info_sheet.write(5, 1, forklift.model)
                    info_sheet.write(6, 0, '製造年月日')
                    info_sheet.write(6, 1, forklift.manufacture_date.strftime('%Y-%m-%d'))
                    info_sheet.write(7, 0, '経過年数')
                    info_sheet.write(7, 1, f'{forklift.elapsed_years:.2f}年')
                    info_sheet.write(8, 0, '配置倉庫')
                    info_sheet.write(8, 1, f'{forklift.warehouse_group} {forklift.warehouse_number} {forklift.floor}')
                    
                    # 列幅を調整
                    info_sheet.set_column(0, 0, 15)
                    info_sheet.set_column(1, 1, 30)
                    
                    # タイトルを追加
                    title_format = workbook.add_format({'bold': True, 'font_size': 14})
                    worksheet.write(0, 0, title, title_format)
                    
                    # データを1行下にずらす
                    for i in range(len(df) + 1, 0, -1):
                        for j in range(len(df.columns)):
                            cell_value = worksheet.table[i - 1][j].value
                            worksheet.write(i, j, cell_value)
                    
                    # ヘッダーを再設定
                    header_format = workbook.add_format({'bold': True, 'bg_color': '#D9D9D9'})
                    for i, col in enumerate(df.columns):
                        worksheet.write(1, i, col, header_format)
                
                output.seek(0)
                
                # ファイル名を設定
                filename = f"vehicle_history_{forklift.management_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                
                return send_file(
                    output,
                    as_attachment=True,
                    download_name=filename,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                
            elif export_format == 'pdf':
                # PDFファイルを作成
                output = BytesIO()
                
                # A4横向き
                c = canvas.Canvas(output, pagesize=landscape(A4))
                
                # 日本語フォントを設定
                try:
                    c.setFont('MSGothic', 10)
                except:
                    # フォントが見つからない場合はデフォルトフォントを使用
                    c.setFont('Helvetica', 10)
                
                # タイトル
                c.setFont('MSGothic', 16)
                c.drawString(30 * mm, 200 * mm, title)
                
                # 日付
                c.setFont('MSGothic', 10)
                c.drawString(30 * mm, 190 * mm, f'出力日: {datetime.now().strftime("%Y-%m-%d")}')
                
                # フォークリフト情報
                c.drawString(30 * mm, 180 * mm, 'フォークリフト情報:')
                c.drawString(30 * mm, 175 * mm, f'管理番号: {forklift.management_number}')
                c.drawString(30 * mm, 170 * mm, f'メーカー: {forklift.manufacturer}')
                c.drawString(30 * mm, 165 * mm, f'タイプ: {forklift.type_name}')
                c.drawString(30 * mm, 160 * mm, f'動力: {forklift.power_source_name}')
                c.drawString(30 * mm, 155 * mm, f'製造年月日: {forklift.manufacture_date.strftime("%Y-%m-%d")}')
                c.drawString(30 * mm, 150 * mm, f'経過年数: {forklift.elapsed_years:.2f}年')
                c.drawString(30 * mm, 145 * mm, f'配置倉庫: {forklift.warehouse_group} {forklift.warehouse_number} {forklift.floor}')
                
                # ヘッダー
                headers = list(df.columns)
                header_widths = [20, 25, 30, 15, 20, 15, 25, 30]  # 各列の幅を設定
                
                x = 30 * mm
                y = 130 * mm
                
                for i, header in enumerate(headers):
                    c.drawString(x, y, header)
                    x += header_widths[i] * mm
                
                # データ
                y -= 10 * mm
                
                for _, row in df.iterrows():
                    x = 30 * mm
                    
                    for i, col in enumerate(df.columns):
                        c.drawString(x, y, str(row[col]))
                        x += header_widths[i] * mm
                    
                    y -= 7 * mm
                    
                    # ページをまたぐ場合は新しいページを作成
                    if y < 20 * mm:
                        c.showPage()
                        
                        # 新しいページのヘッダー
                        c.setFont('MSGothic', 16)
                        c.drawString(30 * mm, 200 * mm, title)
                        
                        c.setFont('MSGothic', 10)
                        c.drawString(30 * mm, 190 * mm, f'出力日: {datetime.now().strftime("%Y-%m-%d")}')
                        
                        x = 30 * mm
                        y = 180 * mm
                        
                        for i, header in enumerate(headers):
                            c.drawString(x, y, header)
                            x += header_widths[i] * mm
                        
                        y -= 10 * mm
                
                c.save()
                
                output.seek(0)
                
                # ファイル名を設定
                filename = f"vehicle_history_{forklift.management_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                
                return send_file(
                    output,
                    as_attachment=True,
                    download_name=filename,
                    mimetype='application/pdf'
                )
            
        except Exception as e:
            flash(f'レポート生成中にエラーが発生しました: {str(e)}', 'danger')
    
    # フォークリフト一覧を取得
    forklifts = Forklift.query.all()
    
    return render_template('report/vehicle_history.html',
                          forklifts=forklifts,
                          repair_target_types=Config.REPAIR_TARGET_TYPE_NAMES)

@report_bp.route('/repair_target_summary', methods=['GET', 'POST'])
def repair_target_summary():
    if request.method == 'POST':
        try:
            # フィルター条件を取得
            year = int(request.form.get('year', Config.CURRENT_DATE.year))
            
            # エクスポート形式を取得
            export_format = request.form.get('export_format', 'excel')
            
            # 修繕対象種別ごとの集計を取得
            target_summary = db.session.query(
                ForkliftRepair.repair_target_type,
                func.count(ForkliftRepair.id).label('count'),
                func.sum(ForkliftRepair.repair_cost).label('total_cost')
            ).filter(
                extract('year', ForkliftRepair.repair_date) == year
            ).group_by(
                ForkliftRepair.repair_target_type
            ).all()
            
            # データフレームを作成
            data = []
            for target_type, count, total_cost in target_summary:
                data.append({
                    '修繕対象種別': Config.REPAIR_TARGET_TYPE_NAMES.get(target_type, target_type),
                    '件数': count,
                    '合計金額': total_cost
                })
            
            df = pd.DataFrame(data)
            
            # 合計を計算
            total_count = sum(item[1] for item in target_summary)
            total_amount = sum(item[2] for item in target_summary)
            
            # タイトルを設定
            title = f'{year}年 修繕対象種別実績一覧'
            
            if export_format == 'excel':
                # Excelファイルを作成
                output = BytesIO()
                
                # Excelファイルに書き込み
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, sheet_name='修繕対象種別実績', index=False)
                    
                    # シートを取得
                    worksheet = writer.sheets['修繕対象種別実績']
                    workbook = writer.book
                    
                    # 列幅を調整
                    for i, col in enumerate(df.columns):
                        column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
                        worksheet.set_column(i, i, column_width)
                    
                    # 合計行を追加
                    row = len(df) + 2
                    worksheet.write(row, 0, '合計')
                    worksheet.write(row, 1, total_count)
                    worksheet.write(row, 2, total_amount)
                    
                    # タイトルを追加
                    title_format = workbook.add_format({'bold': True, 'font_size': 14})
                    worksheet.write(0, 0, title, title_format)
                    
                    # データを1行下にずらす
                    for i in range(len(df) + 3, 0, -1):
                        for j in range(len(df.columns)):
                            cell_value = worksheet.table[i - 1][j].value
                            worksheet.write(i, j, cell_value)
                    
                    # ヘッダーを再設定
                    header_format = workbook.add_format({'bold': True, 'bg_color': '#D9D9D9'})
                    for i, col in enumerate(df.columns):
                        worksheet.write(1, i, col, header_format)
                    
                    # グラフを追加
                    chart = workbook.add_chart({'type': 'pie'})
                    
                    # データ範囲を設定
                    chart.add_series({
                        'name': '修繕費用',
                        'categories': ['修繕対象種別実績', 2, 0, 1 + len(df), 0],
                        'values': ['修繕対象種別実績', 2, 2, 1 + len(df), 2],
                        'data_labels': {'percentage': True}
                    })
                    
                    chart.set_title({'name': '修繕対象種別別費用割合'})
                    chart.set_size({'width': 500, 'height': 300})
                    
                    # グラフをシートに追加
                    worksheet.insert_chart('E2', chart)
                
                output.seek(0)
                
                # ファイル名を設定
                filename = f"repair_target_summary_{year}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                
                return send_file(
                    output,
                    as_attachment=True,
                    download_name=filename,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                
            elif export_format == 'pdf':
                # PDFファイルを作成
                output = BytesIO()
                
                # A4縦向き
                c = canvas.Canvas(output, pagesize=A4)
                
                # 日本語フォントを設定
                try:
                    c.setFont('MSGothic', 10)
                except:
                    # フォントが見つからない場合はデフォルトフォントを使用
                    c.setFont('Helvetica', 10)
                
                # タイトル
                c.setFont('MSGothic', 16)
                c.drawString(30 * mm, 280 * mm, title)
                
                # 日付
                c.setFont('MSGothic', 10)
                c.drawString(30 * mm, 270 * mm, f'出力日: {datetime.now().strftime("%Y-%m-%d")}')
                
                # ヘッダー
                headers = list(df.columns)
                header_widths = [50, 20, 30]  # 各列の幅を設定
                
                x = 30 * mm
                y = 250 * mm
                
                for i, header in enumerate(headers):
                    c.drawString(x, y, header)
                    x += header_widths[i] * mm
                
                # データ
                y -= 10 * mm
                
                for _, row in df.iterrows():
                    x = 30 * mm
                    
                    for i, col in enumerate(df.columns):
                        c.drawString(x, y, str(row[col]))
                        x += header_widths[i] * mm
                    
                    y -= 7 * mm
                
                # 合計
                y -= 10 * mm
                c.drawString(30 * mm, y, '合計')
                c.drawString(30 * mm + header_widths[0] * mm, y, str(total_count))
                c.drawString(30 * mm + (header_widths[0] + header_widths[1]) * mm, y, str(total_amount))
                
                c.save()
                
                output.seek(0)
                
                # ファイル名を設定
                filename = f"repair_target_summary_{year}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                
                return send_file(
                    output,
                    as_attachment=True,
                    download_name=filename,
                    mimetype='application/pdf'
                )
            
        except Exception as e:
            flash(f'レポート生成中にエラーが発生しました: {str(e)}', 'danger')
    
    # 年のリストを作成
    current_year = Config.CURRENT_DATE.year
    years = list(range(current_year - 5, current_year + 1))
    
    return render_template('report/repair_target_summary.html', years=years)

@report_bp.route('/warehouse_history', methods=['GET', 'POST'])
def warehouse_history():
    if request.method == 'POST':
        try:
            # フィルター条件を取得
            facility_id = int(request.form['facility_id'])
            
            start_date = None
            end_date = None
            if request.form.get('start_date'):
                start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
            if request.form.get('end_date'):
                end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
            
            # エクスポート形式を取得
            export_format = request.form.get('export_format', 'excel')
            
            # 倉庫施設情報を取得
            facility = Facility.query.get_or_404(facility_id)
            
            # クエリを構築
            query = FacilityRepair.query.filter(FacilityRepair.facility_id == facility_id)
            
            if start_date:
                query = query.filter(FacilityRepair.repair_date >= start_date)
            
            if end_date:
                query = query.filter(FacilityRepair.repair_date <= end_date)
            
            # 結果を取得
            repairs = query.order_by(FacilityRepair.repair_date).all()
            
            # データフレームを作成
            data = []
            for repair in repairs:
                data.append({
                    '修繕日': repair.repair_date.strftime('%Y-%m-%d'),
                    '階層': repair.floor,
                    '修繕項目': repair.repair_item,
                    '修繕費用': repair.repair_cost,
                    '修繕理由': Config.REPAIR_REASON_NAMES.get(repair.repair_reason, repair.repair_reason),
                    '業者': repair.contractor,
                    '備考': repair.notes or ''
                })
            
            df = pd.DataFrame(data)
            
            # タイトルを設定
            title = f'倉庫施設修繕履歴 - {facility.warehouse_number}'
            
            if export_format == 'excel':
                # Excelファイルを作成
                output = BytesIO()
                
                # Excelファイルに書き込み
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, sheet_name='修繕履歴', index=False)
                    
                    # シートを取得
                    worksheet = writer.sheets['修繕履歴']
                    workbook = writer.book
                    
                    # 列幅を調整
                    for i, col in enumerate(df.columns):
                        column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
                        worksheet.set_column(i, i, column_width)
                    
                    # 倉庫施設情報を追加
                    info_sheet = workbook.add_worksheet('倉庫施設情報')
                    
                    info_sheet.write(0, 0, '倉庫施設情報')
                    info_sheet.write(1, 0, '倉庫番号')
                    info_sheet.write(1, 1, facility.warehouse_number)
                    info_sheet.write(2, 0, '建築年月日')
                    info_sheet.write(2, 1, facility.construction_date.strftime('%Y-%m-%d'))
                    info_sheet.write(3, 0, '主要構造')
                    info_sheet.write(3, 1, facility.main_structure)
                    info_sheet.write(4, 0, '所有形態')
                    info_sheet.write(4, 1, facility.ownership_type_name)
                    info_sheet.write(5, 0, '階層数')
                    info_sheet.write(5, 1, str(facility.floor_count))
                    
                    # 列幅を調整
                    info_sheet.set_column(0, 0, 15)
                    info_sheet.set_column(1, 1, 30)
                    
                    # タイトルを追加
                    title_format = workbook.add_format({'bold': True, 'font_size': 14})
                    worksheet.write(0, 0, title, title_format)
                    
                    # データを1行下にずらす
                    for i in range(len(df) + 1, 0, -1):
                        for j in range(len(df.columns)):
                            cell_value = worksheet.table[i - 1][j].value
                            worksheet.write(i, j, cell_value)
                    
                    # ヘッダーを再設定
                    header_format = workbook.add_format({'bold': True, 'bg_color': '#D9D9D9'})
                    for i, col in enumerate(df.columns):
                        worksheet.write(1, i, col, header_format)
                
                output.seek(0)
                
                # ファイル名を設定
                filename = f"warehouse_history_{facility.warehouse_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                
                return send_file(
                    output,
                    as_attachment=True,
                    download_name=filename,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                
            elif export_format == 'pdf':
                # PDFファイルを作成
                output = BytesIO()
                
                # A4横向き
                c = canvas.Canvas(output, pagesize=landscape(A4))
                
                # 日本語フォントを設定
                try:
                    c.setFont('MSGothic', 10)
                except:
                    # フォントが見つからない場合はデフォルトフォントを使用
                    c.setFont('Helvetica', 10)
                
                # タイトル
                c.setFont('MSGothic', 16)
                c.drawString(30 * mm, 200 * mm, title)
                
                # 日付
                c.setFont('MSGothic', 10)
                c.drawString(30 * mm, 190 * mm, f'出力日: {datetime.now().strftime("%Y-%m-%d")}')
                
                # 倉庫施設情報
                c.drawString(30 * mm, 180 * mm, '倉庫施設情報:')
                c.drawString(30 * mm, 175 * mm, f'倉庫番号: {facility.warehouse_number}')
                c.drawString(30 * mm, 170 * mm, f'建築年月日: {facility.construction_date.strftime("%Y-%m-%d")}')
                c.drawString(30 * mm, 165 * mm, f'主要構造: {facility.main_structure}')
                c.drawString(30 * mm, 160 * mm, f'所有形態: {facility.ownership_type_name}')
                c.drawString(30 * mm, 155 * mm, f'階層数: {facility.floor_count}')
                
                # ヘッダー
                headers = list(df.columns)
                header_widths = [20, 15, 40, 20, 20, 30, 35]  # 各列の幅を設定
                
                x = 30 * mm
                y = 140 * mm
                
                for i, header in enumerate(headers):
                    c.drawString(x, y, header)
                    x += header_widths[i] * mm
                
                # データ
                y -= 10 * mm
                
                for _, row in df.iterrows():
                    x = 30 * mm
                    
                    for i, col in enumerate(df.columns):
                        c.drawString(x, y, str(row[col]))
                        x += header_widths[i] * mm
                    
                    y -= 7 * mm
                    
                    # ページをまたぐ場合は新しいページを作成
                    if y < 20 * mm:
                        c.showPage()
                        
                        # 新しいページのヘッダー
                        c.setFont('MSGothic', 16)
                        c.drawString(30 * mm, 200 * mm, title)
                        
                        c.setFont('MSGothic', 10)
                        c.drawString(30 * mm, 190 * mm, f'出力日: {datetime.now().strftime("%Y-%m-%d")}')
                        
                        x = 30 * mm
                        y = 180 * mm
                        
                        for i, header in enumerate(headers):
                            c.drawString(x, y, header)
                            x += header_widths[i] * mm
                        
                        y -= 10 * mm
                
                c.save()
                
                output.seek(0)
                
                # ファイル名を設定
                filename = f"warehouse_history_{facility.warehouse_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                
                return send_file(
                    output,
                    as_attachment=True,
                    download_name=filename,
                    mimetype='application/pdf'
                )
            
        except Exception as e:
            flash(f'レポート生成中にエラーが発生しました: {str(e)}', 'danger')
    
    # 倉庫施設一覧を取得
    facilities = Facility.query.all()
    
    return render_template('report/warehouse_history.html', facilities=facilities)