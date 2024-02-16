import json
import os
import subprocess
from flask import Flask,render_template,redirect,request, session, url_for
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__,template_folder= 'templates' , static_folder='static')
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///examdb.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable modification tracking

db = SQLAlchemy(app)


app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'


class CreateUsers(db.Model):
    sno = db.Column(db.Integer , primary_key = True )
    name = db.Column(db.String(30) , nullable=False)
    emailid = db.Column(db.String(50) , nullable=False)
    password = db.Column(db.String(30) , nullable = False)
    score = db.Column(db.Integer , nullable = False )
    exams = db.Column(db.Integer , nullable=False)

    def __repr__(self):
        return f"{self.sno} -- {self.name}"

# create admin table
class CreateAdmin(db.Model):
    sno = db.Column(db.Integer , primary_key = True )
    name = db.Column(db.String(30) , nullable=False)
    emailid = db.Column(db.String(50) , nullable=False)
    password = db.Column(db.String(30) , nullable = False)

    def __repr__(self):
        return f"{self.sno} -- {self.name}"
    
#create questions table
class CreateQuestions(db.Model):
    sno = db.Column(db.Integer , primary_key=True)
    question = db.Column(db.String(300) , nullable=False)
    stestcase = db.Column(db.String(300) , nullable=False)
    htestcase = db.Column(db.String(500) , nullable=False)
    section = db.Column(db.String(100) , nullable = False)

    def __repr__(self):
        return f"{self.sno} -- {self.question}"
    
#create scores table
class CreateScores(db.Model):
    sno = db.Column(db.Integer , primary_key=True)
    userid = db.Column(db.Integer , nullable = False )
    # questionid = db.Column(db.Integer , nullable = False)
    section = db.Column(db.String(100) , nullable = False)
    scores = db.Column(db.String(100) , nullable = False)
    status = db.Column(db.String(30) , nullable = False)


    def __repr__(self):
        return f"{self.sno} -- {self.userid}"

#create contact mail table
class CreateContact(db.Model):
    sno = db.Column(db.Integer ,  primary_key = True)
    name = db.Column(db.String(30) , nullable=False)
    emailid = db.Column(db.String(50) , nullable = False)
    phnnumber = db.Column(db.String(20) , nullable = False)
    subject = db.Column(db.String(20) , nullable = False)
    message = db.Column(db.String(400) , nullable = False)

    def __repr__(self):
        return f"{self.name} -- {self.subject}"

def AddScore(uid , section , scores ,qid = 0 , status="notcompleted"):
    totalscores = 0
    uscores = []
    for i in scores:
        if i>=0:
            uscores.append(int(i)*10)


    totalscores = sum(uscores)
    session['totalscores'] = totalscores

    data = CreateScores.query.filter_by(userid=uid , section = section).first()

    if(data is None):
        scores = {}
        scores[qid] = uscores
        dataa = CreateScores(userid = uid , section = section , scores = json.dumps( scores ) , status = status)
        db.session.add(dataa)
        db.session.commit()

    else:
        scores = json.loads(  data.scores )
        scores[qid] = uscores

        # data.scores = json.dumps({'ts':scores})
        data.userid = uid
        data.status = status
        data.section = section 
        data.userid = uid 
        data.scores = json.dumps(scores)
        db.session.add(data)
        db.session.commit()
        
def SubmitScore(uid , section , status):
    data = CreateScores.query.filter_by(userid=uid , section = section).first()

    data.userid = uid
    data.status = status 

    sc =  json.loads(data.scores) 
    totals = 0
    for i in sc:
        totals += sum(sc[i])

    user =  CreateUsers.query.filter_by(sno = uid).first()
    user.score += totals 
    user.exams += 1

    db.session.add(user)
    db.session.add(data)
    db.session.commit()

@app.before_request
def create_tables_database():
    if not os.path.exists('./instance/examdb.db'):
        db.create_all()

@app.route('/',defaults={'flag':'false'})
@app.route('/<flag>')
def home(flag):
    session.pop('id',None)
    session.pop('uid',None)
    return render_template("home.html" , flag= flag)

@app.route('/register',defaults={'message':''})
@app.route('/register/<message>')
def register(message):
    return render_template("register.html",message=message)

@app.route('/login' , defaults={'message': ''})
@app.route('/login/<message>')
def login(message):
    return render_template("login.html" ,message = message)

@app.route('/contactme')
def contactme():
    flag= 'false'
    if 'contactme' in session:
        flag = 'true'
        session.pop('contactme',None)
    return render_template("contactme.html" , flag = flag)

@app.route("/contact/sendmessage" , methods=["POST"])
def sendmessage():
    if request.method == "POST":
        name = request.form.get("name")
        emailid = request.form.get("emailid")
        phnnumber = request.form.get("phnnumber")
        subject = request.form.get("subject")
        message = request.form.get("message")

        msg = CreateContact(name = name , emailid = emailid , phnnumber = phnnumber , subject = subject , message = message)

        db.session.add(msg)
        db.session.commit() 

        session['contactme'] = 'true'
        return redirect('/contactme')

@app.route('/examsec' , methods = ["POST"])
def examsec():
    if request.method == "POST":
        id = request.form.get("id")
        user = CreateUsers.query.filter_by(sno=id).first()

        allvalues = CreateQuestions.query.all()
        sec = CreateScores.query.with_entities(CreateScores.section).filter_by(userid = id , status = "completed").all()
        qdict  =  {}
        for i in allvalues:
            if i.section not in str(sec):
                if i.section not in qdict:
                    qdict[i.section] = 1
                else:
                    qdict[i.section] += 1
                
        return render_template('examsecpage.html' , p=user , qdict = qdict)

@app.route('/userprofile', methods=["POST"] )
@app.route('/userprofile')
def userprofile():
    if request.method=='POST':
        emailid = request.form.get("emailid")
        password = request.form.get("password")

        login = CreateUsers.query.filter_by(emailid = emailid).first()

        if(login is not None and login.password == password):
            alcompleted = CreateScores.query.with_entities(CreateScores.section).filter_by(userid = login.sno , status = "completed").all()

            sdata = []
            for i in alcompleted:
                sdata.append(i[0])

            count = CreateQuestions.query.filter(CreateQuestions.section.in_(sdata )).count()
 
            session['uid'] = login.sno
            return render_template('/userprofile.html',p=login , count = count)
        else:
            return redirect(url_for("login",message = "User Not registered , Try register "))
    else:
        if 'id' in session:
            id = session['id']

        elif 'uid' in session:
            id = session['uid']

        login = CreateUsers.query.filter_by(sno = id ).first()     
        alcompleted = CreateScores.query.with_entities(CreateScores.section).filter_by(userid = login.sno , status = "completed").all()
        sdata = []
        for i in alcompleted:
            sdata.append(i[0])

        count = CreateQuestions.query.filter(CreateQuestions.section.in_( sdata ) ).count()

        return render_template('/userprofile.html' , p= login , count = count )


@app.route('/adminprofile/<emailid>/<password>')
@app.route('/adminprofile', defaults = {'emailid':'f' , 'password':'p'},methods=["POST"] )
def adminprofile(emailid,password):
    contacts = CreateContact.query.all()
    if request.method=='POST':
        emailid = request.form.get("emailids")
        password = request.form.get("passworda")

        login = CreateAdmin.query.filter_by(emailid = emailid).first()
        users = CreateUsers.query.all()
        questions = CreateQuestions.query.order_by(CreateQuestions.section).all()

        if(login is not None and login.password == password):
            return render_template('/adminprofile.html',Admin=login , users=users , questions = questions , contacts = contacts )
        else:
            return redirect(url_for("login",message = "User Not registered , Try register "))
    else:
        emailid = emailid
        password = password

        login = CreateAdmin.query.filter_by(emailid = emailid).first()
        users = CreateUsers.query.all()
        questions = CreateQuestions.query.all()
        
        return render_template('/adminprofile.html',Admin=login , users=users , questions = questions , contacts = contacts )


@app.route('/createquestion' , methods=["POST"])
def createquestion():
    if request.method=="POST":
        emailid = request.form.get("emailid")
        password = request.form.get("password")
        
    return render_template('createquestion.html' , emailid= emailid , password = password)


@app.route("/addquestion",methods=["POST"])
def addquestion():
    if request.method=="POST":
        emailid = request.form.get("emailid")
        password = request.form.get("password")
        qname = request.form.get("qname")

        sinp = list( str( request.form.get("sinp")))
        sout = list( str( request.form.get("sout") ))

        ht1 = list( str(request.form.get("hinp1")) )
        ht12 = list( str( request.form.get("hout1")) )
        ht2 = list( str( request.form.get("hinp2") )  )
        ht22 = list ( str( request.form.get("hout2") ) )
        section = request.form.get("section")

        ht1 = [ht1 , ht12 ]
        ht2 = [ht2 , ht22]

        s = [sinp,sout]

        ht=[ht1 , ht2]

        s = json.dumps(s)
        ht = json.dumps(ht)

        # print(json.loads(ht) , json.loads(ht)[0] , s ,ht, "\n\n\n\n\n\n\n")

        qblock = CreateQuestions(question = qname , stestcase = s , htestcase = ht , section = section)
        db.session.add(qblock)
        db.session.commit()
        return redirect(url_for('adminprofile' , emailid=emailid , password = password ))

@app.route('/updateques/<id>/<emailid>/<password>')
def updateques(id,emailid,password):
    datas = CreateQuestions.query.filter_by(sno=id).first()

    st = json.loads(datas.stestcase)
    ht = json.loads(datas.htestcase)

    return render_template("updatequestion.html" , emailid=emailid , password=password , question= datas.question ,  st = st , ht=ht )

@app.route('/deleteques/<id>/<emailid>/<password>')
def deleteques(id,emailid , password):
    det = CreateQuestions.query.filter_by(sno=id).first()
    db.session.delete(det)
    db.session.commit()

    return redirect(url_for('adminprofile' , emailid=emailid , password=password))

@app.route('/userregister', methods=["POST"] )
def userregistration():
    if request.method=='POST':
        name = request.form.get("name")
        emailids= request.form.get("emailid")
        password = request.form.get("password")

        result = CreateUsers.query.filter_by(emailid = emailids).first()

        if(result is None or emailids != result.emailid):
            users = CreateUsers( name=name , emailid=emailids , password=password , score=0,exams=0)
            db.session.add(users)
            db.session.commit()
            
            return redirect(url_for('home', flag='true'))
        else:
            return redirect(url_for('register',message = 'Email Id already registerd , try login'))

@app.route('/adminregister', methods=["POST"] )
def adminregistration():
    if request.method=='POST':
        name = request.form.get("namea")
        emailids= request.form.get("emailida")  
        password = request.form.get("passworda")  
        adminpassword = request.form.get("adminpassword")

        if(adminpassword=='Sudheer440@'):
            result = CreateAdmin.query.filter_by(emailid = emailids).first()

            if(result is None or emailids != result.emailid):
                admin = CreateAdmin( name=name , emailid=emailids , password=password )
                db.session.add(admin)
                db.session.commit()
                
                return redirect(url_for('home', flag='true'))
            else:
                return redirect(url_for('register',message = 'Email Id already registerd , try login'))
        else:
                return redirect(url_for('register',message = "Wrong Admin Password , try user registration"))


@app.route("/exam/<section>/<id>" )
@app.route('/exam/<section>', defaults={'id':'1'} , methods = ["POST"])
def exam(section , id):
    if(request.method=="POST"):
        uid = request.form.get("id")
        allq = CreateQuestions.query.filter_by(section=section).all()

        id = allq[0].sno
        p = CreateQuestions.query.filter_by(sno=id).first()

        st = json.loads(p.stestcase)
        ht = json.loads(p.htestcase)

        return render_template("exam.html", section  = section, uid=uid ,id = id ,ques = p.question, st=st , ht=ht ,allq = allq)
    else:
        allq = CreateQuestions.query.filter_by(section=section)
        p = CreateQuestions.query.filter_by(sno=id).first()

        st = json.loads(p.stestcase)
        ht = json.loads(p.htestcase)

        # print(st[0], ht[0] , "\n\n\n\n\n\n\n\n\n")
        if "uid" in session:
            uid = session["uid"]

        return render_template("exam.html", id = id , uid = uid ,section = section,ques = p.question, st=st , ht=ht ,allq = allq)

@app.route("/executer" , methods=["POST"])
def executerun():
    if(request.method=="POST"):
        filepath ='static/'
        lang = request.form.get("lang")
        inp = request.form.get("inp")
        code = request.form.get("code")
        id = request.form.get("id")

        question = CreateQuestions.query.filter_by(sno=id).first()
        sinp = question.stestcase
        inp = json.loads(sinp)
        inp = "".join(inp[0])

        # print(inp,"\n\n\n")

        if(lang=="c_cpp"):
            if not os.path.exists(filepath+'temp.c'):
                os.open(filepath+'try.c',os.O_CREAT)

            fd = os.open(filepath+"try.c",os.O_WRONLY)   
            os.truncate(fd,0)
            fileadd = str.encode(str(code))
            os.write(fd,fileadd)
            os.close(fd)
            
            s = subprocess.run(['gcc' , '-o',filepath+'new',filepath+'temp.c'] )
            r = subprocess.run([filepath+'new.exe'],input=bytes(inp.encode()) , stdout=subprocess.PIPE) 
            output = r.stdout.decode('utf-8')
            return output
        
        elif(lang=="python"):
            if not os.path.exists(filepath+'ty.py'):
                os.open(filepath+'ty.py',os.O_CREAT)
            
            fd = os.open(filepath+'ty.py' , os.O_WRONLY)
            os.truncate(fd,0)
            fileadd = str.encode(str(code))
            os.write(fd,fileadd)
            os.close(fd)
            s = subprocess.run(['python',filepath+'ty.py'],input=bytes(inp.encode()),capture_output=True)
            if s.returncode !=0:
                error = s.stderr.decode("utf-8")
                
                return(error)
            else:
                output = s.stdout.decode("utf-8")

                return output

    return redirect('/exam')

@app.route('/executesubmit' , methods=['POST'])
def executesubmit():
    if(request.method=="POST"):
        testcases = [0]*2
        filepath ='static/'
        lang = request.form.get("lang")
        inp = request.form.get("inp")
        code = request.form.get("code")

        id = request.form.get("id")
        uid = request.form.get("uid")
        section = request.form.get("section")

        ques = CreateQuestions.query.filter_by(sno=id).first()

        ht = ques.htestcase
        ht = json.loads(ht)
        tc = [] 
        for i in ht:
            a1 = "".join(i[0])
            a2 = "".join(i[1])
            tc.append([a1,a2])
        # print(tcase , "\n\n\n\n\n\n\n\n")

        if(lang=="c_cpp"):
            count=0
            for ca in tc:
                inp = ca[0]
                ans = ca[1]
                if not os.path.exists(filepath+'try.c'):
                    os.open(filepath+'try.c',os.O_CREAT)

                fd = os.open(filepath+"try.c",os.O_WRONLY)   
                os.truncate(fd,0)
                fileadd = str.encode(str(code))
                os.write(fd,fileadd)
                os.close(fd)
                
                s = subprocess.run(['gcc' , '-o',filepath+'new.exe',filepath+'try.c'] )
                r = subprocess.run([filepath+'new.exe'],input=bytes(inp.encode()) , stdout=subprocess.PIPE) 
                output = r.stdout.decode('utf-8')

                if(str(output).strip() == str(ans).strip()):
                    testcases[count] = 1
                count+=1


            AddScore(section = section , uid = uid ,qid = id, scores = testcases)
            return (testcases)
        
        elif(lang=="python"):
            count = 0
            for ca in tc:
                inp=ca[0]
                ans=ca[1]
                if not os.path.exists(filepath+'ty.py'):
                    os.open(filepath+'ty.py',os.O_CREAT)
                
                fd = os.open(filepath+'ty.py' , os.O_WRONLY)
                os.truncate(fd,0)
                fileadd = str.encode(str(code))
                os.write(fd,fileadd)
                os.close(fd)
                
                s = subprocess.run(['python',filepath+'ty.py'],input=bytes(inp.encode()),capture_output=True)
                if s.returncode !=0:
                    print(s.stderr.decode("utf-8"))
                    testcases[count]=-1
                else:
                    output = s.stdout.decode("utf-8")
                    if(str(output).strip() == str(ans).strip()):
                        testcases[count] = 1
                count+=1

            AddScore(section = section , uid = uid ,qid = id , scores = testcases)
            
            return(testcases)

    return redirect('/exam')


@app.route('/endtest/<section>/<uid>')
def endtest(section,uid):
    
    session['id'] = uid
    SubmitScore(uid = uid , section = section , status = "completed")

    return redirect("/userprofile")

if __name__ == "__main__":
    app.run(debug=True)
 