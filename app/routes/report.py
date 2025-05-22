from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_file
from app.models import db
from app.models.forklift import Forklift, ForkliftRepair
from app.models.facility import Facility, FacilityRepair
from app.models.other_repair import OtherRepair
from app.models.master import Budget
from sqlalchemy import func, extract, and_
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import numpy as np
import io
import base64
from config import Config

report_bp = Blueprint('report', __name__)

@report_bp.route('/')
def index():
    return render_template('report/index.html')

@report_bp.route('/repair_cost_export', methods=['GET', 'POST'])
def repair_cost_export():
    if request.method == 'POST':
        try:
            # フィルター条件を取得
            start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
            asset_type = request.form.get('asset_type')
            target_ids = request.form.getlist('target_ids')
            export_format = request.form.get('export_format', 'excel')
            
            # 対象期間の月リストを作成
            months = []
            current_date = start_date.replace(day=1)
            while current_date <= end_date:
                months.append(current_date)
                # 次の月に進む
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)
            
            # 月ごとのデータを格納する辞書
            monthly_data = {}
            
            # 資産タイプに応じたデータ取得
            if asset_type == 'all' or asset_type == 'facility_forklift_other' or asset_type == 'forklift':
                # フォークリフトのデータを取得
                forklift_query = db.session.query(
                    extract('year', ForkliftRepair.repair_date).label('year'),
                    extract('month', ForkliftRepair.repair_date).label('month'),
                    Forklift.management_number,
                    func.sum(ForkliftRepair.repair_cost).label('total_cost')
                ).join(
                    Forklift, ForkliftRepair.forklift_id == Forklift.id
                ).filter(
                    ForkliftRepair.repair_date.between(start_date, end_date)
                ).group_by(
                    extract('year', ForkliftRepair.repair_date),
                    extract('month', ForkliftRepair.repair_date),
                    Forklift.management_number
                )
                
                # 特定のフォークリフトが選択されている場合
                if asset_type == 'forklift' and target_ids:
                    forklift_query = forklift_query.filter(ForkliftRepair.forklift_id.in_([int(id) for id in target_ids if id.isdigit()]))
                
                forklift_results = forklift_query.all()
                
                # 結果を月ごとに整理
                for year, month, management_number, total_cost in forklift_results:
                    month_key = datetime(int(year), int(month), 1).date()
                    if month_key not in monthly_data:
                        monthly_data[month_key] = {}
                    
                    asset_key = f"フォークリフト: {management_number}"
                    monthly_data[month_key][asset_key] = total_cost
            
            if asset_type == 'all' or asset_type == 'facility_forklift_other' or asset_type == 'facility':
                # 倉庫施設のデータを取得
                facility_query = db.session.query(
                    extract('year', FacilityRepair.repair_date).label('year'),
                    extract('month', FacilityRepair.repair_date).label('month'),
                    Facility.warehouse_number,
                    func.sum(FacilityRepair.repair_cost).label('total_cost')
                ).join(
                    Facility, FacilityRepair.facility_id == Facility.id
                ).filter(
                    FacilityRepair.repair_date.between(start_date, end_date)
                ).group_by(
                    extract('year', FacilityRepair.repair_date),
                    extract('month', FacilityRepair.repair_date),
                    Facility.warehouse_number
                )
                
                # 特定の倉庫施設が選択されている場合
                if asset_type == 'facility' and target_ids:
                    facility_query = facility_query.filter(FacilityRepair.facility_id.in_([int(id) for id in target_ids if id.isdigit()]))
                
                facility_results = facility_query.all()
                
                # 結果を月ごとに整理
                for year, month, warehouse_number, total_cost in facility_results:
                    month_key = datetime(int(year), int(month), 1).date()
                    if month_key not in monthly_data:
                        monthly_data[month_key] = {}
                    
                    asset_key = f"倉庫施設: {warehouse_number}"
                    monthly_data[month_key][asset_key] = total_cost
            
            if asset_type == 'all' or asset_type == 'facility_forklift_other' or asset_type == 'other':
                # その他資産のデータを取得
                other_query = db.session.query(
                    extract('year', OtherRepair.repair_date).label('year'),
                    extract('month', OtherRepair.repair_date).label('month'),
                    OtherRepair.target_name,
                    func.sum(OtherRepair.repair_cost).label('total_cost')
                ).filter(
                    OtherRepair.repair_date.between(start_date, end_date)
                ).group_by(
                    extract('year', OtherRepair.repair_date),
                    extract('month', OtherRepair.repair_date),
                    OtherRepair.target_name
                )
                
                # 特定のその他資産が選択されている場合
                if asset_type == 'other' and target_ids:
                    other_query = other_query.filter(OtherRepair.id.in_([int(id) for id in target_ids if id.isdigit()]))
                
                other_results = other_query.all()
                
                # 結果を月ごとに整理
                for year, month, target_name, total_cost in other_results:
                    month_key = datetime(int(year), int(month), 1).date()
                    if month_key not in monthly_data:
                        monthly_data[month_key] = {}
                    
                    asset_key = f"その他: {target_name}"
                    monthly_data[month_key][asset_key] = total_cost
            
            # 全ての資産キーを取得
            all_asset_keys = set()
            for month_data in monthly_data.values():
                all_asset_keys.update(month_data.keys())
            all_asset_keys = sorted(list(all_asset_keys))
            
            # 詳細データを含むデータフレームを作成
            # 全ての修繕データを取得
            all_repairs = []
            
            # フォークリフト修繕データ
            if asset_type == 'all' or asset_type == 'facility_forklift_other' or asset_type == 'forklift':
                forklift_repairs_query = db.session.query(
                    ForkliftRepair, Forklift
                ).join(
                    Forklift, ForkliftRepair.forklift_id == Forklift.id
                ).filter(
                    ForkliftRepair.repair_date.between(start_date, end_date)
                )
                
                if asset_type == 'forklift' and target_ids:
                    forklift_repairs_query = forklift_repairs_query.filter(ForkliftRepair.forklift_id.in_([int(id) for id in target_ids if id.isdigit()]))
                
                for repair, forklift in forklift_repairs_query.all():
                    all_repairs.append({
                        '修繕日': repair.repair_date,
                        '資産種類': 'フォークリフト',
                        '資産ID': forklift.id,
                        '資産名': forklift.management_number,
                        '修繕項目': repair.repair_item,
                        '修繕費用': repair.repair_cost,
                        '修繕理由': repair.repair_reason,
                        '業者': repair.contractor,
                        '備考': repair.notes or ''
                    })
            
            # 倉庫施設修繕データ
            if asset_type == 'all' or asset_type == 'facility_forklift_other' or asset_type == 'facility':
                facility_repairs_query = db.session.query(
                    FacilityRepair, Facility
                ).join(
                    Facility, FacilityRepair.facility_id == Facility.id
                ).filter(
                    FacilityRepair.repair_date.between(start_date, end_date)
                )
                
                if asset_type == 'facility' and target_ids:
                    facility_repairs_query = facility_repairs_query.filter(FacilityRepair.facility_id.in_([int(id) for id in target_ids if id.isdigit()]))
                
                for repair, facility in facility_repairs_query.all():
                    all_repairs.append({
                        '修繕日': repair.repair_date,
                        '資産種類': '倉庫施設',
                        '資産ID': facility.id,
                        '資産名': facility.warehouse_number,
                        '修繕項目': repair.repair_item,
                        '修繕費用': repair.repair_cost,
                        '修繕理由': repair.repair_reason,
                        '業者': repair.contractor,
                        '備考': repair.notes or ''
                    })
            
            # その他修繕データ
            if asset_type == 'all' or asset_type == 'facility_forklift_other' or asset_type == 'other':
                other_repairs_query = OtherRepair.query.filter(
                    OtherRepair.repair_date.between(start_date, end_date)
                )
                
                if asset_type == 'other' and target_ids:
                    other_repairs_query = other_repairs_query.filter(OtherRepair.id.in_([int(id) for id in target_ids if id.isdigit()]))
                
                for repair in other_repairs_query.all():
                    all_repairs.append({
                        '修繕日': repair.repair_date,
                        '資産種類': 'その他',
                        '資産ID': repair.id,
                        '資産名': repair.target_name,
                        '修繕項目': repair.repair_item,
                        '修繕費用': repair.repair_cost,
                        '修繕理由': repair.repair_reason,
                        '業者': repair.contractor,
                        '備考': repair.notes or ''
                    })
            
            # 詳細データをDataFrameに変換
            df_details = pd.DataFrame(all_repairs)
            if not df_details.empty:
                df_details = df_details.sort_values(by='修繕日')
            
            # 集計データを作成
            data = []
            for month in months:
                month_str = month.strftime('%Y年%m月')
                row_data = {'月': month_str}
                
                # 各資産の修繕費を追加
                for asset_key in all_asset_keys:
                    row_data[asset_key] = monthly_data.get(month, {}).get(asset_key, 0)
                
                data.append(row_data)
            
            df = pd.DataFrame(data)
            
            # 合計行を追加
            totals = {'月': '合計'}
            for asset_key in all_asset_keys:
                totals[asset_key] = df[asset_key].sum()
            
            df = pd.concat([df, pd.DataFrame([totals])], ignore_index=True)
            
            # グラフ用のデータを準備
            graph_data = {
                'months': [month.strftime('%Y-%m') for month in months],
                'datasets': []
            }
            
            # 色のリスト
            colors = [
                '#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b', 
                '#6f42c1', '#fd7e14', '#20c9a6', '#5a5c69', '#858796'
            ]
            
            # 各資産のデータセットを作成
            for i, asset_key in enumerate(all_asset_keys):
                color_index = i % len(colors)
                dataset = {
                    'label': asset_key,
                    'data': [monthly_data.get(month, {}).get(asset_key, 0) for month in months],
                    'backgroundColor': colors[color_index]
                }
                graph_data['datasets'].append(dataset)
            
            # Excelファイルを作成
            output = BytesIO()
            
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # 集計データシートを作成
                df.to_excel(writer, sheet_name='修繕費集計', index=False)
                
                workbook = writer.book
                worksheet = writer.sheets['修繕費集計']
                
                # 列幅を調整
                for i, col in enumerate(df.columns):
                    column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
                    worksheet.set_column(i, i, column_width)
                
                # タイトルを追加
                title_format = workbook.add_format({'bold': True, 'font_size': 14})
                title = f'修繕費用レポート ({start_date.strftime("%Y/%m/%d")} - {end_date.strftime("%Y/%m/%d")})'
                worksheet.write(0, 0, title, title_format)
                
                # データを1行下にずらす
                for i, row in df.iterrows():
                    for j, col in enumerate(df.columns):
                        worksheet.write(i + 2, j, row[col])
                
                # ヘッダーを再設定
                header_format = workbook.add_format({'bold': True, 'bg_color': '#D9D9D9'})
                for i, col in enumerate(df.columns):
                    worksheet.write(1, i, col, header_format)
                
                # 詳細データシートを作成
                if not df_details.empty:
                    # 日付を文字列に変換
                    df_details['修繕日'] = df_details['修繕日'].dt.strftime('%Y-%m-%d')
                    df_details.to_excel(writer, sheet_name='修繕詳細データ', index=False)
                    
                    detail_worksheet = writer.sheets['修繕詳細データ']
                    
                    # 列幅を調整
                    for i, col in enumerate(df_details.columns):
                        column_width = max(df_details[col].astype(str).map(len).max(), len(col)) + 2
                        detail_worksheet.set_column(i, i, column_width)
                    
                    # タイトルを追加
                    detail_worksheet.write(0, 0, f'修繕詳細データ ({start_date.strftime("%Y/%m/%d")} - {end_date.strftime("%Y/%m/%d")})', title_format)
                    
                    # データを1行下にずらす
                    for i, row in df_details.iterrows():
                        for j, col in enumerate(df_details.columns):
                            detail_worksheet.write(i + 2, j, row[col])
                    
                    # ヘッダーを再設定
                    for i, col in enumerate(df_details.columns):
                        detail_worksheet.write(1, i, col, header_format)
                
                # グラフシートを作成
                chart_sheet = workbook.add_worksheet('修繕費グラフ')
                
                # グラフの代わりに説明文を追加
                chart_sheet.write(1, 1, '修繕費用の月別推移データ')
                chart_sheet.write(3, 1, '※データシートの内容を参照してください。')
                
            output.seek(0)
            
            # ファイル名を設定
            filename = f"repair_cost_export_{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            current_app.logger.info(f"レポート生成完了: {filename}")
            
            return send_file(
                output,
                as_attachment=True,
                download_name=filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        
        elif export_format == 'csv':
            # CSVファイルを作成
            output = BytesIO()
            
            # 詳細データを含むCSVを作成
            all_data = []
            
            # フォークリフトの詳細データを追加
            if asset_type == 'all' or asset_type == 'facility_forklift_other' or asset_type == 'forklift':
                forklift_details = db.session.query(
                    ForkliftRepair.repair_date,
                    Forklift.management_number,
                    Forklift.manufacturer,
                    Forklift.model,
                    Forklift.warehouse_group,
                    ForkliftRepair.repair_target_type,
                    ForkliftRepair.repair_item,
                    ForkliftRepair.repair_cost,
                    ForkliftRepair.repair_reason,
                    ForkliftRepair.contractor,
                    ForkliftRepair.notes
                ).join(
                    Forklift, ForkliftRepair.forklift_id == Forklift.id
                ).filter(
                    ForkliftRepair.repair_date.between(start_date, end_date)
                )
                
                if asset_type == 'forklift' and target_ids:
                    forklift_details = forklift_details.filter(ForkliftRepair.forklift_id.in_([int(id) for id in target_ids if id.isdigit()]))
                
                for repair in forklift_details.all():
                    all_data.append({
                        '修繕日': repair.repair_date.strftime('%Y-%m-%d'),
                        '資産種別': 'フォークリフト',
                        '管理番号': repair.management_number,
                        'メーカー': repair.manufacturer,
                        '型式': repair.model,
                        '倉庫グループ': repair.warehouse_group,
                        '修繕対象種別': Config.REPAIR_TARGET_TYPE_NAMES.get(repair.repair_target_type, repair.repair_target_type),
                        '修繕項目': repair.repair_item,
                        '修繕費用': repair.repair_cost,
                        '修繕理由': Config.REPAIR_REASON_NAMES.get(repair.repair_reason, repair.repair_reason),
                        '業者': repair.contractor,
                        '備考': repair.notes or ''
                    })
                
                # 倉庫施設の詳細データを追加
                if asset_type == 'all' or asset_type == 'facility_forklift_other' or asset_type == 'facility':
                facility_details = db.session.query(
                    FacilityRepair.repair_date,
                    Facility.warehouse_number,
                    Facility.address,
                    Facility.warehouse_group,
                    FacilityRepair.floor,
                    FacilityRepair.repair_item,
                    FacilityRepair.repair_cost,
                    FacilityRepair.repair_reason,
                    FacilityRepair.vendor,
                    FacilityRepair.notes
                ).join(
                    Facility, FacilityRepair.facility_id == Facility.id
                ).filter(
                    FacilityRepair.repair_date.between(start_date, end_date)
                )
                
                if asset_type == 'facility' and target_ids:
                    facility_details = facility_details.filter(FacilityRepair.facility_id.in_([int(id) for id in target_ids if id.isdigit()]))
                
                for repair in facility_details.all():
                    all_data.append({
                        '修繕日': repair.repair_date.strftime('%Y-%m-%d'),
                        '資産種別': '倉庫施設',
                        '管理番号': repair.warehouse_number,
                        'メーカー': '',
                        '型式': '',
                        '倉庫グループ': repair.warehouse_group,
                        '修繕対象種別': f'倉庫施設 {repair.floor}階',
                        '修繕項目': repair.repair_item,
                        '修繕費用': repair.repair_cost,
                        '修繕理由': Config.REPAIR_REASON_NAMES.get(repair.repair_reason, repair.repair_reason),
                        '業者': repair.vendor,
                        '備考': repair.notes or ''
                    })
                
                # その他修繕の詳細データを追加
                if asset_type == 'all' or asset_type == 'facility_forklift_other' or asset_type == 'other':
                other_details = db.session.query(
                    OtherRepair.repair_date,
                    OtherRepair.target_name,
                    OtherRepair.repair_target,
                    OtherRepair.repair_item,
                    OtherRepair.repair_cost,
                    OtherRepair.vendor,
                    OtherRepair.notes
                ).filter(
                    OtherRepair.repair_date.between(start_date, end_date)
                )
                
                if asset_type == 'other' and target_ids:
                    other_details = other_details.filter(OtherRepair.target_name.in_(target_ids))
                
                for repair in other_details.all():
                    all_data.append({
                        '修繕日': repair.repair_date.strftime('%Y-%m-%d'),
                        '資産種別': 'その他',
                        '管理番号': repair.target_name,
                        'メーカー': '',
                        '型式': '',
                        '倉庫グループ': '',
                        '修繕対象種別': repair.repair_target,
                        '修繕項目': repair.repair_item,
                        '修繕費用': repair.repair_cost,
                        '修繕理由': '',
                        '業者': repair.vendor,
                        '備考': repair.notes or ''
                    })
                
                # データをCSVに変換
                df = pd.DataFrame(all_data)
                
                # 日付でソート
                df = df.sort_values(by='修繕日')
                
                # CSVに出力
                csv_data = df.to_csv(index=False, encoding='utf-8-sig')
                output.write(csv_data.encode('utf-8-sig'))
                output.seek(0)
                
                # ファイル名を設定
                filename = f"repair_cost_export_{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                
                current_app.logger.info(f"CSVレポート生成完了: {filename}")
                
                return send_file(
                output,
                as_attachment=True,
                download_name=filename,
                mimetype='text/csv'
                )
            
        except Exception as e:
            flash(f'レポート生成中にエラーが発生しました: {str(e)}', 'danger')
            current_app.logger.error(f"レポート生成エラー: {str(e)}")
    
    # フォークリフト一覧を取得
    forklifts = Forklift.query.all()
    
    # 倉庫施設一覧を取得
    facilities = Facility.query.all()
    
    # その他修繕対象一覧を取得
    other_targets = db.session.query(OtherRepair.target_name).distinct().all()
    other_targets = [target[0] for target in other_targets]
    
    return render_template('report/repair_cost_export.html',
                          forklifts=forklifts,
                          facilities=facilities,
                          other_targets=other_targets)

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
                    
                    # データを1行下にずらす（ワークシートのテーブル属性にアクセスせずに処理）
                    # 一度データをメモリに読み込む
                    df_with_title = pd.DataFrame([[''] * len(df.columns)] + df.values.tolist(), columns=df.columns)
                    # タイトル行を追加
                    df_with_title.iloc[0, 0] = title
                    # 再度エクセルに書き込み
                    df_with_title.to_excel(writer, sheet_name='修繕履歴', index=False, header=True)
                    
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
            target_summary_query = db.session.query(
                ForkliftRepair.repair_target_type,
                func.count(ForkliftRepair.id).label('count'),
                func.sum(ForkliftRepair.repair_cost).label('total_cost')
            ).filter(
                extract('year', ForkliftRepair.repair_date) == year
            ).group_by(
                ForkliftRepair.repair_target_type
            )
            
            # クエリをログに出力（詳細版）
            current_app.logger.info(f"修繕対象種別集計クエリ（詳細版）: {str(target_summary_query.statement.compile(compile_kwargs={'literal_binds': True}))}")
            
            # SQLクエリをログに出力
            current_app.logger.info(f"修繕対象種別集計クエリ: {str(target_summary_query)}")
            
            target_summary = target_summary_query.all()
            
            # 結果をログに出力
            current_app.logger.info(f"修繕対象種別集計結果: {len(target_summary)}件")
            
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
                    # Note: We can't directly access worksheet.table[i-1][j].value in xlsxwriter
                    # Instead, we'll use the dataframe to get the values
                    
                    # First write the title in row 0
                    worksheet.write(0, 0, title, title_format)
                    
                    # Then write the dataframe starting from row 2 (leaving row 1 for headers)
                    for i, (_, row) in enumerate(df.iterrows(), start=2):
                        for j, value in enumerate(row):
                            worksheet.write(i, j, value)
                    
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
                    
                    # データを1行下にずらす（ワークシートのテーブル属性にアクセスせずに処理）
                    # 一度データをメモリに読み込む
                    df_with_title = pd.DataFrame([[''] * len(df.columns)] + df.values.tolist(), columns=df.columns)
                    # タイトル行を追加
                    df_with_title.iloc[0, 0] = title
                    # 再度エクセルに書き込み
                    df_with_title.to_excel(writer, sheet_name='修繕履歴', index=False, header=True)
                    
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