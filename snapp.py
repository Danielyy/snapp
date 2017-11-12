import os
import re
from flask import request, redirect, flash, session
import datetime
from flask import Flask, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from wtforms import Form, validators, StringField, HiddenField, SubmitField, DateField, SelectField, ValidationError, FileField
from flask_bootstrap import Bootstrap

basedir = os.path.abspath(os.path.dirname(__file__))
ALLOWED_EXTENSIONS = set(['txt'])

app = Flask(__name__)
bootstrap = Bootstrap(app)
project_dir = os.path.abspath(os.path.dirname(__file__))
reg_sn = r'^([A-Z0-9]{4}-){3}[A-Z0-9]{4}'
# reg_txt = r'^.*?\.txt'
app.config['SQLALCHEMY_DATABASE_URI'] =\
'sqlite:///' + os.path.join(basedir, 'data/sqlite_db')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class SeriesNumberFormAdd(Form):
    hidden_tag = HiddenField()
    # sn_stock = StringField('序列号库存:', render_kw={'readonly': 'readonly'})
    # series_number = StringField('序列号：', [validators.DataRequired(), validators.Regexp(reg_sn)])
    category = SelectField('活动类别：', default='aiqiyi', choices=[('aiqiyi', '爱奇艺活动'), ('baidu', '百度网盘活动')])
    sn_input_date = DateField('序列号入库日期：', [validators.DataRequired()], render_kw={'readonly': 'readonly'})
    # sn_file = FileField('序列号文件：', validators=[FileRequired(), FileAllowed(['txt'], '无格式文本文件！')])
    filename = FileField('序列号文件：', [validators.DataRequired()])
    submit = SubmitField('提交序列号文件')

    # 用来验证序列号的唯一性
    # def validate_series_number(self, field):
    #     if db.session.query(SeriesNumber).filter_by(series_number=field.data).first():
    #         raise ValidationError('序列号已经存在')


class SeriesNumberFormUpdate(Form):
    hidden_tag = HiddenField()
    # category = SelectField('活动类别：', choices=[('aiqiyi', '爱奇艺'), ('baidu', '百度网盘')])
    category = StringField('活动名称：', render_kw={'readonly': 'readonly'})
    sn_stock = StringField('序列号库存:', render_kw={'readonly': 'readonly'})
    sn_output_date = DateField('领取序列号日期：', [validators.DataRequired()], render_kw={'readonly': 'readonly'})
    user_account = StringField('输入领取账户', [validators.DataRequired(), validators.Email(message='错误的账户格式！')])
    submit = SubmitField('领取序列号')


# 测试文件上传功能
class UploadFileForm(Form):
    hidden_tag = HiddenField()
    filename = FileField('选择上传文件：', [validators.DataRequired()])
    submit = SubmitField('提交文件')


# 定义数据库模型
class SeriesNumber(db.Model):
    __tablename__ = 'series_numbers'
    id = db.Column(db.Integer, primary_key=True)
    series_number = db.Column(db.Integer, unique=True)
    category = db.Column(db.String(20))
    sn_input_date = db.Column(db.DateTime)
    sn_output_date = db.Column(db.DateTime)
    user_account = db.Column(db.String(256))
    receipt_status = db.Column(db.Boolean)

    def __init__(self, series_number, category, sn_input_date, sn_output_date, user_account, receipt_status):
        self.series_number = series_number
        self.category = category
        self.sn_input_date = sn_input_date
        self.sn_output_date = sn_output_date
        self.user_account = user_account
        self.receipt_status = receipt_status

    def __repr__(self):
        return '<SeriesNumber {}>'.format(self.series_number)


db.create_all()


# 判断上传文件名称是否符合要求
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


# 通过用户账户查找是否在活动中有领取记录
def search_account(account, category):
    return db.session.query(SeriesNumber).filter_by(user_account=account, category=category).first()


# 查询序列号是否已经存在
def search_sn(sn):
    return db.session.query(SeriesNumber).filter_by(series_number=sn).first()


# 读取兑换码文件到一个list中
def openfile(file):
    with open(file, 'r') as f:
        sn_list = f.readlines()
    return sn_list


@app.route('/')
def hello_world():
    return render_template('index.html')


# 文件上传功能测试
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    form = UploadFileForm(request.form)
    if request.method == 'POST':
        file = request.files['filename']
        if file and allowed_file(file.filename):
            file.save(os.path.join(basedir, 'data/' + file.filename))
            flash('文件上传成功！')
            return redirect(url_for('upload'))
        else:
            flash('文件上传失败！这里只能上传无格式文本文件，并且文件名后缀是以.txt结尾的。')
    return render_template('sn_page.html', form=form)


# 序列号文件导入
@app.route('/snadd', methods=['GET', 'POST'])
def sn_add():
    form = SeriesNumberFormAdd(request.form)
    form.sn_input_date.data = datetime.datetime.today()
    # 统计导入的条数
    count = 0
    if form.category.data == 'aiqiyi':
        category_name = '爱奇艺活动'
    if form.category.data == 'baidu':
        category_name = '百度网盘活动'
    if request.method == 'POST':
        file = request.files['filename']
        if file and allowed_file(file.filename):
            file.save(os.path.join(basedir, 'data/' + file.filename))
            flash('文件上传成功！')
            # 增加文件内容格式校验
            sn_list = openfile(os.path.join(project_dir, 'data/' + file.filename))
            # 循环增加序列号导入数据库
            for i in range(len(sn_list)):
                if re.match(reg_sn, sn_list[i]):#判断是否有合法的序列号
                    if search_sn(re.match(reg_sn, sn_list[i]).group()):#判断是否有重复的序列号
                        flash('序列号：{0} 已经存在，不能重复导入！'.format(re.match(reg_sn, sn_list[i]).group()))
                        pass  #可以补充有重复序列号的处理逻辑
                    else:
                        series_number = re.match(reg_sn, sn_list[i]).group()
                        # session['category'] = form.category.data
                        category = form.category.data
                        sn_input_date = form.sn_input_date.data
                        sn_output_date = None
                        user_account = None
                        receipt_status = False
                        db.session.add(SeriesNumber(series_number=series_number,
                                                    category=category,
                                                    sn_input_date=sn_input_date,
                                                    sn_output_date=sn_output_date,
                                                    user_account=user_account,
                                                    receipt_status=receipt_status))
                        db.session.commit()
                        count += 1
            flash('本次共导入{0}序列号{1}条！'.format(category_name, count))
            return redirect(url_for('sn_add'))
        else:
            flash('文件上传失败！这里只能上传无格式文本文件，并且文件名是以.txt结尾的。')
    return render_template('sn_page.html', form=form)


# 领取活动序列号
@app.route('/<activity>', methods=['GET', 'POST'])
def sn_update(activity):
    form = SeriesNumberFormUpdate(request.form)
    if activity == 'aiqiyi':
        form.category.data = '爱奇艺活动'
    if activity == 'baidu':
        form.category.data = '百度网盘活动'
    form.sn_output_date.data = datetime.datetime.today()
    form.sn_stock.data = db.session.query(SeriesNumber).filter_by(category=activity, receipt_status=False).count()
    if request.method == 'POST' and form.validate():
        # 查询所有序列号
        # re_query = db.session.query(SeriesNumber.series_number).all()
        # 根据内容过滤查询
        # re_query = db.session.query(SeriesNumber.series_number).filter_by(category=form.category.data).all()
        user_info = search_account(form.user_account.data, activity)
        if user_info:
            flash('{0} 用户已经领取过{1}序列号: {2} ，不可重复领取！'.format(user_info.user_account, form.category.data,
                                                         user_info.series_number))
            return redirect(url_for('sn_update', activity=activity))

        # 根据活动类别，查询出第一个未被领取的序列号
        re_query = db.session.query(SeriesNumber).filter_by(category=activity,
                                                            receipt_status=False).first()
        # 被领取的序列号进行标记为已经领取，并更新数据库
        if re_query:
            flash('{0} 用户本次领取{1}序列号： {2} '.format(form.user_account.data, form.category.data, re_query.series_number))
            re_query.receipt_status = True
            re_query.sn_output_date = form.sn_output_date.data
            re_query.user_account = form.user_account.data
            db.session.commit()
            # 更新库存
            form.sn_stock.data = db.session.query(SeriesNumber).filter_by(category=activity, receipt_status=False).count()
        else:
            flash('已经没有序列号可以领取！')
        return redirect(url_for('sn_update', activity=activity))
    return render_template('sn_page.html', form=form)


if __name__ == '__main__':
    app.debug = True
    app.secret_key = '123456'
    app.run()
