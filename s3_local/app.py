from flask import Flask, render_template, request, redirect, url_for, flash
from botocore.exceptions import ClientError
import boto3
import secrets
from prometheus_flask_exporter import PrometheusMetrics


app = Flask(__name__)
metrics = PrometheusMetrics(app) 

app.secret_key = secrets.token_hex(16)

#If there is any errors in app it will redirect to connect page.
@app.errorhandler(500)
@app.errorhandler(Exception)
def handle_error(error):
    print("An error occurred:", str(error))
    flash("An error occurred. Please connect again.")
    return redirect(url_for('connect')) 



#creates an S3 client object using the Boto3 library.
def create_s3_client(access_key, secret_key, region):
    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region
    )
    return session.client('s3') 

#Function for connecting to S3 bucket and rendering the connection form.
@app.route('/', methods=['GET', 'POST'])
@metrics.counter('connect_requests_total', 'Total number of connect requests')
def connect():
    if request.method == 'POST': 
        access_key = request.form['access_key']
        secret_key = request.form['secret_key'] 
        region = 'us-east-1'
        
        global s3_client
        s3_client = create_s3_client(access_key, secret_key, region) 

        buckets = s3_client.list_buckets()['Buckets']
        
        return redirect(url_for('index', buckets=buckets))  

    return render_template('base.html')  


#to disconect s3_clint
@app.route('/disconnect', methods=['GET', 'POST'])
def disconnect():
    global s3_client
    s3_client = None 
    return redirect(url_for('connect')) 


#passing s3_clint context in all the html page
@app.context_processor
def inject_s3_client():
    s3_client = None
    if 's3_client' in globals():
        s3_client = globals()['s3_client']
    return dict(s3_client=s3_client) 


#rendering index page with list of buckets
@app.route('/index') 
def index():

    data = s3_client.list_buckets() 
    buckets = data['Buckets']

    return render_template('index.html', buckets = buckets)  


@app.route('/create_bucket') 
def create_bucket():
    name = request.args.get("bucket_name")
    try:
        s3_client.head_bucket(Bucket=name)
        error_message = f"A bucket with the name '{name}' already exists in your account."
        flash(error_message, 'error')
        return redirect(url_for('index'))
    except ClientError as e: 
        if e.response['Error']['Code'] == '404':
            try:
                s3_client.create_bucket(Bucket=name)
                flash(f"Bucket '{name}' created successfully.", 'success') 
            except ClientError as ce:
                if ce.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                    error_message = f"A bucket with the name '{name}' already exists in your account."
                elif ce.response['Error']['Code'] == 'BucketAlreadyExists':
                    error_message = f"A bucket with the name '{name}' already exists. Bucket names must be globally unique."
                else:
                    error_message = f"An error occurred: {ce}"
                flash(error_message, 'error')
        elif e.response['Error']['Code'] == '403':
            error_message = f"A bucket with the name '{name}' already exists globally and is owned by another AWS account."
            flash(error_message, 'error')
    return redirect(url_for('index'))  


@app.route('/delete_bucket/<bucket_name>')
def delete_bucket(bucket_name):
    try:
        s3_client.delete_bucket(Bucket=bucket_name)
        flash(f"Bucket '{bucket_name}' deleted successfully.", 'success')
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'BucketNotEmpty':
            flash(f"Cannot delete bucket '{bucket_name}' because it is not empty.", 'error')
        else:
            flash(f"Failed to delete bucket '{bucket_name}': {error_code}", 'error')
    return redirect(url_for('index'))


#list files and folders of the bucket
@app.route("/list_bucket_objects/<bucket_name>") 
def list_bucket_objects(bucket_name):
    data = s3_client.list_buckets() 
    available_buckets = [bucket['Name'] for bucket in data['Buckets']]

    response = s3_client.list_objects_v2(Bucket=bucket_name) 
    if 'Contents' in response:
        object_keys = [obj['Key'] for obj in response['Contents']]
    else:
        object_keys = [] 
    
    return render_template('bucket.html',bucket_name=bucket_name, object_keys = object_keys, available_buckets=available_buckets)


#create a folder  in the current selected bucket
@app.route("/create_folder/<bucket_name>", methods=['POST']) 
def create_folder(bucket_name):
    folder_name = request.form['folder_name']

    if not folder_name.endswith('/'):
        folder_name += '/'
    
    s3_client.put_object(Bucket=bucket_name, Key=folder_name) 
    
    return redirect(url_for('list_bucket_objects', bucket_name=bucket_name)) 


#handeling bucket objets
@app.route("/handle_operation/<bucket_name>", methods=['POST', 'GET'])
def handle_operation(bucket_name):
    selected_objects = request.form.getlist('selected_objects')
    destination_bucket = request.form.get('destination_bucket')
    action = request.form.get('action')

    if action == 'delete':
        for object_key in selected_objects:
            s3_client.delete_object(Bucket=bucket_name, Key=object_key)

    if action == 'move' or action == 'copy':
        for object_key in selected_objects:
            copy_source = {'Bucket': bucket_name, 'Key': object_key}
            s3_client.copy_object(CopySource=copy_source, Bucket=destination_bucket, Key=object_key)
            if action == 'move':
                s3_client.delete_object(Bucket=bucket_name, Key=object_key)

    return redirect(url_for('list_bucket_objects', bucket_name=bucket_name))


#upload multiple files in bucket
@app.route('/upload_file/<bucket_name>', methods=['POST'])
def upload_file(bucket_name):
    try:
        files = request.files.getlist('file')
        for file in files:
            file_name = file.filename
            s3_client.upload_fileobj(file, bucket_name, file_name)
        return redirect(url_for('list_bucket_objects', bucket_name=bucket_name))
    except ClientError as e:
        return str(e)
    

###folder---------------------------------------------------------------------------


@app.route("/list_bucket_folder", methods=['GET'])
def list_bucket_folder():
    bucket_name = request.args.get('bucket_name')
    prefix = request.args.get('prefix')
    print('Calling list_bucket_folder with bucket_name:', bucket_name, 'and prefix:', prefix)
    
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        if 'Contents' in response:
            object_keys = [obj['Key'] for obj in response['Contents']]
        else:
            object_keys = []
        return render_template('folder.html', bucket_name=bucket_name, object_keys=object_keys, prefix=prefix)
    except ClientError as e:
        print('An error occurred:', e)
        return render_template('error.html', message='An error occurred while listing folder contents.')




if __name__ == "__main__":
    app.run(debug=True )  




