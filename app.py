from flask import Flask, g,request,jsonify
import sqlite3

app = Flask(__name__)
app.config['DATABASE'] = 'database.db'
# коннект к бд
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row  
    return g.db
# закрытие к коннекта к бд
@app.teardown_appcontext
def close_db(e):
    db = g.pop('db', None)
    if db is not None:
        db.close()
# ф-ция для создания бд в sqlite
def db_init():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS schedules (
                schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
                medicine_name TEXT NOT NULL,
                frequency TEXT NOT NULL,
                duration TEXT NOT NULL,
                user_id TEXT,
                time TEXT    
            )
        ''')
        db.commit()


# /schedules?user_id=
# по юзеру
@app.route('/schedules', methods=['GET'])
def get_medications():
    db = get_db()
    cursor = db.cursor()
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({"error":"Missing User"}),404
    
    cursor.execute('''
    SELECT * FROM schedules WHERE user_id=?
    ''',(user_id))

    cursor = db.execute('SELECT schedule_id FROM schedules WHERE user_id = ?', (user_id))
    schedules = cursor.fetchall()

    if not schedules:
        return jsonify({'message': 'No schedules found for this user'}), 404

    return jsonify({'schedules': [dict(sched) for sched in schedules]})


# /schedule?user_id=&schedule_id=
# по юзеру и графику
@app.route('/schedule',methods=['GET'])
def get_schedules_id_and_user_id():
    user_id = request.args.get('user_id')
    schedule_id = request.args.get('schedule_id')

    if not user_id or not schedule_id:
        return jsonify({"error":"Missing data"}),400
    
    db = get_db()
    cursor = db.cursor()    

    cursor.execute('''
    SELECT * FROM schedules WHERE user_id=? AND schedule_id=?
    ''',(user_id,schedule_id))

    rows = cursor.fetchall()

    if not rows:
        return jsonify({"error":"Missing schedule"}),404

    user_data=[{"frequency":row["frequency"],"duration":row["duration"],"time":row["time"]}for row in rows]

    return jsonify({
        "user_id": user_id,
        "schedule_id": schedule_id,
        "schedule": user_data
    })


# /next_takings?user_id=
# по след приему
@app.route('/next_takings',methods=['GET'])
def get_next_take():
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({"error":"Missing User"}),400
    
    db = get_db()
    cursor = db.cursor()    

    cursor.execute('''
    SELECT * FROM schedules WHERE user_id=?
    ''',(user_id))

    rows = cursor.fetchall()

    if not rows:
        return jsonify({"error":"Missing User"}),404

    next_take=[{"time":row["time"],"medicine_name":row["medicine_name"]}for row in rows]

    return jsonify({
        "user_id": user_id,
        "schedule": next_take
    })


# пост данных
# json пример:
# {
    # "medicine_name":"витамины",
    # "frequency":"2 раза в день",
    # "duration":"месяц",
    # "user_id":"1",
    # "time":"12:00/19:00"
# } 
@app.route('/schedule',methods=['POST'])
def schedule():
    data = request.get_json()
    medicine_name= data.get('medicine_name')
    frequency = data.get('frequency')
    duration = data.get('duration')
    user_id = data.get('user_id')
    time = data.get('time')

    if not all([medicine_name,frequency,duration,user_id]):
        return jsonify({'error':'Missing data'}),400

    db=get_db()
    db.execute('''
    INSERT INTO schedules (medicine_name,frequency,duration,user_id,time)
    VALUES (?,?,?,?,?)
    ''',(medicine_name,frequency,duration,user_id,time))
    db.commit()

    return jsonify({'message':'schedule added successfully!'}),201

# дефолтный путь
@app.route('/')
def index():
    db = get_db()
    cursor = db.execute('SELECT * FROM schedules')
    users = cursor.fetchall()
    return {'users': [dict(user) for user in users]}

# Запуск приложения
if __name__ == '__main__':
    # Инициализация бд
    # db_init()  
    app.run(debug=True)