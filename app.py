from flask import Flask, render_template, request, url_for, redirect

from flask_sqlalchemy import SQLAlchemy

d = {"course_1": "MAD I", "course_2": "DBMS", "course_3": "PDSA", "course_4": "BDM"}


from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///week7_database.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


enrollments = db.Table(
    "enrollments",
    db.Column("enrollment_id", db.Integer, primary_key=True, autoincrement=True),
    db.Column(
        "estudent_id", db.Integer, db.ForeignKey("student.student_id"), nullable=False
    ),
    db.Column(
        "ecourse_id", db.Integer, db.ForeignKey("course.course_id"), nullable=False
    ),
)


class student(db.Model):
    student_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    roll_number = db.Column(db.String(120), unique=True, nullable=False)
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120))
    taken = db.relationship("course", secondary=enrollments, backref=("studying"))

    def __repr__(self):
        return f"course({self.student_id},{self.roll_number},{self.first_name})"


class course(db.Model):
    course_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    course_code = db.Column(db.String(120), unique=True, nullable=False)
    course_name = db.Column(db.String(120), nullable=False)
    course_description = db.Column(db.String(120))

    def __repr__(self):
        return f"course({self.course_id},{self.course_code},{self.course_name})"


@app.route("/")
def index():
    l = student.query.all()
    return render_template("index.html", l=l, title="Home")


@app.route("/student/create/", methods=["GET", "POST"])
def student_create():
    if request.method == "GET":
        return render_template("student_create.html", title="Add Student")
    else:
        if "l_name" in request.form:
            new_stu = student(
                roll_number=request.form["roll"],
                first_name=request.form["f_name"],
                last_name=request.form["l_name"],
            )
        else:
            new_stu = student(
                roll_number=request.form["roll"], first_name=request.form["f_name"]
            )
        rolls_taken = [x.roll_number for x in student.query.all()]
        if request.form["roll"] not in rolls_taken:
            db.session.add(new_stu)
            db.session.commit()
        else:
            return render_template("taken_roll.html", title="Home")
        return redirect(url_for("index"))


@app.route("/student/<int:student_id>/update/", methods=["GET", "POST"])
def update_student(student_id):
    if request.method == "GET":
        s = student.query.filter_by(student_id=student_id).first()
        courses = course.query.all()

        return render_template(
            "update.html",
            current_roll=s.roll_number,
            current_f_name=s.first_name,
            current_l_name=s.last_name,
            title="Update Student",
            student_id=s.student_id,
            courses=courses,
        )

    else:

        s = student.query.filter_by(student_id=student_id).first()
        s.first_name=request.form['f_name']
        if 'l_name' in request.form:
            s.last_name=request.form['l_name']

        db.session.query(enrollments).filter_by(estudent_id=student_id)

        course_id_form = int(request.form["course"])

        c = course.query.filter_by(course_id=course_id_form).first()
        s.taken.append(c)

        db.session.commit()
        return redirect(url_for("index"))


@app.route("/student/<int:student_id>/delete/")
def delete_student(student_id):
    rn = student.query.filter_by(student_id=student_id).first().roll_number
    db.session.query(enrollments).filter_by(estudent_id=student_id).delete()
    student.query.filter_by(student_id=student_id).delete()
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/student/<int:student_id>/")
def details(student_id):

    s = student.query.filter_by(student_id=student_id).first()

    enrolled_in = db.session.query(enrollments).filter_by(estudent_id=student_id).all()

    course_det = [course.query.filter_by(course_id=x[2]).first() for x in enrolled_in]

    new = [
        (x.course_id, x.course_code, x.course_name, x.course_description)
        for x in course_det
    ]

    return render_template(
        "details.html",
        roll_number=s.roll_number,
        first_name=s.first_name,
        last_name=s.last_name,
        student_id=s.student_id,
        courses_taken=new,
        title="Home",
    )


@app.route("/student/<int:student_id>/withdraw/<int:course_id>/")
def withdraw_enroll(student_id,course_id):
    result=db.session.query(enrollments).filter_by(estudent_id=student_id,
                                            ecourse_id=course_id)
    result.delete()
    db.session.commit()    
    return redirect(url_for("index"))


@app.route("/courses/")
def course_list():
    l=course.query.all()
    return render_template("course_list.html",l=l,title="Courses")


@app.route("/course/create/", methods=["GET", "POST"])
def new_course():
    if request.method=="GET":
        return render_template("course_create.html",title="Create course")

    else:
        codes_taken = [x.course_code for x in course.query.all()]
        if request.form['code'] in codes_taken:
            return render_template("code_taken.html",title="Error")

        else:
            form=request.form
            new_course=course(course_code=form['code'],
                            course_name=form['c_name'],
                            course_description=form['desc'])
            
            db.session.add(new_course)
            db.session.commit()

            return redirect(url_for("course_list"))



@app.route("/course/<int:course_id>/")
def course_details(course_id):
    c=course.query.filter_by(course_id=course_id).first()
    s_id=db.session.query(enrollments).filter_by(ecourse_id=course_id).all()
    s = [student.query.filter_by(student_id=x[1]).first() for x in s_id]

    return render_template("course_details.html",c=c,l=s,title="Course Details")


@app.route("/course/<int:course_id>/update/", methods=["GET", "POST"])
def course_update(course_id):
    if request.method=="GET":

        c=course.query.filter_by(course_id=course_id).first()
        
        return render_template("course_update.html",
                                title="Update Course",
                                c=c
                                )
    else:
        c=course.query.filter_by(course_id=course_id).first()
        c.course_name=request.form['c_name']
        c.course_description=request.form['desc']
        db.session.commit()

        return redirect(url_for("course_list"))

@app.route("/course/<int:course_id>/delete/")
def course_delete(course_id):

    db.session.query(enrollments).filter_by(ecourse_id=course_id).delete()
    course.query.filter_by(course_id=course_id).delete()
    db.session.commit()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=1)
