from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_file
from app.models import db
from app.models.forklift import Forklift, ForkliftRepair
from app.models.facility import Facility, FacilityRepair
from app.models.other_repair import OtherRepair
from app.models.master import Budget
from sqlalchemy import func, extract, and_, or_
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO
import json
from config import Config

report_bp = Blueprint('report', __name__)

@report_bp.route('/')
def index():
    return render_template('report/index.html')

@report_bp.route('/database_export', methods=['GET', 'POST'])
def database_export():
    # フォークリフト一覧を取得
    forklifts = Forklift.query.order_by(Forklift.management_number).all()
    
    # 倉庫施設一覧を取得
    facilities = Facility.query.order_by(Facility.warehouse_number).all()
    
    # その他修繕対象一覧を取得
    other_targets = db.session.query(OtherRepair.id, OtherRepair.target_name).distinct().all()
    
    # 倉庫グループと倉庫番号の一覧を取得
    warehouse_groups = db.session.query(Forklift.warehouse_group).distinct().order_by(Forklift.warehouse_group).all()
    warehouse_groups = [group[0] for group in warehouse_groups]
    
    warehouse_numbers = db.session.query(Forklift.warehouse_number).distinct().order_by(Forklift.warehouse_number).all()
    warehouse_numbers = [number[0] for number in warehouse_numbers]
    
    if request.method == 'POST':
        try:
            # 共通パラメータ
            data_type = request.form.get('data_type')
            export_format = request.form.get('export_format', 'excel')
            
            # データ種類に応じた処理
            if data_type == 'repair':
                return export_repair_data(request.form, export_format)
            elif data_type == 'forklift':
                return export_forklift_data(request.form, export_format)
            elif data_type == 'facility':
                return export_facility_data(request.form, export_format)
            else:
                flash('無効なデータ種類が指定されました。', 'danger')
                return redirect(url_for('report.database_export'))
                
        except Exception as e:
            current_app.logger.error(f"エクスポートエラー: {str(e)}")
            flash(f'エクスポート処理中にエラーが発生しました: {str(e)}', 'danger')
            return redirect(url_for('report.database_export'))
    
    # GET リクエスト時のレンダリング
    return render_template(
        'report/database_export.html',
        forklifts=forklifts,
        facilities=facilities,
        other_targets=other_targets,
        warehouse_groups=warehouse_groups,
        warehouse_numbers=warehouse_numbers,
        forklift_types=Config.FORKLIFT_TYPE_NAMES,
        power_sources=Config.POWER_SOURCE_NAMES,
        ownership_types=Config.OWNERSHIP_TYPE_NAMES
    )

def export_repair_data(form_data, export_format):
    """修繕データをエクスポートする"""
    # フィルター条件を取得
    start_date = datetime.strptime(form_data.get('start_date', '2000-01-01'), '%Y-%m-%d').date() if form_data.get('start_date') else None
    end_date = datetime.strptime(form_data.get('end_date', '2099-12-31'), '%Y-%m-%d').date() if form_data.get('end_date') else None
    asset_type = form_data.get('repair_asset_type', 'all')
    target_ids = form_data.getlist('repair_target_ids')
    min_cost = form_data.get('min_cost', '')
    min_cost = int(min_cost) if min_cost and min_cost.isdigit() else None
    
    # 全ての修繕データを格納するリスト
    all_repairs = []
    
    # フォークリフト修繕データ
    if asset_type == 'all' or asset_type == 'forklift':
        forklift_repairs_query = db.session.query(
            ForkliftRepair, Forklift
        ).join(
            Forklift, ForkliftRepair.forklift_id == Forklift.id
        )
        
        # 日付フィルター
        if start_date:
            forklift_repairs_query = forklift_repairs_query.filter(ForkliftRepair.repair_date >= start_date)
        if end_date:
            forklift_repairs_query = forklift_repairs_query.filter(ForkliftRepair.repair_date <= end_date)
        
        # 費用フィルター
        if min_cost:
            forklift_repairs_query = forklift_repairs_query.filter(ForkliftRepair.repair_cost >= min_cost)
        
        # 特定のフォークリフトが選択されている場合
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
                'アワーメーター': repair.hour_meter,
                '倉庫グループ': forklift.warehouse_group,
                '倉庫番号': forklift.warehouse_number,
                '階': forklift.floor,
                '備考': repair.notes or '',
                '作成者': repair.operator,
                '作成日時': repair.created_at,
                '更新日時': repair.updated_at
            })
    
    # 倉庫施設修繕データ
    if asset_type == 'all' or asset_type == 'facility':
        facility_repairs_query = db.session.query(
            FacilityRepair, Facility
        ).join(
            Facility, FacilityRepair.facility_id == Facility.id
        )
        
        # 日付フィルター
        if start_date:
            facility_repairs_query = facility_repairs_query.filter(FacilityRepair.repair_date >= start_date)
        if end_date:
            facility_repairs_query = facility_repairs_query.filter(FacilityRepair.repair_date <= end_date)
        
        # 費用フィルター
        if min_cost:
            facility_repairs_query = facility_repairs_query.filter(FacilityRepair.repair_cost >= min_cost)
        
        # 特定の倉庫施設が選択されている場合
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
                'アワーメーター': None,
                '倉庫グループ': None,
                '倉庫番号': facility.warehouse_number,
                '階': repair.floor,
                '備考': repair.notes or '',
                '作成者': repair.operator,
                '作成日時': repair.created_at,
                '更新日時': repair.updated_at
            })
    
    # その他修繕データ
    if asset_type == 'all' or asset_type == 'other':
        other_repairs_query = OtherRepair.query
        
        # 日付フィルター
        if start_date:
            other_repairs_query = other_repairs_query.filter(OtherRepair.repair_date >= start_date)
        if end_date:
            other_repairs_query = other_repairs_query.filter(OtherRepair.repair_date <= end_date)
        
        # 費用フィルター
        if min_cost:
            other_repairs_query = other_repairs_query.filter(OtherRepair.repair_cost >= min_cost)
        
        # 特定のその他資産が選択されている場合
        if asset_type == 'other' and target_ids:
            other_repairs_query = other_repairs_query.filter(OtherRepair.id.in_([int(id) for id in target_ids if id.isdigit()]))
        
        for repair in other_repairs_query.all():
            all_repairs.append({
                '修繕日': repair.repair_date,
                '資産種類': 'その他',
                '資産ID': repair.id,
                '資産名': repair.target_name,
                '修繕項目': repair.category,
                '修繕費用': repair.repair_cost,
                '修繕理由': None,
                '業者': repair.contractor,
                'アワーメーター': None,
                '倉庫グループ': None,
                '倉庫番号': None,
                '階': None,
                '備考': repair.notes or '',
                '作成者': repair.operator,
                '作成日時': repair.created_at,
                '更新日時': repair.updated_at
            })
    
    # データをDataFrameに変換
    df = pd.DataFrame(all_repairs)
    
    if df.empty:
        flash('条件に一致するデータがありませんでした。', 'warning')
        return redirect(url_for('report.database_export'))
    
    # 日付でソート
    df = df.sort_values(by='修繕日')
    
    # 日時列を文字列に変換
    if '修繕日' in df.columns:
        df['修繕日'] = df['修繕日'].dt.strftime('%Y-%m-%d')
    if '作成日時' in df.columns:
        df['作成日時'] = df['作成日時'].dt.strftime('%Y-%m-%d %H:%M:%S')
    if '更新日時' in df.columns:
        df['更新日時'] = df['更新日時'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # ファイル名を設定
    date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"repair_data_export_{date_str}"
    
    # エクスポート形式に応じた処理
    if export_format == 'csv':
        # CSVファイルを作成
        output = BytesIO()
        df.to_csv(output, index=False, encoding='utf-8-sig')
        output.seek(0)
        
        return send_file(
            output,
            as_attachment=True,
            download_name=f"{filename}.csv",
            mimetype='text/csv'
        )
    else:
        # Excelファイルを作成
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='修繕データ', index=False)
            
            workbook = writer.book
            worksheet = writer.sheets['修繕データ']
            
            # 列幅を調整
            for i, col in enumerate(df.columns):
                column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.set_column(i, i, column_width)
            
            # タイトルを追加
            title_format = workbook.add_format({'bold': True, 'font_size': 14})
            filter_text = f"修繕データエクスポート"
            if start_date and end_date:
                filter_text += f" ({start_date.strftime('%Y/%m/%d')} - {end_date.strftime('%Y/%m/%d')})"
            worksheet.write(0, 0, filter_text, title_format)
            
            # データを1行下にずらす
            for i, row in df.iterrows():
                for j, col in enumerate(df.columns):
                    worksheet.write(i + 2, j, row[col])
            
            # ヘッダーを再設定
            header_format = workbook.add_format({'bold': True, 'bg_color': '#D9D9D9'})
            for i, col in enumerate(df.columns):
                worksheet.write(1, i, col, header_format)
        
        output.seek(0)
        
        return send_file(
            output,
            as_attachment=True,
            download_name=f"{filename}.xlsx",
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

def export_forklift_data(form_data, export_format):
    """フォークリフトマスタデータをエクスポートする"""
    # フィルター条件を取得
    forklift_type = form_data.get('forklift_type', 'all')
    power_source = form_data.get('power_source', 'all')
    warehouse_group = form_data.get('warehouse_group', 'all')
    warehouse_number = form_data.get('warehouse_number', 'all')
    
    # クエリを構築
    query = Forklift.query
    
    # フィルター適用
    if forklift_type != 'all':
        query = query.filter(Forklift.forklift_type == forklift_type)
    
    if power_source != 'all':
        query = query.filter(Forklift.power_source == power_source)
    
    if warehouse_group != 'all':
        query = query.filter(Forklift.warehouse_group == warehouse_group)
    
    if warehouse_number != 'all':
        query = query.filter(Forklift.warehouse_number == warehouse_number)
    
    # データを取得
    forklifts = query.order_by(Forklift.management_number).all()
    
    if not forklifts:
        flash('条件に一致するデータがありませんでした。', 'warning')
        return redirect(url_for('report.database_export'))
    
    # データを辞書のリストに変換
    forklift_data = []
    for forklift in forklifts:
        forklift_data.append({
            '管理番号': forklift.management_number,
            'メーカー': forklift.manufacturer,
            'フォークリフト種類': forklift.type_name,
            '動力源': forklift.power_source_name,
            'モデル': forklift.model,
            'シリアル番号': forklift.serial_number,
            '最大荷重(kg)': forklift.load_capacity,
            '製造日': forklift.manufacture_date,
            '経過年数': round(forklift.elapsed_years, 2) if forklift.elapsed_years is not None else None,
            '最大揚高(mm)': forklift.lift_height,
            '倉庫グループ': forklift.warehouse_group,
            '倉庫番号': forklift.warehouse_number,
            '階': forklift.floor,
            '担当者': forklift.operator,
            '更新者': forklift.updated_by
        })
    
    # DataFrameに変換
    df = pd.DataFrame(forklift_data)
    
    # 日付列を文字列に変換
    if '製造日' in df.columns:
        df['製造日'] = df['製造日'].dt.strftime('%Y-%m-%d')
    
    # ファイル名を設定
    date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"forklift_master_export_{date_str}"
    
    # エクスポート形式に応じた処理
    if export_format == 'csv':
        # CSVファイルを作成
        output = BytesIO()
        df.to_csv(output, index=False, encoding='utf-8-sig')
        output.seek(0)
        
        return send_file(
            output,
            as_attachment=True,
            download_name=f"{filename}.csv",
            mimetype='text/csv'
        )
    else:
        # Excelファイルを作成
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='フォークリフトマスタ', index=False)
            
            workbook = writer.book
            worksheet = writer.sheets['フォークリフトマスタ']
            
            # 列幅を調整
            for i, col in enumerate(df.columns):
                column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.set_column(i, i, column_width)
            
            # タイトルを追加
            title_format = workbook.add_format({'bold': True, 'font_size': 14})
            filter_text = "フォークリフトマスタデータエクスポート"
            worksheet.write(0, 0, filter_text, title_format)
            
            # データを1行下にずらす
            for i, row in df.iterrows():
                for j, col in enumerate(df.columns):
                    worksheet.write(i + 2, j, row[col])
            
            # ヘッダーを再設定
            header_format = workbook.add_format({'bold': True, 'bg_color': '#D9D9D9'})
            for i, col in enumerate(df.columns):
                worksheet.write(1, i, col, header_format)
        
        output.seek(0)
        
        return send_file(
            output,
            as_attachment=True,
            download_name=f"{filename}.xlsx",
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

def export_facility_data(form_data, export_format):
    """倉庫施設マスタデータをエクスポートする"""
    # フィルター条件を取得
    ownership_type = form_data.get('ownership_type', 'all')
    min_floor_count = form_data.get('min_floor_count', '')
    min_floor_count = int(min_floor_count) if min_floor_count and min_floor_count.isdigit() else None
    
    # クエリを構築
    query = Facility.query
    
    # フィルター適用
    if ownership_type != 'all':
        query = query.filter(Facility.ownership_type == ownership_type)
    
    if min_floor_count:
        query = query.filter(Facility.floor_count >= min_floor_count)
    
    # データを取得
    facilities = query.order_by(Facility.warehouse_number).all()
    
    if not facilities:
        flash('条件に一致するデータがありませんでした。', 'warning')
        return redirect(url_for('report.database_export'))
    
    # データを辞書のリストに変換
    facility_data = []
    for facility in facilities:
        facility_data.append({
            '倉庫番号': facility.warehouse_number,
            '建設日': facility.construction_date,
            '主要構造': facility.main_structure,
            '所有形態': facility.ownership_type_name,
            '階数': facility.floor_count
        })
    
    # DataFrameに変換
    df = pd.DataFrame(facility_data)
    
    # 日付列を文字列に変換
    if '建設日' in df.columns:
        df['建設日'] = df['建設日'].dt.strftime('%Y-%m-%d')
    
    # ファイル名を設定
    date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"facility_master_export_{date_str}"
    
    # エクスポート形式に応じた処理
    if export_format == 'csv':
        # CSVファイルを作成
        output = BytesIO()
        df.to_csv(output, index=False, encoding='utf-8-sig')
        output.seek(0)
        
        return send_file(
            output,
            as_attachment=True,
            download_name=f"{filename}.csv",
            mimetype='text/csv'
        )
    else:
        # Excelファイルを作成
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='倉庫施設マスタ', index=False)
            
            workbook = writer.book
            worksheet = writer.sheets['倉庫施設マスタ']
            
            # 列幅を調整
            for i, col in enumerate(df.columns):
                column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.set_column(i, i, column_width)
            
            # タイトルを追加
            title_format = workbook.add_format({'bold': True, 'font_size': 14})
            filter_text = "倉庫施設マスタデータエクスポート"
            worksheet.write(0, 0, filter_text, title_format)
            
            # データを1行下にずらす
            for i, row in df.iterrows():
                for j, col in enumerate(df.columns):
                    worksheet.write(i + 2, j, row[col])
            
            # ヘッダーを再設定
            header_format = workbook.add_format({'bold': True, 'bg_color': '#D9D9D9'})
            for i, col in enumerate(df.columns):
                worksheet.write(1, i, col, header_format)
        
        output.seek(0)
        
        return send_file(
            output,
            as_attachment=True,
            download_name=f"{filename}.xlsx",
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )