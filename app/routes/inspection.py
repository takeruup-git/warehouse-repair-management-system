from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_file
from app.models import db, AuditLog
from app.models.forklift import Forklift
from app.models.inspection import BatteryFluidCheck, PeriodicSelfInspection, PreShiftInspection
from app.models.master import Employee
from datetime import datetime, timedelta
import os
import pandas as pd
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from config import Config

inspection_bp = Blueprint('inspection', __name__)

# 日本語フォントの登録
try:
    pdfmetrics.registerFont(TTFont('MSGothic', 'msgothic.ttc'))
except:
    # フォントが見つからない場合はデフォルトフォントを使用
    pass

@inspection_bp.route('/')
def index():
    return render_template('inspection/index.html')

@inspection_bp.route('/battery_fluid')
def battery_fluid():
    # バッテリー液量点検表の一覧を取得
    checks = BatteryFluidCheck.query.order_by(BatteryFluidCheck.check_date.desc()).all()
    return render_template('inspection/battery_fluid/index.html', checks=checks)

@inspection_bp.route('/battery_fluid/create', methods=['GET', 'POST'])
def create_battery_fluid():
    if request.method == 'POST':
        try:
            # フォームからデータを取得
            check_date = datetime.strptime(request.form['check_date'], '%Y-%m-%d').date()
            forklift_id = int(request.form['forklift_id'])
            management_number = request.form['management_number']
            warehouse = request.form['warehouse']
            elapsed_years = float(request.form['elapsed_years'])
            fluid_level = request.form['fluid_level']
            
            refill_date = None
            if request.form.get('refill_date'):
                refill_date = datetime.strptime(request.form['refill_date'], '%Y-%m-%d').date()
                
            refiller = request.form.get('refiller', '')
            confirmation_date = datetime.strptime(request.form['confirmation_date'], '%Y-%m-%d').date()
            inspector = request.form['inspector']
            notes = request.form.get('notes', '')
            operator = request.form['operator_name']
            
            # バッテリー液量点検表を作成
            check = BatteryFluidCheck(
                check_date=check_date,
                forklift_id=forklift_id,
                management_number=management_number,
                warehouse=warehouse,
                elapsed_years=elapsed_years,
                fluid_level=fluid_level,
                refill_date=refill_date,
                refiller=refiller,
                confirmation_date=confirmation_date,
                inspector=inspector,
                notes=notes,
                operator=operator
            )
            
            db.session.add(check)
            
            # 監査ログを記録
            audit_log = AuditLog(
                action='create',
                entity_type='battery_fluid_check',
                operator=operator,
                details=f'バッテリー液量点検表 {management_number} を作成'
            )
            db.session.add(audit_log)
            
            db.session.commit()
            
            flash('バッテリー液量点検表が正常に作成されました。', 'success')
            return redirect(url_for('inspection.battery_fluid'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'エラーが発生しました: {str(e)}', 'danger')
    
    # フォークリフト一覧を取得（バッテリー式のみ）
    forklifts = Forklift.query.filter_by(power_source='battery').all()
    
    # 従業員一覧を取得
    employees = Employee.query.filter_by(is_active=True).all()
    
    return render_template('inspection/battery_fluid/create.html',
                          forklifts=forklifts,
                          employees=employees)

@inspection_bp.route('/battery_fluid/<int:id>')
def view_battery_fluid(id):
    check = BatteryFluidCheck.query.get_or_404(id)
    return render_template('inspection/battery_fluid/view.html', check=check)

@inspection_bp.route('/battery_fluid/<int:id>/edit', methods=['GET', 'POST'])
def edit_battery_fluid(id):
    check = BatteryFluidCheck.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # フォームからデータを取得して更新
            check.check_date = datetime.strptime(request.form['check_date'], '%Y-%m-%d').date()
            check.fluid_level = request.form['fluid_level']
            
            if request.form.get('refill_date'):
                check.refill_date = datetime.strptime(request.form['refill_date'], '%Y-%m-%d').date()
            else:
                check.refill_date = None
                
            check.refiller = request.form.get('refiller', '')
            check.confirmation_date = datetime.strptime(request.form['confirmation_date'], '%Y-%m-%d').date()
            check.inspector = request.form['inspector']
            check.notes = request.form.get('notes', '')
            
            db.session.commit()
            
            # 監査ログを記録
            audit_log = AuditLog(
                action='update',
                entity_type='battery_fluid_check',
                entity_id=id,
                operator=request.form.get('operator_name', 'システム'),
                details=f'バッテリー液量点検表 ID:{id} を更新'
            )
            db.session.add(audit_log)
            db.session.commit()
            
            flash('バッテリー液量点検表が正常に更新されました。', 'success')
            return redirect(url_for('inspection.view_battery_fluid', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'エラーが発生しました: {str(e)}', 'danger')
    
    # 従業員一覧を取得
    employees = Employee.query.filter_by(is_active=True).all()
    
    return render_template('inspection/battery_fluid/edit.html',
                          check=check,
                          employees=employees)

@inspection_bp.route('/battery_fluid/<int:id>/delete', methods=['POST'])
def delete_battery_fluid(id):
    check = BatteryFluidCheck.query.get_or_404(id)
    
    try:
        db.session.delete(check)
        
        # 監査ログを記録
        audit_log = AuditLog(
            action='delete',
            entity_type='battery_fluid_check',
            entity_id=id,
            operator=request.form.get('operator_name', 'システム'),
            details=f'バッテリー液量点検表 ID:{id} を削除'
        )
        db.session.add(audit_log)
        db.session.commit()
        
        flash('バッテリー液量点検表が正常に削除されました。', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'削除中にエラーが発生しました: {str(e)}', 'danger')
    
    return redirect(url_for('inspection.battery_fluid'))

@inspection_bp.route('/battery_fluid/export', methods=['GET', 'POST'])
def export_battery_fluid():
    if request.method == 'POST':
        try:
            # フィルター条件を取得
            warehouse = request.form.get('warehouse', '')
            warehouse_group = request.form.get('warehouse_group', '')
            management_number = request.form.get('management_number', '')
            
            # 日付範囲を取得
            start_date = None
            end_date = None
            if request.form.get('start_date'):
                start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
            if request.form.get('end_date'):
                end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
            
            # クエリを構築
            query = BatteryFluidCheck.query
            
            if warehouse:
                query = query.filter(BatteryFluidCheck.warehouse.like(f'%{warehouse}%'))
            
            if management_number:
                query = query.filter(BatteryFluidCheck.management_number.like(f'%{management_number}%'))
            
            if start_date:
                query = query.filter(BatteryFluidCheck.check_date >= start_date)
            
            if end_date:
                query = query.filter(BatteryFluidCheck.check_date <= end_date)
            
            # フォークリフトの条件を追加
            if warehouse_group:
                query = query.join(Forklift).filter(Forklift.warehouse_group == warehouse_group)
            
            # 結果を取得
            checks = query.order_by(BatteryFluidCheck.check_date.desc()).all()
            
            # エクスポート形式を取得
            export_format = request.form.get('export_format', 'excel')
            
            if export_format == 'excel':
                # Excelファイルを作成
                output = BytesIO()
                
                # データフレームを作成
                data = []
                for check in checks:
                    data.append({
                        '点検日': check.check_date.strftime('%Y-%m-%d'),
                        '管理番号': check.management_number,
                        '倉庫': check.warehouse,
                        '経過年数': check.elapsed_years,
                        '液量': check.fluid_level,
                        '補充日': check.refill_date.strftime('%Y-%m-%d') if check.refill_date else '',
                        '補充者': check.refiller,
                        '確認日': check.confirmation_date.strftime('%Y-%m-%d'),
                        '点検責任者': check.inspector,
                        '備考': check.notes
                    })
                
                df = pd.DataFrame(data)
                
                # Excelファイルに書き込み
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, sheet_name='バッテリー液量点検表', index=False)
                    
                    # シートを取得
                    worksheet = writer.sheets['バッテリー液量点検表']
                    
                    # 列幅を調整
                    for i, col in enumerate(df.columns):
                        column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
                        worksheet.set_column(i, i, column_width)
                
                output.seek(0)
                
                # ファイル名を設定
                filename = f"battery_fluid_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                
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
                c.drawString(30 * mm, 200 * mm, 'バッテリー液量点検表')
                
                # 日付
                c.setFont('MSGothic', 10)
                c.drawString(30 * mm, 190 * mm, f'出力日: {datetime.now().strftime("%Y-%m-%d")}')
                
                # ヘッダー
                headers = ['点検日', '管理番号', '倉庫', '経過年数', '液量', '補充日', '補充者', '確認日', '点検責任者']
                header_widths = [20, 20, 30, 15, 15, 20, 20, 20, 20]
                
                x = 30 * mm
                y = 180 * mm
                
                for i, header in enumerate(headers):
                    c.drawString(x, y, header)
                    x += header_widths[i] * mm
                
                # データ
                y -= 10 * mm
                
                for check in checks:
                    x = 30 * mm
                    
                    c.drawString(x, y, check.check_date.strftime('%Y-%m-%d'))
                    x += header_widths[0] * mm
                    
                    c.drawString(x, y, check.management_number)
                    x += header_widths[1] * mm
                    
                    c.drawString(x, y, check.warehouse)
                    x += header_widths[2] * mm
                    
                    c.drawString(x, y, str(check.elapsed_years))
                    x += header_widths[3] * mm
                    
                    c.drawString(x, y, check.fluid_level)
                    x += header_widths[4] * mm
                    
                    c.drawString(x, y, check.refill_date.strftime('%Y-%m-%d') if check.refill_date else '')
                    x += header_widths[5] * mm
                    
                    c.drawString(x, y, check.refiller)
                    x += header_widths[6] * mm
                    
                    c.drawString(x, y, check.confirmation_date.strftime('%Y-%m-%d'))
                    x += header_widths[7] * mm
                    
                    c.drawString(x, y, check.inspector)
                    
                    y -= 7 * mm
                    
                    # ページをまたぐ場合は新しいページを作成
                    if y < 20 * mm:
                        c.showPage()
                        
                        # 新しいページのヘッダー
                        c.setFont('MSGothic', 16)
                        c.drawString(30 * mm, 200 * mm, 'バッテリー液量点検表')
                        
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
                filename = f"battery_fluid_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                
                return send_file(
                    output,
                    as_attachment=True,
                    download_name=filename,
                    mimetype='application/pdf'
                )
            
        except Exception as e:
            flash(f'エクスポート中にエラーが発生しました: {str(e)}', 'danger')
    
    # フォークリフト一覧を取得（バッテリー式のみ）
    forklifts = Forklift.query.filter_by(power_source='battery').all()
    
    # 倉庫グループ一覧を取得
    warehouse_groups = db.session.query(Forklift.warehouse_group).distinct().all()
    warehouse_groups = [wg[0] for wg in warehouse_groups]
    
    return render_template('inspection/battery_fluid/export.html',
                          forklifts=forklifts,
                          warehouse_groups=warehouse_groups)

@inspection_bp.route('/periodic_self')
def periodic_self():
    # 定期自主検査記録表の一覧を取得
    inspections = PeriodicSelfInspection.query.order_by(PeriodicSelfInspection.inspection_date.desc()).all()
    return render_template('inspection/periodic_self/index.html', inspections=inspections)

@inspection_bp.route('/periodic_self/export', methods=['GET', 'POST'])
def export_periodic_self():
    if request.method == 'POST':
        try:
            # フィルター条件を取得
            warehouse = request.form.get('warehouse', '')
            warehouse_group = request.form.get('warehouse_group', '')
            management_number = request.form.get('management_number', '')
            
            # 日付範囲を取得
            start_date = None
            end_date = None
            if request.form.get('start_date'):
                start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
            if request.form.get('end_date'):
                end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
            
            # クエリを構築
            query = PeriodicSelfInspection.query
            
            if warehouse:
                query = query.filter(PeriodicSelfInspection.warehouse.like(f'%{warehouse}%'))
            
            if management_number:
                query = query.filter(PeriodicSelfInspection.management_number.like(f'%{management_number}%'))
            
            if start_date:
                query = query.filter(PeriodicSelfInspection.inspection_date >= start_date)
            
            if end_date:
                query = query.filter(PeriodicSelfInspection.inspection_date <= end_date)
            
            # フォークリフトの条件を追加
            if warehouse_group:
                query = query.join(Forklift).filter(Forklift.warehouse_group == warehouse_group)
            
            # 結果を取得
            inspections = query.order_by(PeriodicSelfInspection.inspection_date.desc()).all()
            
            # エクスポート形式を取得
            export_format = request.form.get('export_format', 'excel')
            
            if export_format == 'excel':
                # Excelファイルを作成
                output = BytesIO()
                
                # データフレームを作成
                data = []
                for inspection in inspections:
                    data.append({
                        '点検日': inspection.inspection_date.strftime('%Y-%m-%d'),
                        '管理番号': inspection.management_number,
                        '倉庫': inspection.warehouse,
                        'アワーメーター': inspection.hour_meter,
                        '走行装置': '良' if inspection.travel_system_ok else '不良',
                        '荷役装置': '良' if inspection.loading_device_ok else '不良',
                        '電気装置': '良' if inspection.electrical_system_ok else '不良',
                        '制動装置': '良' if inspection.brake_system_ok else '不良',
                        '操縦装置': '良' if inspection.steering_system_ok else '不良',
                        '点検責任者': inspection.inspector,
                        '備考': inspection.notes
                    })
                
                df = pd.DataFrame(data)
                
                # Excelファイルに書き込み
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, sheet_name='定期自主検査記録表', index=False)
                    
                    # シートを取得
                    worksheet = writer.sheets['定期自主検査記録表']
                    
                    # 列幅を調整
                    for i, col in enumerate(df.columns):
                        column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
                        worksheet.set_column(i, i, column_width)
                
                output.seek(0)
                
                # ファイル名を設定
                filename = f"periodic_self_inspection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                
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
                c.drawString(30 * mm, 200 * mm, '定期自主検査記録表')
                
                # 日付
                c.setFont('MSGothic', 10)
                c.drawString(30 * mm, 190 * mm, f'出力日: {datetime.now().strftime("%Y-%m-%d")}')
                
                # ヘッダー
                headers = ['点検日', '管理番号', '倉庫', 'アワーメーター', '走行装置', '荷役装置', '電気装置', '制動装置', '操縦装置', '点検責任者']
                header_widths = [20, 20, 30, 20, 15, 15, 15, 15, 15, 20]
                
                x = 30 * mm
                y = 180 * mm
                
                for i, header in enumerate(headers):
                    c.drawString(x, y, header)
                    x += header_widths[i] * mm
                
                # データ
                y -= 10 * mm
                
                for inspection in inspections:
                    x = 30 * mm
                    
                    c.drawString(x, y, inspection.inspection_date.strftime('%Y-%m-%d'))
                    x += header_widths[0] * mm
                    
                    c.drawString(x, y, inspection.management_number)
                    x += header_widths[1] * mm
                    
                    c.drawString(x, y, inspection.warehouse)
                    x += header_widths[2] * mm
                    
                    c.drawString(x, y, str(inspection.hour_meter))
                    x += header_widths[3] * mm
                    
                    c.drawString(x, y, '良' if inspection.travel_system_ok else '不良')
                    x += header_widths[4] * mm
                    
                    c.drawString(x, y, '良' if inspection.loading_device_ok else '不良')
                    x += header_widths[5] * mm
                    
                    c.drawString(x, y, '良' if inspection.electrical_system_ok else '不良')
                    x += header_widths[6] * mm
                    
                    c.drawString(x, y, '良' if inspection.brake_system_ok else '不良')
                    x += header_widths[7] * mm
                    
                    c.drawString(x, y, '良' if inspection.steering_system_ok else '不良')
                    x += header_widths[8] * mm
                    
                    c.drawString(x, y, inspection.inspector)
                    
                    y -= 7 * mm
                    
                    # ページをまたぐ場合は新しいページを作成
                    if y < 20 * mm:
                        c.showPage()
                        
                        # 新しいページのヘッダー
                        c.setFont('MSGothic', 16)
                        c.drawString(30 * mm, 200 * mm, '定期自主検査記録表')
                        
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
                filename = f"periodic_self_inspection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                
                return send_file(
                    output,
                    as_attachment=True,
                    download_name=filename,
                    mimetype='application/pdf'
                )
            
        except Exception as e:
            flash(f'エクスポート中にエラーが発生しました: {str(e)}', 'danger')
    
    # フォークリフト一覧を取得
    forklifts = Forklift.query.all()
    
    # 倉庫グループ一覧を取得
    warehouse_groups = db.session.query(Forklift.warehouse_group).distinct().all()
    warehouse_groups = [wg[0] for wg in warehouse_groups]
    
    return render_template('inspection/periodic_self/export.html',
                          forklifts=forklifts,
                          warehouse_groups=warehouse_groups)

@inspection_bp.route('/periodic_self/<int:id>')
def view_periodic_self(id):
    inspection = PeriodicSelfInspection.query.get_or_404(id)
    return render_template('inspection/periodic_self/view.html', inspection=inspection)

@inspection_bp.route('/periodic_self/create', methods=['GET', 'POST'])
def create_periodic_self():
    if request.method == 'POST':
        try:
            # フォームからデータを取得
            inspection_date = datetime.strptime(request.form['inspection_date'], '%Y-%m-%d').date()
            management_number = request.form['management_number']
            hour_meter = request.form['hour_meter']
            travel_system_ok = 'travel_system_ok' in request.form
            loading_device_ok = 'loading_device_ok' in request.form
            electrical_system_ok = 'electrical_system_ok' in request.form
            brake_system_ok = 'brake_system_ok' in request.form
            steering_system_ok = 'steering_system_ok' in request.form
            inspector = request.form['inspector']
            notes = request.form['notes']
            operator = request.form['operator']
            
            # 定期自主検査記録表を作成
            inspection = PeriodicSelfInspection(
                inspection_date=inspection_date,
                management_number=management_number,
                hour_meter=hour_meter,
                travel_system_ok=travel_system_ok,
                loading_device_ok=loading_device_ok,
                electrical_system_ok=electrical_system_ok,
                brake_system_ok=brake_system_ok,
                steering_system_ok=steering_system_ok,
                inspector=inspector,
                notes=notes,
                operator=operator
            )
            
            db.session.add(inspection)
            db.session.commit()
            
            # 監査ログに記録
            log = AuditLog(
                action='create',
                entity_type='periodic_self_inspection',
                entity_id=inspection.id,
                operator=operator,
                details=f'定期自主検査記録表を作成しました。管理番号: {management_number}'
            )
            db.session.add(log)
            db.session.commit()
            
            flash('定期自主検査記録表が作成されました', 'success')
            return redirect(url_for('inspection.periodic_self'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'作成中にエラーが発生しました: {str(e)}', 'danger')
    
    # フォークリフト一覧を取得
    forklifts = Forklift.query.all()
    
    return render_template('inspection/periodic_self/create.html',
                          forklifts=forklifts,
                          inspection_results=Config.INSPECTION_RESULT_NAMES)

@inspection_bp.route('/periodic_self/<int:id>/delete', methods=['POST'])
def delete_periodic_self(id):
    inspection = PeriodicSelfInspection.query.get_or_404(id)
    
    try:
        db.session.delete(inspection)
        db.session.commit()
        
        # 監査ログに記録
        log = AuditLog(
            action='delete',
            entity_type='periodic_self_inspection',
            entity_id=id,
            operator=request.form.get('operator_name', 'システム'),
            details=f'定期自主検査記録表を削除しました。管理番号: {inspection.management_number}'
        )
        db.session.add(log)
        db.session.commit()
        
        flash('定期自主検査記録表が削除されました', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'削除中にエラーが発生しました: {str(e)}', 'danger')
    
    return redirect(url_for('inspection.periodic_self'))
    if request.method == 'POST':
        try:
            # フォームからデータを取得
            inspection_date = datetime.strptime(request.form['inspection_date'], '%Y-%m-%d').date()
            forklift_id = int(request.form['forklift_id'])
            management_number = request.form['management_number']
            inspection_type = request.form['inspection_type']
            motor_condition = request.form['motor_condition']
            tire_condition = request.form['tire_condition']
            fork_condition = request.form['fork_condition']
            repair_action = request.form['repair_action']
            inspector = request.form['inspector']
            notes = request.form.get('notes', '')
            operator = request.form['operator_name']
            
            # 定期自主検査記録表を作成
            inspection = PeriodicSelfInspection(
                inspection_date=inspection_date,
                forklift_id=forklift_id,
                management_number=management_number,
                inspection_type=inspection_type,
                motor_condition=motor_condition,
                tire_condition=tire_condition,
                fork_condition=fork_condition,
                repair_action=repair_action,
                inspector=inspector,
                notes=notes,
                operator=operator
            )
            
            db.session.add(inspection)
            
            # 監査ログを記録
            audit_log = AuditLog(
                action='create',
                entity_type='periodic_self_inspection',
                operator=operator,
                details=f'定期自主検査記録表 {management_number} を作成'
            )
            db.session.add(audit_log)
            
            db.session.commit()
            
            flash('定期自主検査記録表が正常に作成されました。', 'success')
            return redirect(url_for('inspection.periodic_self'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'エラーが発生しました: {str(e)}', 'danger')
    
    # フォークリフト一覧を取得
    forklifts = Forklift.query.filter_by(asset_status='active').all()
    
    # 従業員一覧を取得
    employees = Employee.query.filter_by(is_active=True).all()
    
    return render_template('inspection/periodic_self/create.html',
                          forklifts=forklifts,
                          employees=employees,
                          inspection_results=Config.INSPECTION_RESULT_NAMES,
                          repair_actions=Config.REPAIR_ACTION_NAMES)

@inspection_bp.route('/pre_shift')
def pre_shift():
    # 始業前点検報告書の一覧を取得
    inspections = PreShiftInspection.query.order_by(PreShiftInspection.inspection_date.desc()).all()
    return render_template('inspection/pre_shift/index.html', inspections=inspections)

@inspection_bp.route('/pre_shift/<int:id>')
def view_pre_shift(id):
    inspection = PreShiftInspection.query.get_or_404(id)
    return render_template('inspection/pre_shift/view.html', inspection=inspection)

@inspection_bp.route('/pre_shift/create', methods=['GET', 'POST'])
def create_pre_shift():
    if request.method == 'POST':
        try:
            # フォームからデータを取得
            inspection_date = datetime.strptime(request.form['inspection_date'], '%Y-%m-%d').date()
            management_number = request.form['management_number']
            tire_ok = 'tire_ok' in request.form
            brake_ok = 'brake_ok' in request.form
            battery_ok = 'battery_ok' in request.form
            oil_ok = 'oil_ok' in request.form
            fork_ok = 'fork_ok' in request.form
            chain_ok = 'chain_ok' in request.form
            mast_ok = 'mast_ok' in request.form
            warning_light_ok = 'warning_light_ok' in request.form
            horn_ok = 'horn_ok' in request.form
            inspector = request.form['inspector']
            notes = request.form['notes']
            operator = request.form['operator']
            
            # 始業前点検報告書を作成
            inspection = PreShiftInspection(
                inspection_date=inspection_date,
                management_number=management_number,
                tire_ok=tire_ok,
                brake_ok=brake_ok,
                battery_ok=battery_ok,
                oil_ok=oil_ok,
                fork_ok=fork_ok,
                chain_ok=chain_ok,
                mast_ok=mast_ok,
                warning_light_ok=warning_light_ok,
                horn_ok=horn_ok,
                inspector=inspector,
                notes=notes,
                operator=operator
            )
            
            db.session.add(inspection)
            db.session.commit()
            
            # 監査ログに記録
            log = AuditLog(
                action='create',
                entity_type='pre_shift_inspection',
                entity_id=inspection.id,
                operator=operator,
                details=f'始業前点検報告書を作成しました。管理番号: {management_number}'
            )
            db.session.add(log)
            db.session.commit()
            
            flash('始業前点検報告書が作成されました', 'success')
            return redirect(url_for('inspection.pre_shift'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'作成中にエラーが発生しました: {str(e)}', 'danger')
    
    # フォークリフト一覧を取得
    forklifts = Forklift.query.all()
    
    # 従業員一覧を取得
    employees = Employee.query.all() if 'Employee' in globals() else []
    
    return render_template('inspection/pre_shift/create.html',
                          forklifts=forklifts,
                          employees=employees,
                          inspection_results=Config.INSPECTION_RESULT_NAMES)

@inspection_bp.route('/pre_shift/<int:id>/delete', methods=['POST'])
def delete_pre_shift(id):
    inspection = PreShiftInspection.query.get_or_404(id)
    
    try:
        db.session.delete(inspection)
        db.session.commit()
        
        # 監査ログに記録
        log = AuditLog(
            action='delete',
            entity_type='pre_shift_inspection',
            entity_id=id,
            operator=request.form.get('operator_name', 'システム'),
            details=f'始業前点検報告書を削除しました。管理番号: {inspection.management_number}'
        )
        db.session.add(log)
        db.session.commit()
        
        flash('始業前点検報告書が削除されました', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'削除中にエラーが発生しました: {str(e)}', 'danger')
    
    return redirect(url_for('inspection.pre_shift'))
    if request.method == 'POST':
        try:
            # フォームからデータを取得
            inspection_date = datetime.strptime(request.form['inspection_date'], '%Y-%m-%d').date()
            forklift_id = int(request.form['forklift_id'])
            management_number = request.form['management_number']
            inspection_type = request.form['inspection_type']
            hour_meter = int(request.form['hour_meter'])
            operating_hours = float(request.form['operating_hours'])
            fluid_refill = request.form.get('fluid_refill')
            if fluid_refill:
                fluid_refill = float(fluid_refill)
            
            engine_oil = None
            brake_condition = None
            battery_fluid = None
            tire_pressure = None
            
            if inspection_type == 'engine':
                engine_oil = request.form['engine_oil']
                brake_condition = request.form['brake_condition']
            else:  # battery
                battery_fluid = request.form['battery_fluid']
                tire_pressure = request.form['tire_pressure']
            
            inspector = request.form['inspector']
            notes = request.form.get('notes', '')
            operator = request.form['operator_name']
            
            # 始業前点検報告書を作成
            inspection = PreShiftInspection(
                inspection_date=inspection_date,
                forklift_id=forklift_id,
                management_number=management_number,
                inspection_type=inspection_type,
                hour_meter=hour_meter,
                operating_hours=operating_hours,
                fluid_refill=fluid_refill,
                engine_oil=engine_oil,
                brake_condition=brake_condition,
                battery_fluid=battery_fluid,
                tire_pressure=tire_pressure,
                inspector=inspector,
                notes=notes,
                operator=operator
            )
            
            db.session.add(inspection)
            
            # 監査ログを記録
            audit_log = AuditLog(
                action='create',
                entity_type='pre_shift_inspection',
                operator=operator,
                details=f'始業前点検報告書 {management_number} を作成'
            )
            db.session.add(audit_log)
            
            db.session.commit()
            
            flash('始業前点検報告書が正常に作成されました。', 'success')
            return redirect(url_for('inspection.pre_shift'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'エラーが発生しました: {str(e)}', 'danger')
    
    # フォークリフト一覧を取得
    forklifts = Forklift.query.filter_by(asset_status='active').all()
    
    # 従業員一覧を取得
    employees = Employee.query.filter_by(is_active=True).all()
    
    return render_template('inspection/pre_shift/create.html',
                          forklifts=forklifts,
                          employees=employees)