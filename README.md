### S3 Manager is a Flask web application that allows users to manage their Amazon S3 buckets through a user-friendly interface. With S3 Manager, users can perform CRUD (Create, Read, Update, Delete) operations on their S3 buckets using Flask and Boto3.


> Live Demo-

**Experience S3 Manager live:**  https://s3-manager-7w8e.vercel.app/

**Note:** To connect to your S3 bucket, you'll need to provide your IAM user access key and secret access key. You can do this by visiting the connect page through the provided link and entering your credentials.

**Installation and Setup:**
If you prefer to run the application locally or customize it, follow these steps:


**Clone the Repository-**

git clone https://github.com/rudra273/S3_manager.git

**Set Up Virtual Environment-**

cd s3_manager

python -m venv venv

**Activate Virtual Environment-
On Windows:**

venv\Scripts\activate

**On macOS and Linux:**

source venv/bin/activate

**Install Dependencies-**

pip install -r requirements.txt

**Add the Following Lines to app.py-**

``` if __name__ == "__main__": ```

```        app.run(debug=True)  ``` 
    
**Run the Application-**

python app.py

_ The application should now be running locally. Visit http://localhost:5000 in your web browser to access it. _
