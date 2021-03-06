# snapp

## 说明：仅为工作需要和个人学习使用

### 主要功能：
1. 提供活动序列号的领取
2. 提供通过.txt文件方式导入新序列号
3. 限制同一账户的多次领取
4. 导入序列号时判断是否有重复的序列号
5. 提供已领取序列号查询，可通过活动类型、用户账户进行查询（支持分页显示）
6. 通过webhooks向钉钉群推送信息

### 文件目录结构：

    .
    ├── app
    │   ├── __init__.py
    │   ├── main <主程序目录>
    │   │   ├── errors.py <错误页面>
    │   │   ├── forms.py <表单定义>
    │   │   ├── __init__.py
    │   │   ├── upload <保存上传文件目录>
    │   │   └── views.py <功能视图>
    │   ├── models.py <数据库模型>
    │   └── templates
    │       ├── index.html <首页模板>
    │       ├── _layout2.html <渲染flash消息模板，默认风格>
    │       ├── _layout.html <渲染flash消息模板，代码采用风格>
    │       ├── _navbar.html <页面导航栏模板>
    │       └── sn_page.html <代码领取、上传等页面统一模板>
    ├── config.py <配置文件>
    ├── data <保持数据库目录>
    │   └── data-dev.sqlite
    ├── migrations <数据库迁移脚本>
    ├── manage.py <运行管理>
    ├── README.md
    ├── requirements.txt <运行环境>
    │
    │------------此处是分割线---------
    ├── snapp.py <未模块化的主程序>
    └── templates
        ├── index.html
        ├── _layout.html
        ├── _navbar.html
        └── sn_page.html


### 准备工作：
1. 安装插件： 
````
pip install -r requirements.txt
````
2. 在data目录建立SQLite数据库和表，模型如下：
````
python3 manage.py db upgrade
通过以上命令在data目录下创建数据库和表，模型如下：
class SeriesNumber(db.Model):
    __tablename__ = 'series_numbers' #表单名称
    id = db.Column(db.Integer, primary_key=True)
    series_number = db.Column(db.Integer, unique=True) #序列号列
    category = db.Column(db.String(20)) #活动类别列
    sn_input_date = db.Column(db.DateTime) #序列号入库时间
    sn_output_date = db.Column(db.DateTime) #序列号领取时间
    user_account = db.Column(db.String(256)) #领取人账户
    receipt_status = db.Column(db.Boolean) #序列号状态，False:未领取，True:已领取
````
3. 运行程序：
````
python3 manage.py runserver --host 0.0.0.0
````
4. 数据库迁移：
````
python3 manage.py db init #初始化
python3 manage.py db migrate -m "initial migration" #建立数据库迁移脚本
python3 manage.py db upgrade #升级初始化数据库