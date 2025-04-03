from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, ValidationError
from wtforms.validators import DataRequired, Email, EqualTo, Length
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('ユーザー名', validators=[DataRequired()])
    password = PasswordField('パスワード', validators=[DataRequired()])
    remember_me = BooleanField('ログイン状態を保持する')
    submit = SubmitField('ログイン')

class RegistrationForm(FlaskForm):
    username = StringField('ユーザー名', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('メールアドレス', validators=[DataRequired(), Email()])
    full_name = StringField('氏名', validators=[Length(max=64)])
    password = PasswordField('パスワード', validators=[Length(min=8)])
    password2 = PasswordField(
        'パスワード（確認）', 
        validators=[EqualTo('password', message='パスワードが一致しません。')]
    )
    role = SelectField('権限', choices=[
        ('user', '一般ユーザー'),
        ('manager', '管理者'),
        ('admin', 'システム管理者')
    ])
    is_active = BooleanField('アクティブ', default=True)
    submit = SubmitField('登録')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('このユーザー名は既に使用されています。別のユーザー名を選択してください。')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('このメールアドレスは既に使用されています。別のメールアドレスを入力してください。')

class PasswordChangeForm(FlaskForm):
    current_password = PasswordField('現在のパスワード', validators=[DataRequired()])
    new_password = PasswordField('新しいパスワード', validators=[
        DataRequired(),
        Length(min=8, message='パスワードは8文字以上である必要があります。')
    ])
    confirm_password = PasswordField('新しいパスワード（確認）', validators=[
        DataRequired(),
        EqualTo('new_password', message='パスワードが一致しません。')
    ])
    submit = SubmitField('パスワードを変更')