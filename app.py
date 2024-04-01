from flask import Flask, render_template, session, request, redirect, url_for, flash, jsonify
import sqlite3
import bcrypt
from datetime import datetime, timedelta
# import speech_recognition as sr
from textblob import TextBlob
import pandas

datetime_str = "2024-03-10 12:30:45"

dt_obj = datetime.strptime(datetime_str,"%Y-%m-%d %H:%M:%S" )
print(dt_obj)

app = Flask(__name__)
app.secret_key = "abc"

session = {}



def identify_sentiment(audio): # audio = name of audio file in string

    recognizer = sr.Recognizer()

    audio_file = audio

    with sr.AudioFile(audio_file) as file:
        audio_data = recognizer.record(file)
        try:
            text = recognizer.recognize_google(audio_data)
        except sr.UnknownValueError:
            return "Google Speech Recognition could not understand the audio"
    blob = TextBlob(text)
    sentimet_polarity = blob.sentiment.polarity
    if sentimet_polarity > 0:
        return "Positive"
    elif sentimet_polarity < 0:
        return "Negative"
    else:
        return "Neutral"

@app.route("/", methods=["GET", "POST"])
def index():
    isLogin = False
    if "username" in session:
        isLogin = True

    return render_template('index.html', isLogin = isLogin)

@app.route("/myprofile", methods=["GET", "POST"])
def myprofile():
    return render_template("myprofile.html")

@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route("/login", methods=["GET", "POST"])
def login():
    connector = sqlite3.connect("hw.db")
    cursor = connector.cursor()
    if request.method == "POST":
        input_username = request.form.get("input_username")
        input_password = request.form.get("input_password")
        encoded_password = input_password.encode("UTF-8")

        command = "SELECT password FROM users_table WHERE username = (?)"
        # print(input_username)
        cursor.execute(command, (input_username,))
        db_pw_tuple = cursor.fetchall()

        # rint(db_pw_tuple)
        for db_password in db_pw_tuple:
            # print(db_password[0])
            # print(input_password)
            # if input_password == db_password[0]:

            # print(encoded_password)
            # print(db_password)

            if bcrypt.checkpw(encoded_password, db_password[0]) == True:
                # print("input pw matches db pw!")
                session["username"] = input_username
                update_command = "UPDATE users_table SET logindate = ? WHERE username = ?"
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute(update_command, (current_time, input_username))
                connector.commit()
                return redirect(url_for("index"))
        else:
            flash("Invalid")
            # print("input pw does NOT match pw!")

        return redirect(url_for("login"))

    else:
        return render_template("login.html")


@app.route("/signup", methods = ["GET", "POST"])
def signup():
    if request.method == 'POST':
        # retrieve values form user input
        username = request.form.get("username")
        password = request.form.get("password")
        re_passwrod = request.form.get("re-enter password")
        email = request.form.get("Email")
        age = request.form.get("Age")
        # store value into database
        conn = sqlite3.connect("hw.db")
        cursor = conn.cursor()
        command = "SELECT password FROM users_table WHERE username = ?;"
        cursor.execute(command,(username,))
        result = cursor.fetchone()
        if password != re_passwrod:
            flash("confirm password different")
            return render_template('signup.html')
        if result == None:
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
            command = "INSERT INTO users_table (username, password, email, age) VALUES (?, ?, ?, ?)"
            cursor.execute(command, (username, hashed_password, email, age))
            conn.commit()
            conn.close()
        else:
            flash("Existing Username")
            return render_template('signup.html')
        return redirect(url_for("login"))
    else:
        return render_template("signup.html")


@app.route("/database1")
def database1():
    connector = sqlite3.connect("hw.db")
    cursor = connector.cursor()
    command = "SELECT username, age, email, logindate FROM users_table"
    cursor.execute(command)
    users = cursor.fetchall()
    users_index = [i for i in range(1, len(users)+1)]
    users_username = []
    users_age = []
    users_email = []
    users_logindate = []
    loginCounts = []
    for user in users:
        users_username.append(user[0])
        users_age.append(user[1])
        users_email.append(user[2])
        users_logindate.append(user[3])
    for i in range(30):
        command = "SELECT COUNT(*) FROM users_table WHERE logindate = ?"
        d = datetime.now().date() - timedelta(days=i)
        d = d.strftime("%Y-%m-%d")
        cursor.execute(command, (d,))
        loginCounts.append(cursor.fetchall())
    loginCounts = [count[0] for count in loginCounts]
    loginCounts = [count[0] for count in loginCounts]
    print(loginCounts)
    connector.close()
    return render_template("database1.html", num_users = len(users), indices = users_index, usernames = users_username, ages = users_age, emails = users_email, logindates = users_logindate, loginCount = loginCounts)

@app.route('/delete_user/<username>', methods=["POST"])
def delete_user(username):
    connector = sqlite3.connect('hw.db')
    cursor = connector.cursor()
    command = "DELETE FROM users_table where username = ?"
    cursor.execute(command, (username, ))
    connector.commit()
    connector.close()
    return jsonify({"success":True}), 200




@app.route("/database_main")
def database_main():
    data = pandas.read_csv("consulting_data_content_logic.csv")

    # DataFrame
    # Gender distribution
    gender_distribution = data["gender"].value_counts().to_dict()

    # Type of consulting distribution
    type_distribution = data["type_of_consulting"].value_counts().to_dict()
    return render_template("database_main.html", gender_distribution=gender_distribution,type_distribution=type_distribution)
    # gender_distribution = {"Male": 50}
    # Male: 500
    # Female: 490
    # Other: 10
    # {"Male": 500, "Female": 490,..."}

def add_data(username, date, contents, sentiment):
    connector = sqlite3.connect("hw.db")
    cursor = connector.cursor()
    cursor.execute("SELECT MAX(id) from consult")
    result = cursor.fetchone()
    new_id = int(result) + 1
    command = "INSERT INTO consult (username, date, contents, sentiment, id) VALUES (?,?,?,?,?);"
    cursor.execute(command,(username,date,contents,sentiment, new_id))
    connector.commit()
    connector.close()




if __name__ =="__main__":
    app.run(debug=True)