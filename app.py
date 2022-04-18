from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, join_room, leave_room, emit
from flask_session import Session
import pandas as pd
from flask import *

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'secret'
app.config['SESSION_TYPE'] = 'filesystem'

Session(app)

socketio = SocketIO(app, manage_session=False, cors_allowed_origins='*')


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/main', methods=['GET', 'POST'])
def main():  
    return render_template('main.html')

@app.route('/adduserpage', methods=['GET', 'POST'])
def adduserpage():
    return render_template('adduserpage.html')   

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    return render_template('admin.html')    


@app.route('/adduserdetails', methods=['GET', 'POST'])
def adduserdetails():
    username = request.form['username']
    password = request.form['password']
    emaniId = request.form['emailid']
    data = pd.read_csv(r'E:\Flask\Chat-App\templates\Login.csv',usecols=["UserName","EmailId","Password","UserType"])
    if username not in data['UserName'].values:
        flash("User not exists, please ask admin to create")  
        return render_template('adduserpage.html')
    data.set_index('UserName',inplace = True)
    Type = data.loc[username,'UserType'] 
    data.drop([username],inplace= True)
    dictionary_row = {"UserName":username,"EmailId":emaniId,"Password":password, "UserType":Type}
    data.reset_index(inplace = True)
    data = data.append(dictionary_row, ignore_index=True)
    data.set_index('UserName',inplace = True)
    data.to_csv(r'E:\Flask\Chat-App\templates\Login.csv')
    flash("Details updated successfuly")  
    return render_template('index.html')  

@app.route('/adminuser', methods=['GET', 'POST'])
def adminuser():
    username = request.form['username']
    password = request.form['password']
    data = pd.read_csv(r'E:\Flask\Chat-App\templates\Login.csv',usecols=["UserName","EmailId","Password","UserType"])
    #data.set_index('UserName', inplace=True)
    if username not in data['UserName'].values:
        flash("Please enter valid UserName ")  
        return render_template('admin.html')  
    #data = pd.read_csv(r'E:\Flask\Chat-App\templates\Login.csv')
    data.set_index('UserName', inplace=True)
    if not data.loc[username,'UserType'] == 'Admin':
        flash("Given User doesn't have Admin rights")  
        return render_template('admin.html')  
    if not data.loc[username,'Password'] == password:
            flash("Password incorrect")
            return redirect(url_for('admin'))    
    return render_template('userrights.html')


@app.route('/Userlist', methods=['GET', 'POST'])
def Userlist():
    data = pd.read_csv(r'E:\Flask\Chat-App\templates\Login.csv', usecols=['UserName','EmailId','UserType'])
    lt = data.values.tolist()
    return render_template('userlist.html', lt = lt)

@app.route('/AddUser', methods=['GET', 'POST'])
def AddUser():
    username = request.form['username']
    if not username:
        flash("Please Enter username")  
        return render_template('userrights.html')  
    if not username.strip():
        flash("Please Enter vaild username")  
        return render_template('userrights.html')      
    data = pd.read_csv(r'E:\Flask\Chat-App\templates\Login.csv',usecols=["UserName","EmailId","Password","UserType"])
    if username in data['UserName'].values:
        flash("User already exsits, Please enter valid UserName ")  
        return render_template('userrights.html') 
    dictionary_row = {"UserName":username,"EmailId":'Default@abc.com',"Password":'Default',"UserType":"User"}
    data = data.append(dictionary_row, ignore_index=True)
    data.set_index('UserName',inplace = True)
    data.to_csv(r'E:\Flask\Chat-App\templates\Login.csv')
    flash("User added successfuly")  
    return render_template('userrights.html')  

@app.route('/RemoveUser', methods=['GET', 'POST'])
def RemoveUser():
    username = request.form['username']
    if not username:
        flash("Please Enter username")  
        return render_template('userrights.html')  
    if not username.strip():
        flash("Please Enter vaild username")  
        return render_template('userrights.html')      
    
    data = pd.read_csv(r'E:\Flask\Chat-App\templates\Login.csv',usecols=["UserName","EmailId","Password","UserType"])
    if username not in data['UserName'].values:
        flash("User does not exsits, Please enter valid UserName ")  
        return render_template('userrights.html') 
    data.set_index('UserName',inplace = True)
    data.drop([username],inplace= True)
    data.to_csv(r'E:\Flask\Chat-App\templates\Login.csv')
    flash("User removed successfuly")  
    return render_template('userrights.html')  



@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if(request.method=='POST'):
        username = request.form['username']
        room = request.form['room']
        password = request.form['password']
        data = pd.read_csv(r'E:\Flask\Chat-App\templates\Login.csv',usecols=["UserName","EmailId","Password","UserType"])
        if username not in data['UserName'].values:
            flash("Please enter valid UserName ")  
            return render_template('main.html')
        
        data.set_index('UserName', inplace=True)
        if data.loc[username,'Password'] == password:
            pass
        else:
            flash("Password incorrect")
            return redirect(url_for('main'))
        #Store the data in session
        if password == 'Default':
            flash("Plesse reset your password as its a default one")
            return redirect(url_for('index'))
            
        session['username'] = username
        session['room'] = room
        return render_template('chat.html', session = session)
    else:
        if(session.get('username') is not None):
            return render_template('chat.html', session = session)
        else:
            return redirect(url_for('index'))

@socketio.on('join', namespace='/chat')
def join(message):
    room = session.get('room')
    join_room(room)
    emit('status', {'msg':  session.get('username') + ' has entered the room.'}, room=room)


@socketio.on('text', namespace='/chat')
def text(message):
    room = session.get('room')
    emit('message', {'msg': session.get('username') + ' : ' + message['msg']}, room=room)


@socketio.on('left', namespace='/chat')
def left(message):
    room = session.get('room')
    username = session.get('username')
    leave_room(room)
    session.clear()
    emit('status', {'msg': username + ' has left the room.'}, room=room)


if __name__ == '__main__':
    socketio.run(app)