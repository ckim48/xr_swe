from flask import Flask, render_template, session, request, redirect, url_for, flash, jsonify, send_file
import sqlite3
import bcrypt
from datetime import datetime, timedelta
# import speech_recognition as sr
from textblob import TextBlob
import pandas, json

datetime_str = "2024-03-10 12:30:45"

dt_obj = datetime.strptime(datetime_str,"%Y-%m-%d %H:%M:%S" )
print(dt_obj)

app = Flask(__name__)
app.secret_key = "abc"


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
    isAdmin = False
    if "username" in session:
        isLogin = True
        if session["username"] == "testtest":
            isAdmin = True
    return render_template('index.html', isLogin = isLogin, isAdmin=isAdmin)

@app.route("/myprofile", methods=["GET", "POST"])
def myprofile():
    isLogin = False
    isAdmin = False
    if "username" in session:
        isLogin = True
        if session["username"] == "testtest":
            isAdmin = True
        conn = sqlite3.connect("hw.db")
        cursor = conn.cursor()
        command = "SELECT email, age, country, mbti, description, sentiment FROM users_table WHERE username = ?;"
        cursor.execute(command, (session["username"],))
        result = cursor.fetchall()

        username = session["username"]
        loginCounts = []
        loginPeriod = []
        connector2 = sqlite3.connect("hw.db")
        cursor2 = connector2.cursor()
        for i in range(7):
            command2 = "SELECT COUNT(*) FROM loginCounts WHERE username = ? and logindate = ?"
            d = datetime.now().date() - timedelta(days=i)
            d = d.strftime("%Y-%m-%d")
            cursor2.execute(command2, (username, d,))
            loginCounts.append(cursor2.fetchall())
            loginPeriod.append(d)
        counts = [count[0] for count in loginCounts]
        counts = [count[0] for count in counts]
        print(loginPeriod)
        connector2.close()

        return render_template("myprofile.html", loginCount = counts[::-1], isAdmin=isAdmin,loginPeriod = loginPeriod[::-1], active_page = "myprofile", username=session["username"], age=result[0][1], email=result[0][0], country = result[0][2], mbti = result[0][3], description = result[0][4], sentiment = result[0][5], isLogin=isLogin)
    if "username" in session:
        return render_template("myprofile.html")
    else:
        return render_template("login.html")

@app.route("/logout", methods = ["GET"])
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route("/login", methods=["GET", "POST"])
def login():
    connector = sqlite3.connect("hw.db")
    cursor = connector.cursor()
    connector2 = sqlite3.connect("hw.db")
    cursor2 = connector2.cursor()
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
            if bcrypt.checkpw(encoded_password, db_password[0]) == True:
                # print("input pw matches db pw!")
                session["username"] = input_username
                update_command = "UPDATE users_table SET logindate = ? WHERE username = ?"
                current_time = datetime.now().strftime("%Y-%m-%d")
                cursor.execute(update_command, (current_time, input_username))
                connector.commit()
                login_command = "INSERT INTO loginCounts (username, logindate) VALUES (?, ?)"
                cursor2.execute(login_command, (input_username, current_time))
                connector2.commit()
                connector.close()
                connector2.close()
                print(session)
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
        country = request.form.get("Country")
        MBTI = request.form.get("MBTI")
        description = request.form.get("Description")
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
            current_time = datetime.now().strftime("%Y-%m-%d")
            command = "INSERT INTO users_table (username, password, email, age, country, MBTI, description, signdate, sentiment) VALUES (?, ?, ?, ?, ?, ?, ?,?,?)"
            cursor.execute(command, (username, hashed_password, email, age, country, MBTI, description,current_time, 0))
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
    isAdmin = False
    isLogin = False
    if "username" in session:
        isLogin = True
        if session["username"] == "testtest":
            isAdmin = True
    connector = sqlite3.connect("hw.db")
    cursor = connector.cursor()
    command = "SELECT username, age, email, country, mbti, description, logindate FROM users_table"
    cursor.execute(command)
    users = cursor.fetchall()
    users_index = [i for i in range(1, len(users)+1)]
    users_username = []
    users_age = []
    users_email = []
    users_country = []
    users_mbti = []
    users_description = []
    users_logindate = []
    loginCounts = []
    loginPeriod = []
    for user in users:
        users_username.append(user[0])
        users_age.append(user[1])
        users_email.append(user[2])
        users_country.append(user[3])
        users_mbti.append(user[4])
        users_description.append(user[5])
        users_logindate.append(user[6])
    connector.commit()
    connector.close()
    connector2 = sqlite3.connect("hw.db")
    cursor2 = connector2.cursor()
    for i in range(7):
        command2 = "SELECT COUNT(*) FROM loginCounts WHERE logindate = ?"
        d = datetime.now().date() - timedelta(days=i)
        d = d.strftime("%Y-%m-%d")
        cursor2.execute(command2, (d,))
        loginCounts.append(cursor2.fetchall())
        loginPeriod.append(d)
    counts = [count[0] for count in loginCounts]
    counts = [count[0] for count in counts]
    print(loginPeriod)
    signup_counts = {}
    for user in users:
        signup_month = user[6].split("-")[0] + "-" + user[6].split("-")[1]
        if signup_month in signup_counts:
            signup_counts[signup_month] += 1
        else:
            signup_counts[signup_month] = 1

    signup_period = list(signup_counts.keys())
    signup_count = list(signup_counts.values())
    connector.close()
    connector2.close()
    return render_template("database1.html", isAdmin=isAdmin, active_page = "database", isLogin = isLogin, num_users = len(users), indices = users_index, usernames = users_username, ages = users_age, emails = users_email, country = users_country, mbti = users_mbti, description = users_description, logindates = users_logindate, loginCount = counts, loginPeriod = loginPeriod, signupCount=signup_count, signupPeriod=signup_period)

@app.route('/update_database/<username>', methods=['POST'])
def update_database(username):
    print("Called")
    connector = sqlite3.connect("hw.db")
    cursor = connector.cursor()
    age = request.form.get("age")
    email = request.form.get("email")
    mbti = request.form.get("mbti")
    description = request.form.get("description")
    command = "UPDATE users_table SET age = ?, email = ?, mbti = ?, description = ? WHERE username = ?"
    cursor.execute(command, (age, email, mbti, description, username))
    connector.commit()
    connector.close()
    return jsonify({"success": True}), 200

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
    isAdmin = False
    isLogin = False
    if "username" in session:
        isLogin = True
        if session["username"] == "testtest":
            isAdmin = True
    data = pandas.read_csv("consulting_data_content_logic.csv")
    # DataFrame
    # Gender distribution
    gender_distribution = data["gender"].value_counts().to_dict()
    type_distribution = data["type_of_consulting"].value_counts().to_dict()
    sentiment_distribution = data["sentiment"].value_counts().to_dict()

    first, second, third, fourth = ["E", "I"], ["N", "S"], ["F", "T"], ["J", "P"]
    conn = sqlite3.connect("hw.db")
    cursor = conn.cursor()
    MBTI_dict = {}
    for f in first:
        for s in second:
            for t in third:
                for fo in fourth:
                    mbti = f+s+t+fo
                    command2 = "SELECT COUNT(*) FROM users_table WHERE MBTI = ?"
                    cursor.execute(command2, (mbti, ))
                    result = cursor.fetchone()[0]
                    MBTI_dict[mbti] = result
    conn.close()

    conn = sqlite3.connect("hw.db")
    cursor = conn.cursor()
    age_dict = {"10s": 0, "20s": 0, "30s": 0, "40s": 0, "50s": 0, "60s": 0}
    for age_min in [10, 20, 30, 40, 50, 60]:
        age_max = age_min+9
        command2 = "SELECT COUNT(*) FROM users_table WHERE age >= ? and age <= ?"
        cursor.execute(command2, (age_min, age_max, ))
        result = cursor.fetchone()[0]
        age_dict[str(age_min)+"s"] = result
    conn.close()
    print(age_dict)

    return render_template("database_main.html", active_page = "database", isLogin = isLogin, gender_distribution=gender_distribution, type_distribution = type_distribution, sentiment_distribution = sentiment_distribution, age_distribution = age_dict, mbti_distribution = MBTI_dict, isAdmin=isAdmin)
    # gender_distribution = {"Male": 50}
    # Male: 500
    # Female: 490
    # Other: 10
    # {"Male": 500, "Female": 490,..."}

@app.route("/dashboard")
def dashboard():
    isLogin = False
    isAdmin = False
    if "username" in session:
        isLogin = True
        if session["username"] == "testtest":
            isAdmin = True
    return render_template('dashboard.html', isLogin=isLogin, isAdmin=isAdmin)

@app.route('/download_mac')
def download_mac():
    file_path = "consulting_data_content_logic.csv"
    return send_file(file_path)
# send_file is used to send the correspoding file to the user's browser for download
@app.route('/download_window')
def download_window():
    file_path = "consulting_data_content_logic.csv"
    return send_file(file_path)

if __name__ =="__main__":
    app.run(debug=True)
