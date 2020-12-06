from flask import Flask, render_template,request,session,redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_mail import Mail
from werkzeug.utils import secure_filename
import os
import json


with open("config.json","r") as c:
    params = json.load(c)["params"]

app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config["UPLOAD_FOLDER"] = params['upload_loc']
app.config.update(
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_PORT = "465",
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail_user'],
    MAIL_PASSWORD = params['gmail_password']
    )
mail = Mail(app)
if(params["local_server"]):
    app.config['SQLALCHEMY_DATABASE_URI'] = params["local_uri"]
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params["prod_uri"]
db = SQLAlchemy(app)

class Messages(db.Model):
    '''sno Name Email number msg Date'''
    sno = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(80),  nullable=False)
    Email = db.Column(db.String(120),  nullable=False)
    number = db.Column(db.String(12),  nullable=False)
    msg = db.Column(db.String(120),  nullable=False)

class Posts(db.Model):
    '''sno Name Email number msg Date'''
    sno = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(80),  nullable=False)
    Slug = db.Column(db.String(20),  nullable=False)
    Content = db.Column(db.String(120),  nullable=False)
    Name = db.Column(db.String(120),  nullable=False) 
    Date = db.Column(db.String(120),  nullable=True)
    img_file = db.Column(db.String(120),  nullable=False)

@app.route('/')
def home_page():
    posts = Posts.query.filter_by().all()[0:params['no_of_posts']]
    return render_template('index.html',params = params,posts = posts)

'''about blog contact marketing'''

@app.route('/about')
def about_page():
    return render_template('about.html',params = params)

@app.route('/contact',methods = ['GET','POST'])
def contact_page():
    if(request.method == 'POST'):
        '''add entry to database'''
        name =request.form.get('name')
        email =request.form.get('email')
        number =request.form.get('number')
        msg =request.form.get('msg')

        entry = Messages(Name = name, Email = email,number = number, msg = msg)
        db.session.add(entry)
        db.session.commit()

        mail.send_message("New message from "+name,
        sender=email,
        recipients=[params['gmail_user']],
        body=msg+"\n"+"Phone Number : "+number+"\nEmail : "+email)
    return render_template('contact.html',params = params)

@app.route('/post/<string:post_slug>',methods = ["GET"])
def about_post(post_slug):
    post  = Posts.query.filter_by(Slug = post_slug).first()
    posts = Posts.query.filter_by().all()
    return render_template('post.html',params = params,post = post,posts = posts)

@app.route('/uploader', methods = ['GET','POST'])
def upload():
    if request.method == "POST":
        f = request.files['file_1']
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
        return "Uploaded Successfully"
    return render_template('about.html',params = params)

@app.route('/login',methods = ["GET","POST"])
def login_page():
    if('user' in session and session['user'] == params['admin_username'] ):
        posts = Posts.query.all()
        return render_template('dashboard.html',params = params,posts = posts)

    if(request.method=="POST"):
        username = request.form.get('uname')
        password = request.form.get('pass')
        if(username == params['admin_username'] and password == params['admin_password']):
            session['user'] = username
            posts = Posts.query.all()
        return render_template('dashboard.html',params = params,posts = posts)
    return render_template('login.html',params = params)
    
@app.route('/edit/<string:sno>',methods = ['GET','POST'])
def edit_post(sno):
    if ('user' in session and session['user'] == params['admin_username']):
        if request.method == 'POST':
            Title = request.form.get('Title')
            Content = request.form.get('Content')
            Name = request.form.get('Name')
            slug = request.form.get('Slug')
            Image = request.form.get('Image')
            Date = datetime.now()

            if sno == '0':
                post = Posts(Title = Title,Content = Content, Name =  Name,Slug = slug,img_file = Image,Date = Date)
                db.session.add(post)
                db.session.commit()
        
            else:
                post = Posts.query.filter_by(sno =sno).first()
                post.Title = Title
                post.Content = Content
                post.Name  = Name
                post.slug = slug
                post.img_file = Image
                Date = datetime.now()
                db.session.commit()
                return redirect('/edit/'+sno)    
        post = Posts.query.filter_by(sno = sno).first()
        return render_template('edit.html',params = params,post =post,sno = sno)
            

@app.route('/delete/<string:sno>',methods = ['GET','POST'])
def delete_post(sno):
    if('user' in session and session['user'] == params['admin_username'] ):
        post = Posts.query.filter_by(sno = sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/login')

@app.route('/logout')
def logout_page():
    session.pop('user')
    return redirect('/login')

app.run(debug=True)