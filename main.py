import os
import time
import requests

# Настройки (лучше вынести в переменные окружения)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = "ваш_username"
REPO_NAME = "ваш_репозиторий"
LAST_ISSUE_FILE = "last_issue_id.txt"

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def get_last_issue_id():
    if os.path.exists(LAST_ISSUE_FILE):
        with open(LAST_ISSUE_FILE, "r") as f:
            return int(f.read().strip())
    return 0

def save_last_issue_id(issue_id):
    with open(LAST_ISSUE_FILE, "w") as f:
        f.write(str(issue_id))

def fetch_new_issues():
    last_id = get_last_issue_id()
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues"
    params = {"state": "open", "sort": "created", "direction": "desc", "per_page": 10}
    
    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code != 200:
        print(f"Ошибка API: {response.status_code}")
        return []

    issues = response.json()
    new_issues = [i for i in issues if i["number"] > last_id]
    
    if new_issues:
        # Обновляем ID на максимальный в пачке
        max_id = max(i["number"] for i in new_issues)
        save_last_issue_id(max_id)
    
    return new_issues

def post_reply(issue_number, text):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues/{issue_number}/comments"
    payload = {"body": text}
    response = requests.post(url, headers=HEADERS, json=payload)
    if response.status_code == 201:
        print(f"Ответ на Issue #{issue_number} отправлен.")
    else:
        print(f"Ошибка отправки: {response.status_code}")

def main():
    print("Запуск бота...")
    while True:
        new_issues = fetch_new_issues()
        for issue in new_issues:
            # Пропускаем pull requests (они тоже приходят в issues API)
            if "pull_request" in issue:
                continue
            
            title = issue["title"]
            body = issue.get("body", "") or ""
            
            # Формируем ответ (можно заменить на вызов LLM)
            reply_text = (
                f"Спасибо за обращение, **{issue['user']['login']}**!\n\n"
                f"Мы получили ваш вопрос по теме: *{title}*.\n"
                "Мейнтейнер ответит в ближайшее время. "
                "Пожалуйста, убедитесь, что вы приложили логи или шаги воспроизведения, если это баг."
            )
            
            post_reply(issue["number"], reply_text)
        
        time.sleep(60)  # Опрос раз в минуту (лимит API: 5000 запросов/час)

if __name__ == "__main__":
    main()
