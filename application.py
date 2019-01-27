from flask_socketio import SocketIO, emit
from flask import Flask, render_template, url_for, jsonify, flash, request, redirect
from flask_wtf import FlaskForm
from flask_bootstrap import Bootstrap
from wtforms import StringField, SubmitField, TextAreaField, HiddenField, IntegerField
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from wtforms.validators import ValidationError, DataRequired, Length, Optional
from random import random, seed, randrange
import os
from dotenv import load_dotenv


basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'Xyasef-134vaserfO'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

socketio = SocketIO(app)
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Factory(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(32), unique=True)
	low_val = db.Column(db.Integer, default=1)
	high_val = db.Column(db.Integer, default=15)
	leaves = db.relationship('Leaf', cascade="all,delete", backref='creator', lazy='dynamic')

	def __repr__(self):
		return '<Factory {}>'.format(self.name)

	def generate(self, numLeaves):
		seed()
		for leaf in self.leaves.all():
			socketio.emit('delete_leaf', {'factoryId': self.id, 'leafId': leaf.id}, namespace='/test')
			db.session.delete(leaf)
		db.session.commit()
		for i in range(numLeaves):		
			number = randrange(self.low_val, self.high_val + 1)
			leaf = Leaf(factory_id=self.id, value=number)
			db.session.add(leaf)
		db.session.commit()
		leaves = self.leaves.all()
		leaves.reverse()
		for leaf in leaves:
			socketio.emit('newgeneration', {'factoryId': self.id, 'leafId': leaf.id, 'leafValue': leaf.value}, namespace='/test')

class Leaf(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	value = db.Column(db.Integer)
	factory_id = db.Column(db.Integer, db.ForeignKey(Factory.id))

	def __repr__(self):
		return '<Leaf {} Value {}>'.format(str(self.id), str(self.value))

class DeleteFactoryForm(FlaskForm):
	factoryId = HiddenField("Factory ID")
	delete = SubmitField('Delete')

class CreateFactoryForm(FlaskForm):
	name = StringField('Factory Name', validators=[DataRequired(), Length(min=0, max=32)])
	submit = SubmitField('Create')

	def validate_name(self, name):
		factory = Factory.query.filter_by(name=name.data).first()
		if factory is not None:
			raise ValidationError('Factory name already in use')

class ModifyFactoryForm(FlaskForm):
	name = StringField(validators=[Length(min=0, max=32)])
	lowVal = IntegerField(validators=[Optional()])
	highVal = IntegerField(validators=[Optional()])
	factoryId = HiddenField("Factory ID")
	modify = SubmitField('Modify')

	def validate_name(self, name):
		factory = Factory.query.filter_by(name=name.data).first()
		if factory is not None:
			raise ValidationError('Factory name already in use')

	def validate_lowVal(self, lowVal):
		factory = Factory.query.filter_by(id=self.factoryId.data).first()
		if self.highVal.data is None:
			if int(lowVal.data) >= factory.high_val:
				raise ValidationError("Low Value must be lower than High Value")
		else:
			if int(lowVal.data) >= self.highVal.data:
				raise ValidationError("Low Value must be lower than High Value")

	def validate_highVal(self, highVal):
		factory = Factory.query.filter_by(id=self.factoryId.data).first()
		if self.lowVal.data is None:
			if int(highVal.data) <= factory.low_val:
				raise ValidationError("High Value must be higher than Low Value")
		else:
			if int(highVal.data) <= self.lowVal.data:
				raise ValidationError("High Value must be higher than Low Value")

class GenerateLeavesForm(FlaskForm):
	factoryId = HiddenField("Factory ID")
	numLeaves = IntegerField("Number of Leaves", validators=[DataRequired()])
	generate = SubmitField('Generate')

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
	factories = Factory.query.all()
	delForms = {}
	genForms = {}
	for f in factories:
		delForms[f.id] = DeleteFactoryForm(factoryId=f.id)
		genForms[f.id] = GenerateLeavesForm(factoryId=f.id)
	if request.method == 'POST' and 'delete' in request.form:
		toDelete = Factory.query.filter_by(id=request.form['factoryId']).first()
		db.session.delete(toDelete)
		db.session.commit()
		socketio.emit('delete_factory', {'factoryId': request.form['factoryId']}, namespace='/test')
		flash('record deleted')
		return redirect(url_for('index'))
	if request.method == 'POST' and 'generate' in request.form:
		form = genForms[int(request.form['factoryId'])]
		if 1 <= int(form.numLeaves.data) <= 15:
			toGenerate = Factory.query.filter_by(id=request.form['factoryId']).first()
			toGenerate.generate(numLeaves=int(request.form['numLeaves']))
			flash("Leaves generated")
		else:
			flash("Num Leaves must in range 1:15")
		return redirect(url_for('index'))
	return render_template('index.html', factories=factories, 
		delForms=delForms, genForms=genForms)

@app.route('/create_factory', methods=['GET', 'POST'])
def create_factory():
	form = CreateFactoryForm()
	if form.validate_on_submit():
		factory = Factory(name=form.name.data)
		db.session.add(factory)
		db.session.commit()
		f = Factory.query.filter_by(name=form.name.data).first()
		createForm = CreateFactoryForm(factoryId=f.id)
		flash('factory created as ' + form.name.data)
		socketio.emit('create', {'factoryName': f.name, 'factoryId': f.id, 'csrf_token': createForm.csrf_token.data }, namespace='/test')
		return redirect(url_for('create_factory'))
	return render_template('create_factory.html', form=form)

@app.route('/modify/<factoryName>', methods=['GET', 'POST'])
def modify(factoryName):
	factory = Factory.query.filter_by(name=factoryName).first()
	if factory:
		form = ModifyFactoryForm(factoryId=factory.id)
		if form.validate_on_submit():
			socketioPayload = { 'factoryId': factory.id, 
								'factoryName': factory.name, 
								'factoryLow': factory.low_val, 
								'factoryHigh': factory.high_val }
			toModify = Factory.query.filter_by(id=request.form['factoryId']).first()
			if request.form['name'] != '':
				toModify.name = request.form['name']
				socketioPayload['factoryName'] = request.form['name']
			if request.form['lowVal']:
				toModify.low_val = request.form['lowVal']
				socketioPayload['factoryLow'] = request.form['lowVal']
			if request.form['highVal']:
				toModify.high_val = request.form['highVal']
				socketioPayload['factoryHigh'] = request.form['highVal']
			db.session.commit()
			socketio.emit('modify_factory', socketioPayload, namespace='/test')
			return redirect(url_for('modify', factoryName=toModify.name))
		return render_template('modify.html', factory=factory, form=form)
	return render_template('modify.html', fname=factoryName)

if __name__ == '__main__':
    socketio.run(app)