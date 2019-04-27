import os
import sys
import click
from flask import Flask,render_template,url_for,redirect,request,flash,Response
from flask_wtf import FlaskForm
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager,UserMixin,login_user,login_required,logout_user,current_user
#from flask_principal import Principal,Permission,RoleNeed
from flask_ckeditor import CKEditorField
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, IntegerField, \
    TextAreaField, SubmitField, MultipleFileField
from wtforms.validators import DataRequired, Length, ValidationError, Email

WIN = sys.platform.startswith('win')
if WIN:  # 如果是 Windows 系统，使用三个斜线
    prefix = 'sqlite:///'
else:  # 否则使用四个斜线
    prefix = 'sqlite:////'

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(app.root_path, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控
# 在扩展类实例化前加载配置
db=SQLAlchemy(app)#初始化拓展了,传入app类
login_manager = LoginManager(app)#实例化拓展类LoginManager
#principals = Principal(app)#实例化拓展类Principal
#admin_permission = Permission(RoleNeed('admin'))



#此处开始写路由route
@app.route('/',methods=['GET','POST'])
def index():
    if request.method=='POST':
        if not current_user.is_authenticated:
            return redirect(url_for('index'))
        brand = request.form.get('brand')
        name = request.form.get('name')
        price = request.form.get('price')
        year = request.form.get('year')
        if not brand or not name or not price or not year or len(year)>4 or len(brand)>60 or len(name)>20 or len(price)>60:
            flash('不合法输入！')
            return redirect(url_for('index'))
        c_info = Car_Info(brand=brand,name=name,price=price,year=year)
        db.session.add(c_info)
        db.session.commit()
        flash('成功添加一条新信息')
        return redirect(url_for('index'))
    car_info=Car_Info.query.all()
    return render_template('index.html',car_info=car_info)


@app.route('/c_info/edit/<int:car_id>', methods=['GET', 'POST']) #编辑车辆信息
#@admin_permission.require()
def edit(car_id):
    c_info = Car_Info.query.get_or_404(car_id)
    if request.method == 'POST':  # 处理编辑表单的提交请求
        brand = request.form['brand']
        name = request.form['name']
        price = request.form['price']
        year = request.form['year']
        if not brand or not name or not price or not year or len(year)>4 or len(brand)>60 or len(name)>20 or len(price)>60:
            flash('无效的输入.')
            return redirect(url_for('edit', car_id=car_id))  # 重定向回对应的编辑页面
        c_info.brand = brand  # 更新标题
        c_info.year = year  # 更新年份
        db.session.commit()  # 提交数据库会话
        flash('Item updated.')
        return redirect(url_for('index'))  # 重定向回主页
    return render_template('edit.html', c_info=c_info)  # 传入被编辑的电影记录


@app.route('/login',methods=['GET','POST'])
def sign_in():
    if request.method=='POST':
        uaccount=request.form['account']
        password = request.form['password']

        if not uaccount or not password:
            flash('不合法输入：用户名和密码中有一项为空！')
            return redirect(url_for('sign_in'))
        user = User.query.first()#验证用户名和密码是否正确
        if uaccount == user.account and password == user.password:
            login_user(user)
            flash('登陆成功！')
            return redirect(url_for('index'))
        flash('用户名或密码错误！')#验证失败返回错误提示
        return redirect(url_for('sign_in'))
    return render_template('login.html')


@app.route('/logout')
@login_required#用于视图保护
def logout():
    logout_user()   #登出用户
    flash('登出成功！')
    return redirect(url_for('index'))


@app.route('/signup',methods=['GET','POST'])
def sign_up():
    uaccount = request.form.get('acc-signup')
    password = request.form.get('psw-signup')
    username = request.form.get('name-signup')
    identity = request.form.get('ide-signup')
    exuser = User.query.first()
    if uaccount == exuser.account:
        flash('该用户名已被注册！')
        return redirect(url_for('index'))
    u_info = User(account=uaccount,password=password,username=username,identity=identity)
    db.session.add(u_info)
    db.session.commit()
    flash('注册成功！')
    return render_template('register.html')


@app.route('/console')
def console():
    render_template('console.html')


@app.route('/orders',methods=['GET','POST'])
@login_required
def user_order():
    if request.method == 'POST':
        if not current_user.is_authenticated:
            return redirect(url_for('sign_in'))
    return render_template('user_orders.html')


@app.route('/c_info/delete/<int:car_id>', methods=['POST'])  # 限定只接受 POST 请求
#@admin_permission.require()
#@login_required #登陆保护
def delete(car_id):
    c_info = Car_Info.query.get_or_404(car_id)  # 获取电影记录
    db.session.delete(c_info)  # 删除对应的记录
    db.session.commit()  # 提交数据库会话
    flash('Item deleted.')
    return redirect(url_for('index'))  # 重定向回主页




@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'),404


@app.errorhandler(401)
def unauthorized(e):
    return render_template('login.html'),401

#此处开始写命令@command
@app.cli.command()  # 注册为命令
@click.option('--drop', is_flag=True, help='Create after drop.')  # 设置选项
def initdb(drop):
    """Initialize the database."""
    if drop:  # 判断是否输入了选项
        db.drop_all()
    db.create_all()
    click.echo('Initialized database.')  # 输出提示信息


@app.cli.command()
def forge():
    """Generate fake data."""
    db.create_all()
    # 全局的两个变量移动到这个函数内
    car_info = [
        {'brand': 'Toyota', 'name': 'collora','price':140.1,'year':'2000'},
        {'brand': 'Honda', 'name': 'civic','price':122.1,'year':'2000'},
        {'brand': 'BMW', 'name': 'M3','price':112.1,'year':'2000'},
        {'brand': 'Audi', 'name': 'TT','price':772.1,'year':'2000'},
        {'brand': 'Benz', 'name': 'C200','price':332.1,'year':'2000'},
        {'brand': 'VW', 'name': 'GOLF','price':92.1,'year':'2000'},
        {'brand': 'SUBARU', 'name': 'BRZ','price':212.1,'year':'2000'},
        {'brand': 'Ford', 'name': 'Focus','price':172.1,'year':'2000'},
        {'brand': 'MINI', 'name': 'Cooper','price':381.1,'year':'2000'},
        {'brand': 'Ferrari', 'name': 'F430','price':2392.1,'year':'2000'}
    ]
    for m in car_info:
        c_info = Car_Info(brand=m['brand'], name=m['name'],price=m['price'],year=m['year'])
        db.session.add(c_info)
    db.session.commit()
    click.echo('Done.')


@app.cli.command()
@click.option('--account', prompt=True, help='The account used to login.')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='The password used to login.')
def admin(account,password):
    """创建管理员."""
    db.create_all()
    user = User.query.first()
    if user is not None:
        click.echo('Updating user...')
        user.account = account
        user.set_password(password)  # 设置密码
    else:
        click.echo('Creating user...')
        user = User(account=account,username='Admin',identity='19970426')
        user.set_password(password)  # 设置密码
        db.session.add(user)
    db.session.commit()  # 提交数据库会话
    click.echo('Done.')


@login_manager.user_loader
def load_user(user_id):
    user=User.query.get(int(user_id))   #用ID作为User模型的主键查询对应的用户
    return user

#此处开始写类class
class User(db.Model, UserMixin):  # 表名将会是 user（自动生成，小写处理），“一”的角色，客户/用户
    #__tablename__='user'
    id = db.Column(db.Integer, primary_key=True)  # 主键
    account = db.Column(db.String(20),unique=True)   #账号,不可重复
    username = db.Column(db.String(20))  # 客户姓名
    password = db.Column(db.String(20))   #密码
    identity = db.Column(db.String(20),unique=True)  #身份证号




class Car_Info(db.Model):  # 表名将会是 movie ， “多”的角色，车辆
    __tablename__='car_info'
    id = db.Column(db.Integer, primary_key=True)  # 主键
    brand = db.Column(db.String(60))  # 汽车品牌
    name = db.Column(db.String(20))  #汽车名
    price = db.Column(db.Float)  #汽车租价
    year = db.Column(db.String(4))  # 出厂年份
    orders = db.relationship('Orders',uselist=False)


class Orders(db.Model):#表名将会是orders , “多”的角色,订单
    __tablename__='orders'
    id = db.Column(db.Integer,primary_key=True)   #主键
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'))#外键，连接用户信息表
    car_id = db.Column(db.Integer,db.ForeignKey('car_info.id'))#外键，连接车辆信息表
    car_info = db.relationship('Car_Info')#与车辆信息建立一对一关系，一个订单对应一个车辆信息
    user = db.relationship('User')#与用户信息建立一对多关系，一个用户可以对应多个订单信息



class Admin(db.Model,UserMixin):#表名将会是admin，独立角色,管理员
    __tablename__='admin'
    id = db.Column(db.String(20),primary_key=True)  #主键
    name = db.Column(db.String(20))
    username = db.Column(db.String(20))
    password_hash = db.Column(db.String(128))
    def set_password(self,password):
        self.password_hash = generate_password_hash(password)
    def validate_password(self,password):
        return check_password_hash(self.password_hash,password)

if __name__ == '__main__':
    app.run()
