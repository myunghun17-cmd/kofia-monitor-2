import requests
from bs4 import BeautifulSoup
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SENDER_EMAIL = os.environ["SENDER_EMAIL"]
SENDER_PASSWORD = os.environ["SENDER_PASSWORD"]
RECEIVER_EMAILS = os.environ["RECEIVER_EMAIL"].split(",")

BOARDS = [
    {
        "name": "KOFIA 안내사항",
        "url": "https://www.kofia.or.kr/brd/m_212/list.do",
        "state_file": "last_seq_kofia.txt",
        "selector": "table tbody tr",
    },
    {
        "name": "KVCA 출자공고",
        "url": "https://www.kvca.or.kr/Program/invest/list.html?a_gb=board&a_cd=8&a_item=0&sm=2_2_2",
        "state_file": "last_seq_kvca.txt",
        "selector": "table tbody tr",
    },
]

def get_latest_posts(url, selector):
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(res.text, "html.parser")
    rows = soup.select(selector)
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

def send_email(board_name, url, new_posts):
    msg = MIMEMultipart()
    msg["Subject"] = f"[{board_name} 알림] 새 글 {len(new_posts)}건"
    msg["From"] = SENDER_EMAIL
    msg["To"] = ", ".join(RECEIVER_EMAILS)

    body = f"{board_name} 새 글이 올라왔습니다.\n\n"
    for p in new_posts:
        body += f"[{p['seq']}] {p['title']}\n"
    body += f"\n바로가기: {url}"

    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAILS, msg.as_string())
    print(f"{board_name} 이메일 발송 완료!")

def check_board(board):
    name = board["name"]
    url = board["url"]
    state_file = board["state_file"]
    selector = board["selector"]

    posts = get_latest_posts(url, selector)
    if not posts:
        print(f"{name} 게시글을 가져오지 못했습니다.")
        return

    latest_seq = posts[0]["seq"]

    try:
        with open(state_file) as f:
            last_seq = int(f.read().strip())
    except:
        last_seq = latest_seq
        with open(state_file, "w") as f:
            f.write(str(last_seq))
        print(f"{name} 초기화 완료. 현재 최신글: {last_seq}")
        return

    new_posts = [p for p in posts if p["seq"] > last_seq]

    if new_posts:
        print(f"{name} 새 글 {len(new_posts)}건 발견!")
        send_email(name, url, new_posts)
        with open(state_file, "w") as f:
            f.write(str(latest_seq))
    else:
        print(f"{name} 새 글 없음.")

for board in BOARDS:
    check_board(board)
