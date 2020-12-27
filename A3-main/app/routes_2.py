from boto3 import dynamodb
from flask_mail import Message
from flask import render_template, url_for, flash, redirect, session
from app.forms import LoginForm, RegistrationForm, RegistrationForm_owner, writeReviewsForm, ForgotPasswordForm, ReplyForm
from app import webapp, bcrypt, mail
from boto3.dynamodb.conditions import Key, Attr
import boto3, tempfile, io
from werkzeug.utils import secure_filename
from botocore.exceptions import NoCredentialsError

s3 = boto3.resource('s3')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

'''
Routes for login
'''

@webapp.route("/", methods=['GET', 'POST'])
@webapp.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.is_submitted():
        email = form.email.data
        password = form.password.data
        # admin login
        if email == 'ece1779@admin.com':
            if password == 'ece1779':
                session['admin'] = 'admin'
                return render_template('admin.html', title='Manager', type=session['admin'])
            else:
                flash(f"Incorrect admin password.", 'warning')
                return redirect(url_for('login'))

        # user  login
        if checkUserExist(form) == 'user':
            session['user'] = 'user' # for type check
            session['username'] = email # to get current login username
            return redirect(url_for('restaurants', type=session['user']))
        # owner login
        elif checkUserExist(form) == 'owner':
            session['owner'] = 'owner'
            # get restaurant name: name
            table = dynamodb.Table('restaurants')
            response = table.scan(FilterExpression=Attr("owner").eq(email))
            #response = table.get_item(
                #Key={
                    #'owner' : email
                #},
                #ProjectionExpression="#n",
                #ExpressionAttributeNames= {'#n':'name'}
            #)
            restaurant_name = response['Items'][0]['name']
            return redirect(url_for('reviews', restaurant_name=restaurant_name, type=session['owner']))
        else:
            flash(f"That username doesn't exist!",'warning')
            return redirect(url_for('register_user'))
    return render_template('login.html', title='Login', form=form)

'''
Routes for register
'''

@webapp.route("/register_user", methods=['GET', 'POST'])
def register_user():
    form = RegistrationForm()
    if form.is_submitted():
        if checkUserExist(form) != 'user':
            email = form.email.data
            password = form.password.data
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            table = dynamodb.Table('userinfo')
            response = table.put_item(
                Item={
                    'user': email,
                    'password': hashed_password,
                    'userType': 'user'
                }
            )
            flash(f'User Successfully created', 'success')
            return redirect(url_for('login'))
        else:
            flash(f'The user is already exist', 'warning')
            return render_template('register.html', title='Register', form=form)

    return render_template('register.html', title='User Register', form=form)


@webapp.route("/register_owner", methods=['GET', 'POST'])
def register_owner():
    form = RegistrationForm_owner()
    if form.is_submitted():
        if checkUserExist(form) != 'owner':
            email = form.email.data
            password = form.password.data
            restaurant_name = form.restaurant_name.data
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            UploadedFile = form.restaurant_pic.data
            #flash(UploadedFile)
            filename = secure_filename(UploadedFile.filename)

            table = dynamodb.Table('userinfo')
            response = table.put_item(
                Item={
                    'user': email,
                    'password': hashed_password,
                    'userType': 'owner'
                }
            )
            table = dynamodb.Table('restaurants')
            response = table.put_item(
                Item={
                    'name': restaurant_name,
                    'owner': email,
                    'restaurant_pic': filename
                }
            )
            uploadFile(form)
            flash(f'Owner Successfully created', 'success')
            return redirect(url_for('login'))
        else:
            flash(f'The owner is already exist','warning')
            return render_template('register.html', title='Register', form=form)
    return render_template('register_owner.html', title='Owner Register', form=form)

@webapp.route("/forgot_password", methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.is_submitted():
        if checkUserExist(form):
            email = form.email.data
            newpassword = 'ece1779a1'
            hashed_newpassword = bcrypt.generate_password_hash(newpassword).decode('utf-8')

            msg = Message('New Password', sender='ece1779a1group@gmail.com', recipients=[email])
            msg.body = "Your temporary password is ece1779a1, please login and change your password as soon as possible."
            mail.send(msg)

        else:
            flash(f"That email doesn't match our record", 'warning')
            return redirect(url_for('forgot_password'))
    return render_template('forgot_password.html', title='Forgot Password', form=form)

@webapp.route("/logout")
def logout():
    session.pop('admin',None)
    session.pop('user', None)
    session.pop('owner', None)
    session.pop('username', None)
    return redirect(url_for('login'))
'''
Routes for display restaurants
'''
@webapp.route("/restaurants/<type>", methods=['GET', 'POST'])
def restaurants(type):
    # get all the restaurants name and filename
    restaurants_name = []
    filename = []
    rating = []
    allRestaurant = getAllRestaurant()
    for i in range(0, len(allRestaurant)):
        restaurants_name.append(allRestaurant[i]['name'])
        filename.append(allRestaurant[i]['restaurant_pic'])
        rating.append(allRestaurant[i]['average_rating'])
    restaurants = list(zip(filename, restaurants_name, rating))
    return render_template('restaurants.html', restaurants=restaurants, type=type)

'''
Routes for listing all reviews
'''
@webapp.route("/reviews/<type>/<restaurant_name>", methods=['GET', 'POST'])
def reviews(restaurant_name, type):
    comments = getAllComment(restaurant_name)
    return render_template('reviews.html', comments=comments, restaurant_name=restaurant_name, type=type)

'''
Routes for writing reviews
'''
@webapp.route("/reviews/<type>/<restaurant_name>/writeReviews", methods=['GET', 'POST'])
def write_reviews(restaurant_name, type):
    form = writeReviewsForm()
    if form.is_submitted():
        comment_get = form.comment.data
        stars_get = form.stars.data
        #print(comment)
        #print(stars)
        table = dynamodb.Table('comment')
        #get username
        username = session['username']
        table.put_item(
            Item={
                'username': username,
                'comment': comment_get,
                'reply': '',
                'restaurant': restaurant_name,
                'stars': stars_get,
            }
        )
        updateStars(restaurant_name)
        return redirect(url_for('reviews', restaurant_name=restaurant_name, type = type))
    return render_template('writeReviews.html',form=form, restaurant_name=restaurant_name)

'''
Routs for reply 
'''
@webapp.route('/reviews/<type>/<restaurant_name>/<username>/reply', methods=['GET', 'POST'])
def reply(username, restaurant_name, type):
    form = ReplyForm()
    if form.is_submitted():
        reply = form.reply.data
        table = dynamodb.Table('comment')
        table.update_item(
            Key={
                'username': username,
            },
            UpdateExpression="set reply = :r",
            ExpressionAttributeValues={
                ':r': reply,
            }
        )
        return redirect(url_for('reviews', restaurant_name=restaurant_name, type=type))
    return render_template('reply.html', form=form, username=username, restaurant_name=restaurant_name)

@webapp.route("/delete_users", methods=['GET', 'POST'])
def delete_users():
    # delete the user table
    response = dynamodb.delete_table(
        TableName='userinfo'
    )
    flash(f'All the users have been successfully deleted!')
    return render_template('admin.html', title='Manager', type=session['admin'])

'''

helper functions

'''
#update restaurant stars after user send a comment
def updateStars(restaurant_name):
    table = dynamodb.Table('comment')
    response = table.scan(FilterExpression = Attr("restaurant").eq(restaurant_name))
    star = 0
    for i in range(0,len(response['Items'])):
        star = star+response['Items'][i]['stars']
    star = star/len(response['Items'])
    table_two= dynamodb.Table('restaurants')
    response_two = table_two.scan(FilterExpression=Attr("name").eq(restaurant_name))
    table_two.update_item(
    Key={
        'owner': response_two['Items'][0]['owner'],
	'name': response_two['Items'][0]['name']
    },
    UpdateExpression='SET average_rating = :val1',
    ExpressionAttributeValues={
        ':val1': star
    }
)

# Return usertype if email exist, or return false if no such email
def checkUserExist(form):
    # Get table from dynamodb
    table = dynamodb.Table('userinfo')

    # Get data from form
    email = form.email.data
    password = form.password.data

    response = table.get_item(
        Key={
            'user': email
        },
        ProjectionExpression="password,userType"
    )
    if 'Item' in response:
        if bcrypt.check_password_hash(response['Item']['password'], password):
            status = response['Item']['userType']
    else:
        status = False
    return status

# Return all the comments of the input restaurant
def getAllComment(restaurant_name):
    table = dynamodb.Table('comment')
    response = table.scan(
        FilterExpression = Attr("restaurant").eq(restaurant_name)
    )
    username = []
    stars = []
    comment = []
    reply = []
    for i in range(0, len(response['Items'])):
        username.append(response['Items'][i]['username'])
        stars.append(response['Items'][i]['stars'])
        comment.append(response['Items'][i]['comment'])
        reply.append(response['Items'][i]['reply'])
    AllComment = list(zip(username, stars, comment, reply))
    return AllComment

# Return all the restaurants
def getAllRestaurant():
    table = dynamodb.Table('restaurants')
    response = table.scan()
    return response['Items']

# upload restaurant picture to aws s3 bucket
def uploadFile(form):
    UploadedFile = form.restaurant_pic.data
    filename = secure_filename(UploadedFile.filename)
    if filename!="":
        upload_to_aws(UploadedFile,'restaurantpic1',filename)

def upload_to_aws(local_file, bucket, s3_file):
    s3 = boto3.client('s3')
    try:
        s3.upload_fileobj(local_file, bucket, s3_file,ExtraArgs={'ACL':'public-read'})
        print("Upload Successful")
        return True
    except FileNotFoundError:
        print("The file was not found")
        return False
    except NoCredentialsError:
        print("Credentials not available")
        return False
