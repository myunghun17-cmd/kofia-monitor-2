import requests
from bs4 import BeautifulSoup
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

URL = "https://www.kofia.or.kr/brd/m_212/list.do"
STATE_FILE = "last_seq.txt"

SENDER_EMAIL = os.environ["SENDER_EMAIL"]
SENDER_PASSWORD = os.environ["SENDER_PASSWORD"]
RECEIVER_EMAILS = os.environ["RECEIVER_EMAIL"].split(",")

def get_latest_posts():
    res = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(res.text, "html.parser")
    rows = soup.select("table tbody tr")
    posts = []
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 2:
            try:
                seq = int(cols[0].text.strip())
                title = cols[1].text.strip()
                posts.append({"seq": seq, "title": title})
            except:
                continue
    return posts

def send_email(new_posts):
    msg = MIMEMultipart()
    msg["Subject"] = f"[KOFIA 알림] 새 안내사항 {len(new_posts)}건"
    msg["From"] = SENDER_EMAIL
    msg["To"] = ", ".join(RECEIVER_EMAILS)

    body = "금융투자협회 안내사항 새 글이 올라왔습니다.\n\n"
    for p in new_posts:
        body += f"[{p['seq']}] {p['title']}\n"
    body += f"\n바로가기: {URL}"

    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAILS, msg.as_string())
    print("이메일 발송 완료!")

def main():
    posts = get_latest_posts()
    if not posts:
        print("게시글을 가져오지 못했습니다.")
        return

    latest_seq = posts[0]["seq"]

    try:
        with open(STATE_FILE) as f:
            last_seq = int(f.read().strip())
    except:
        last_seq = latest_seq
        with open(STATE_FILE, "w") as f:
            f.write(str(last_seq))
        print(f"초기화 완료. 현재 최신글: {last_seq}")
        return

    new_posts = [p for p in posts if p["seq"] > last_seq]

    if new_posts:
        print(f"새 글 {len(new_posts)}건 발견!")
        send_email(new_posts)
        with open(STATE_FILE, "w") as f:
            f.write(str(latest_seq))
    else:
        print("새 글 없음.")

main()
