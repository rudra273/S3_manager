# AKIA5FTY7PAX23A7D7NM
# GMkKisNu0mEd41FVb6so8ZnMM6Mm/ulPfqSJ8+Uv


from flask import Flask, render_template, request, redirect, url_for
from botocore.exceptions import ClientError
app = Flask(__name__)

import boto3

r2session= boto3.Session(region_name='us-east-1')
s3_client = r2session.client('s3') 


@app.route('/')
def connect():
    # if request.method ==  'POST':
    #     access_key = request.form['access_key']
    #     secret_key = request.form['secret_key']
    #     region = request.form['region']
    #     output_format = request.form['output_format'] 

    #     session = boto3.Session(
    #         aws_access_key_id=access_key,
    #         aws_secret_access_key=secret_key,
    #         region_name=region
    #     )
    #     s3 = session.client('s3')
    #     buckets = s3.list_buckets()['Buckets']
    #     return redirect(url_for('index', buckets = buckets)) 

    return render_template('base.html') 



@app.route('/index')
def index():
    data = s3_client.list_buckets()
    buckets = data['Buckets']

    return render_template('index.html', buckets = buckets)  


@app.route('/create_bucket') 
def create_bucket():
    name =  request.args.get("bucket_name")
    res = s3_client.create_bucket(Bucket = name )
    print(res)
    return redirect(url_for('index'))  


@app.route('/delete_bucket/<bucket_name>')
def delete_bucket(bucket_name):
    s3_client.delete_bucket(Bucket=bucket_name)
    return redirect(url_for('index')) 


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


@app.route("/create_folder/<bucket_name>", methods=['POST']) 
def create_folder(bucket_name):
    folder_name = request.form['folder_name']

    if not folder_name.endswith('/'):
        folder_name += '/'
    
    s3_client.put_object(Bucket=bucket_name, Key=folder_name)
    
    return redirect(url_for('list_bucket_objects', bucket_name=bucket_name)) 


@app.route("/handle_operation/<bucket_name>", methods=['POST'])
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



if __name__ == "__main__":
    app.run(debug=True, port=8080)  

