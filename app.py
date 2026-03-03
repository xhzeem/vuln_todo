from flask import Flask, render_template, request, redirect, url_for, session, render_template_string, g
import sqlite3
import os
import subprocess

app = Flask(__name__)
app.secret_key = 'super_secret_lab_key'
DATABASE = 'database.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Vulnerability 1: SQL Injection in Login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        db = get_db()
        cursor = db.cursor()
        
        # SQL Injection vulnerable line
        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        
        try:
            cursor.execute(query)
            user = cursor.fetchone()
            if user:
                session['user_id'] = user['id']
                session['username'] = user['username']
                return redirect('/dashboard')
            else:
                return render_template('login.html', error='Invalid credentials')
        except sqlite3.Error as e:
            return render_template('login.html', error=f'Database error: {e}')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# Vulnerability 2: Stored XSS in Dashboard / Tasks
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/')
        
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM tasks WHERE user_id = ?', (session['user_id'],))
    tasks = cursor.fetchall()
    
    return render_template('dashboard.html', tasks=tasks, username=session.get('username'))

@app.route('/task/add', methods=['GET', 'POST'])
def add_task():
    if 'user_id' not in session:
        return redirect('/')
        
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        
        db = get_db()
        cursor = db.cursor()
        # Parameterized query used here to isolate the XSS vulnerability (we render unescaped in the template)
        cursor.execute('INSERT INTO tasks (user_id, title, description) VALUES (?, ?, ?)', (session['user_id'], title, description))
        db.commit()
        return redirect('/dashboard')
        
    return render_template('add_task.html', username=session.get('username'))

# Vulnerability 3: SSTI in User Profile setting
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect('/')
        
    db = get_db()
    cursor = db.cursor()
    
    if request.method == 'POST':
        bio = request.form.get('bio')
        cursor.execute('UPDATE users SET bio = ? WHERE id = ?', (bio, session['user_id']))
        db.commit()
        
    cursor.execute('SELECT bio FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    current_bio = user['bio'] if user and user['bio'] else "No bio set."
    
    # Intentionally vulnerable to Server-Side Template Injection
    # The bio is evaluated as a Jinja2 template string before rendering the main profile page
    try:
        rendered_bio = render_template_string(current_bio)
    except Exception as e:
        rendered_bio = f"Error rendering bio: {str(e)}"
        
    return render_template('profile.html', bio=rendered_bio, raw_bio=current_bio, username=session.get('username'))

# Vulnerability 4: OS Command Injection in System Check
@app.route('/system_check', methods=['GET', 'POST'])
def system_check():
    if 'user_id' not in session:
        return redirect('/')
        
    output = ""
    if request.method == 'POST':
        target_ip = request.form.get('ip')
        if target_ip:
            # Command Injection vulnerable line
            command = f"ping -c 1 {target_ip}"
            try:
                # Using shell=True and unsanitized input
                process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()
                output = stdout.decode('utf-8') + stderr.decode('utf-8')
            except Exception as e:
                output = str(e)
                
    return render_template('system.html', output=output, username=session.get('username'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
