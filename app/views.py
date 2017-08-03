from app import app,SQLAlchemy,db
from app.db_handler import User,UserCode
from flask import Flask, render_template,request,json,session,redirect,jsonify,send_from_directory
from werkzeug import generate_password_hash, check_password_hash
import os

@app.route('/signUp',methods=['POST'])
def signUp():
	"""Sign Up for Virtual Lab

	POST: Submit sign-up parameters. The following must be present:
	 inputName : The name of your account. does not need to be unique
	 inputEmail : e-mail ID used for login . must be unique.
	Returns HTTP 404 when data does not exist.
	"""
	# read the posted values from the UI
	_name = request.form['inputName']
	_email = request.form['inputEmail']
	_password = request.form['inputPassword']

	# validate the received values
	if _name and _email and _password:
		_hashed_password = generate_password_hash(_password)
		newUser = User(_email, _name,_hashed_password)
		try:
			db.session.add(newUser)
			db.session.commit()
			return json.dumps({'status':True,'message':'User %s created successfully. e-mail:%s !'%(_name,_email)})
		except Exception as exc:
			reason = str(exc)
			return json.dumps({'status':False,'message':str(reason)})



@app.route('/validateLogin',methods=['POST'])
def validateLogin():
	_username = request.form['inputEmail']
	_password = request.form['inputPassword']
	user = User.query.filter_by(email=_username).first() #retrieve the row based on e-mail
	if user is not None:
		if check_password_hash(user.pwHash,_password):
			session['user'] = [user.username,user.email]
			return json.dumps({'status':True})
		else:
			return json.dumps({'status':False,'message':'Wrong Email address or Password. hash mismatch'})
	else:
		return json.dumps({'status':False,'message':'Username not specified'})

@app.route('/logout',methods=['POST'])
def logout():
	try:
		print ('logging out',session.pop('user',None))
		return json.dumps({'status':True,'message':'Logged out'})
	except Exception as exc:
		reason = str(exc)
		return json.dumps({'status':False,'message':str(reason)})


@app.route('/getUserName')
def getUserName():
	if user is not None:
		return json.dumps({'username':session['user'][0]})
	else:
		return json.dumps({'error':'Not Logged In'})



@app.route('/addScript',methods=['POST'])
def addScript():
	try:
		if session.get('user'):
			_user = session.get('user')[1]
			_title = request.form['inputTitle']
			_description = request.form['inputDescription']

			newSnippet = UserCode(_user, _title,_description)
			try:
				db.session.add(newSnippet)
				db.session.commit()
				return json.dumps({'status':True})
			except Exception as exc:
				return json.dumps({'status':False,'message':str(exc)})

		else:
			return json.dumps({'status':False,'message':'Unauthorized access'})
	except Exception as e:
		return json.dumps({'status':False,'message':str(e)})


@app.route('/getScriptList')
def getCode():
	try:
		if session.get('user'):
			_user = session.get('user')[1]
			scripts = UserCode.query.filter_by(user=_user)
			scripts_dict = []
			for script in scripts:
				single_script = {
						'Id': script.id,
						'Filename': script.title,
						#'Code': script.code, #Can be enbled if the user demands all scripts and content.
						'Date': script.pub_date}
				scripts_dict.append(single_script)
			return json.dumps(scripts_dict)
		else:
			return json.dumps([])
	except Exception as e:
		print (str(e))
		return json.dumps([])



@app.route('/getScriptById',methods=['POST'])
def getCodeById():
	if session.get('user'):
		_id = request.form['id']
		_user = session.get('user')[1]
		try:
			script = UserCode.query.filter_by(user=_user,id=_id).first()
			print('sending :',script.title)
			return json.dumps({'status':True,'Id':script.id,'Code':script.code,'Filename':script.title,'Date':script.pub_date,'message':'got script %s'%script.title})
		except Exception as exc:
			return json.dumps({'data':None,'status':False,'message':str(exc)})
	else:
		return json.dumps({'data':None,'status':False,'message':'Unauthorized access'})




@app.route('/updateCode', methods=['POST'])
def updateCode():
  if session.get('user'):
    _user = session.get('user')[1]
    _title = request.form['inputTitle']
    _description = request.form['inputDescription']
    _code_id = request.form['codeId']
    try:
      script = UserCode.query.filter_by(user=_user,id=_code_id).first()
      script.title = _title
      script.code = _description
      db.session.commit()
      return json.dumps({'status':True,'message':'Updated!'})
    except Exception as exc:
      return json.dumps({'status':False,'message':str(exc)})
  else:
    return json.dumps({'status':False,'message':'Unauthorized access'})




@app.route('/deleteScript',methods=['POST'])
def deleteCode():
  if session.get('user'):
    _user = session.get('user')[1]
    _id = request.form['scriptId']
    try:
      UserCode.query.filter_by(user=_user,id=_id).delete()
      print ('deleted',_id)
      db.session.commit()
      return json.dumps({'status':True,'message':'Deleted!'})
    except Exception as exc:
      print(exc)
      return json.dumps({'status':False,'message':str(exc)})
  else:
    return json.dumps({'status':False,'message':'Unauthorized access'})


"""
#Pending migration to postgres



import inspect,random
import numpy as np
# A dummy class that will pretend to be a minimal PSLab . we shall use this for testing purposes.
class dummy(object):
	def __init__(self):
		self.x=np.linspace(0,8*np.pi,200)
		self.r = random.random()
	def capture1(self,chan,samples,tg):
		'''
		Example doc for capture command. returns a sine wave
		'''
		self.x=np.linspace(0,8*np.pi,samples)
		return self.x,np.sin(self.x+np.pi*random.random()/10)
	def capture2(self,samples,tg):
		self.x=np.linspace(0,8*np.pi,samples)
		return self.x,np.sin(self.x+np.pi*random.random()/10),np.sin(self.x+np.pi*random.random()/10)

	def get_voltage(self,chan):
		'''
		bloo blahs
		a454
		*&^ "23"
		'''
		return self.r+random.random()
	def set_pv1(self,val):
		return val+self.r


try:
	from PSL import sciencelab
	I = sciencelab.connect(verbose=True)
	I.set_sine2(1000)
except Exception as e:
	print ('using dummy class',str(e))
	I = dummy()

# Use the inspect module to prepare a list of methods available in the class. This is quite flexible, and in theory this framework should easily adapt to serve any hardware with a python communication library
functionList = {}
for a in dir(I):
	attr = getattr(I, a)
	if inspect.ismethod(attr) and a!='__init__':
		functionList[a] = attr



"""
