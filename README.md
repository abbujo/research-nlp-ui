# research-nlp-ui
UI for Research NLP

Steps for creating this (FOR WINDOWS SETUP):

INSTALLING PREREQUISITES:
1. Install python in your system. Link (https://www.python.org/downloads/)
2. Install pip using this command: python get-pip.py . For more information about pip installation visit https://www.liquidweb.com/kb/install-pip-windows/
3. Install VS Code, please install using this link: https://code.visualstudio.com/download
4. Make sure you have git installed. If it is not install it using the link.https://git-scm.com/book/en/v2/Getting-Started-Installing-Git


CREATING MONGODB INSTANCE (Only if you want to access your own db. If you want to use my connection string itr will chose my database and you won't be able to see the data that is being populated.):
1. Create an account with MongoDB compass: https://www.mongodb.com/products/compass
2. Create an account with Python as major language.
3. Create a shared cluster. By clicking on build a database if you had used it before. If you are signing up for the first time, it will automatically take you there.
4. Wait for a while till the deployment of cluster takes place.
5. Click on the cluster deployment you just created. The default name would be Cluster0. If you haven't given it a name.
6. Go to collections tab.
7. Click on add my own data.
8. Give 'TestPyMongo' as the db name and 'test' as the collection name.
9. On the left hand side there would be a side panel. Click on 'Network Access' and allow access from anywhere.
10. Go back to 'Databases' from the left side panel. 
11. Next to your cluster name would be the connect option.
12. Please click on it and create a user for database access. Give a usename and password. Please remember the password it will be used later on.
16. Click on 'Choose a connection method'
17. Click on 'Connect using MongoDB Compass'.
18. If you do not have MongoDB atlas, Install it using the link provided there. Otherwise copy the connection string and save it somewhere.

RUNNING THE APPLICATION:
1. Open VS Code.
2. In VS Code Open Terminal using the shortcut key: Ctrl+` . For more info visit: https://code.visualstudio.com/docs/editor/integrated-terminal
3. clone this repo using command: git clone https://github.com/abbujo/research-nlp-ui.git
4. create a virtual environment using command: python -m venv venv/ . For more infor visit https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment
5. Activate the virtual env using: .\venv\Scripts\activate #  [Windows Users only]
6. Install all the required packages using command : pip install -r requirements.txt
7. Please udate the connection link in NLP.py, if you want to use your own MongoDB instance.
8. start the flask server using command: flask run
9. Open the link in your browser and follow the instructions.
