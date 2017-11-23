import os
import re
import datetime
from flask import render_template, request, session, redirect, url_for, current_app, flash
from .. import db
from ..models import SeriesNumber
from . import main
from . forms import SeriesNumberFormAdd, SeriesNumberFormUpdate, UploadFileForm, SearchInfo
from .webhooks import SNSendDing

# ALLOWED_EXTENSIONS = set(['txt'])
basedir = os.path.abspath(os.path.dirname(__file__))
reg_sn = r'([A-Z0-9]{4}-){3}[A-Z0-9]{4}'


# 判断上传文件名称是否符合要求
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in current_app.config['ALLOWED_EXTENSIONS']


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


@main.route('/')
def hello_world():
    return render_template('index.html')


# 文件上传功能测试
@main.route('/upload', methods=['GET', 'POST'])
def upload():
    form = UploadFileForm(request.form)
    if request.method == 'POST':
        file = request.files['filename']
        if file and allowed_file(file.filename):
            file.save(os.path.join(basedir, 'upload/' + file.filename))
            flash('文件上传成功！', 'success')
            return redirect(url_for('.upload'))
        else:
            flash('文件上传失败！这里只能上传无格式文本文件，并且文件名后缀是以.txt结尾的。', 'warning')
    return render_template('sn_page.html', form=form)


# 序列号文件导入
@main.route('/snadd', methods=['GET', 'POST'])
def sn_add():
    form = SeriesNumberFormAdd(request.form)
    form.sn_input_date.data = datetime.datetime.today()
    # 统计导入的条数
    count = 0
    if form.category.data == 'aiqiyi':
        category_name = '爱奇艺活动'
    if form.category.data == 'baidu':
        category_name = '百度网盘活动'
    if form.category.data == 'vip-8':
        category_name = 'VIP-8元红包'
    if request.method == 'POST':
        file = request.files['filename']
        if file and allowed_file(file.filename):
            file.save(os.path.join(basedir, 'upload/' + file.filename))
            flash('文件上传成功！', 'success')
            # 增加文件内容格式校验
            sn_list = openfile(os.path.join(basedir, 'upload/' + file.filename))
            # 循环增加序列号导入数据库
            for i in range(len(sn_list)):
                # if re.match(reg_sn, sn_list[i]):#判断是否有合法的序列号
                if search_sn(sn_list[i]):#判断是否有重复的序列号
                    flash('序列号：{0} 已经存在，不能重复导入！'.format(re.match(reg_sn, sn_list[i]).group()), 'warning')
                    pass  #可以补充有重复序列号的处理逻辑
                else:
                    series_number = sn_list[i]
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
            flash('本次共导入{0}序列号{1}条！'.format(category_name, count), 'success')
            return redirect(url_for('.sn_add'))
        else:
            flash('文件上传失败！这里只能上传无格式文本文件，且文件名后缀是以.txt结尾。', 'warning')
    return render_template('sn_page.html', form=form)


# 领取活动序列号
@main.route('/<activity>', methods=['GET', 'POST'])
def sn_update(activity):
    form = SeriesNumberFormUpdate(request.form)
    if activity == 'aiqiyi':
        form.category.data = '爱奇艺活动'
    if activity == 'baidu':
        form.category.data = '百度网盘活动'
    if activity == 'vip-8':
        form.category.data = 'VIP-8元红包'
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
                                                         user_info.series_number), 'danger')
            return redirect(url_for('.sn_update', activity=activity))

        # 根据活动类别，查询出第一个未被领取的序列号
        re_query = db.session.query(SeriesNumber).filter_by(category=activity,
                                                            receipt_status=False).first()
        # 被领取的序列号进行标记为已经领取，并更新数据库
        if re_query:
            flash('{0} 用户本次领取{1}序列号： {2} '.format(form.user_account.data, form.category.data, re_query.series_number), 'success')
            re_query.receipt_status = True
            re_query.sn_output_date = form.sn_output_date.data
            re_query.user_account = form.user_account.data
            db.session.commit()
            # 更新库存
            form.sn_stock.data = db.session.query(SeriesNumber).filter_by(category=activity, receipt_status=False).count()
            # 向钉钉客服群发送消息推送
            SNSendDing(form.user_account.data, form.category.data, re_query.series_number)
        else:
            flash('已经没有序列号可以领取！', 'warning')
        return redirect(url_for('.sn_update', activity=activity))
    return render_template('sn_page.html', form=form)


# 领取记录查询
@main.route('/info', methods=['GET', 'POST'])
def info():
    form = SearchInfo(request.form)
    page = request.args.get('page', 1, type=int)
    if request.method == 'POST':
        session['active'] = form.category.data
        session['account'] = form.user_account.data
        return redirect(url_for('.info'))
    form.category.data = session.get('active')
    form.user_account.data = session.get('account')
    if form.user_account.data == '':
        count = db.session.query(SeriesNumber).filter_by(category=form.category.data, receipt_status=True).count()
        pagination = db.session.query(SeriesNumber).filter_by(category=form.category.data, receipt_status=True).paginate(page, 10, False)
    else:
        count = db.session.query(SeriesNumber).filter_by(category=form.category.data, user_account=form.user_account.data, receipt_status=True).count()
        pagination = db.session.query(SeriesNumber).filter_by(category=form.category.data, user_account=form.user_account.data,
                                                              receipt_status=True).paginate(page, 10, False)
    re_query = pagination.items
    if session.get('active') == 'baidu':
        category = '百度网盘活动'
    elif session.get('active') == 'aiqiyi':
        category = '爱奇艺活动'
    elif session.get('active') == 'VIP-8':
        category = 'VIP-8元红包'
    else:
        category = ' '
    return render_template('info.html', form=form, count=count, category=category, re_query=re_query,
                               pagination=pagination)


# 仅做测试使用
@main.route('/test', methods=['GET', 'POST'])
def test():
    form = SearchInfo(request.form)
    page = request.args.get('page', 1, type=int)
    if request.method == 'POST':
        session['active'] = form.category.data
        session['account'] = form.user_account.data
        return redirect(url_for('.test'))
    form.category.data = session.get('active')
    form.user_account.data = session.get('account')
    if form.user_account.data == '':
        count = db.session.query(SeriesNumber).filter_by(category=form.category.data, receipt_status=True).count()
        pagination = db.session.query(SeriesNumber).filter_by(category=form.category.data, receipt_status=True).paginate(page, 10, False)
    else:
        count = db.session.query(SeriesNumber).filter_by(category=form.category.data, user_account=form.user_account.data, receipt_status=True).count()
        pagination = db.session.query(SeriesNumber).filter_by(category=form.category.data, user_account=form.user_account.data,
                                                              receipt_status=True).paginate(page, 10, False)
    re_query = pagination.items
    if session.get('active') == 'baidu':
        category = '百度网盘活动'
    elif session.get('active') == 'aiqiyi':
        category = '爱奇艺活动'
    else:
        category = ' '
    return render_template('test.html', form=form, count=count, category=category, re_query=re_query,
                               pagination=pagination)


