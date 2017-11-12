import os
import re
from flask import request, redirect, flash
import datetime
from flask import Flask, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from wtforms import Form, validators, StringField, HiddenField, SubmitField, DateField, SelectField, ValidationError, FileField
from flask_bootstrap import Bootstrap


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
