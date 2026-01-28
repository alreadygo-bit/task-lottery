import os
import json
import random
from flask import Flask, request, jsonify, send_from_directory, render_template_string

# Render 会设置 PORT 环境变量
port = int(os.environ.get("PORT", 5000))

app = Flask(__name__, static_folder='static')

DATA_DIR = 'data'
TASKS_FILE = os.path.join(DATA_DIR, 'tasks.txt')
PARTICIPANTS_FILE = os.path.join(DATA_DIR, 'participants.txt')
RESULTS_FILE = os.path.join(DATA_DIR, 'results.json')

os.makedirs(DATA_DIR, exist_ok=True)

def load_list(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def save_results(results):
    with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

def load_results():
    if not os.path.exists(RESULTS_FILE):
        return {}
    with f := open(RESULTS_FILE, 'r', encoding='utf-8'):
        return json.load(f)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/participants')
def get_participants():
    participants = load_list(PARTICIPANTS_FILE)
    results = load_results()
    available = [p for p in participants if p not in results]
    return jsonify(available)

@app.route('/api/draw', methods=['POST'])
def draw():
    name = request.json.get('name')
    if not name:
        return jsonify({'error': '请输入姓名'}), 400

    results = load_results()
    if name in results:
        return jsonify({'error': '你已经抽过了！'}), 400

    tasks = load_list(TASKS_FILE)
    if not tasks:
        return jsonify({'error': '任务列表为空，请联系管理员'}), 400

    # 计算每个任务还能被抽几次（支持重复任务）
    from collections import Counter
    total_count = Counter(tasks)
    used_count = Counter(results.values())
    available_tasks = [
        task for task in tasks
        if used_count[task] < total_count[task]
    ]

    if not available_tasks:
        return jsonify({'error': '所有任务已被抽完！'}), 400

    chosen = random.choice(available_tasks)
    results[name] = chosen
    save_results(results)

    return jsonify({'task': chosen})

# 简易 admin 页面（无密码，因在内网或信任环境）
@app.route('/admin')
def admin():
    results = load_results()
    items = [{'name': k, 'task': v} for k, v in results.items()]
    html = '''
    <h2>✅ 任务分配结果</h2>
    <table border="1" cellpadding="10" style="border-collapse: collapse;">
      <tr><th>姓名</th><th>任务</th></tr>
      {rows}
    </table>
    <br>
    <a href="/">← 返回抽签</a> |
    <a href="/admin/raw">查看原始 JSON</a>
    '''.format(
        rows=''.join(f"<tr><td>{item['name']}</td><td>{item['task']}</td></tr>" for item in items)
    )
    return html

@app.route('/admin/raw')
def admin_raw():
    results = load_results()
    return jsonify(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
