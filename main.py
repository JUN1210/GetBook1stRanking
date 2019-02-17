import requests
from bs4 import BeautifulSoup
import urllib
from retry import retry
import re
import pandas as pd
from email import message
import smtplib
import os

# SOGOurl = "http://www.book1st.net/ranking/0001/0001/page1.html"
# Businessurl = "http://www.book1st.net/ranking/0001/0003/page1.html"
# Bunkourl = "http://www.book1st.net/ranking/0001/0004/page1.html"
# のランキング情報を取得する

# 記事の公開日をメールの文面で見れるようにしたい。

uri = 'http://www.book1st.net/ranking/0001/'
genre = ["0001", "0003", "0004"]
category = "/page1.html"

def pages():
    urls = []
    for page in genre:
        url = uri + page + category
        urls.append(url)

    return urls

#urlsリストのページ情報を取得
@retry(urllib.error.HTTPError, tries=5, delay=2, backoff=2)
def soup_url(urls):
    soups = []
    for url in urls:
        print("...get...html...")
        htmltext = urllib.request.urlopen(url).read()
        soup = BeautifulSoup(htmltext, "lxml")
        soups.append(soup)
    return soups

#Gmailの認証データ
smtp_host = os.environ["smtp_host"]
smtp_port = os.environ["smtp_port"]
from_email = os.environ["from_email"] # 送信元のアドレス
to_email = os.environ["to_email"]  # 送りたい先のアドレス 追加時は,で追加
bcc_email = os.environ["bcc_email"]  #Bccのアドレス追加
username = os.environ["username"] # Gmailのアドレス
password = os.environ["password"] # Gmailのパスワード


#取得したページの情報から、最新の記事URLとリンクを抜き出す

#取得したページの情報から、必要なデータを抜き出す

@retry(urllib.error.HTTPError, tries=7, delay=1)
def get_ranking(soups):
    df = pd.DataFrame(index=[], columns=["genre", "ranking", "title", "author", "publisher"])
    for soup in soups:
        genre = soup.find("div", class_="selected").string

        for el in soup.find_all("div", class_="entry"):

            rank  = el.find("div", class_="rankno").find("img").get("alt")

            title  = el.find("h3", class_="entry-header")
            if title:
                title = title.string
            else:
                title = "not find"

            author = el.find("h4", class_="entry_name")
            if author:
                author = author.string
            else:
                author = "not find"

            publisher = el.find("h5", class_="entry_price")
            if publisher:
                publisher = publisher.string
            else:
                publisher = "not find"

            print("{} {} {} {} {}".format(genre, rank, title, author, publisher))
            series = pd.Series([genre, rank, title, author, publisher], index = df.columns)

            if series["ranking"] != "not find":
                df = df.append(series, ignore_index = True)

        update = soup.find("div", id="update").string

    return df, update


def mail(update):
    # メールの内容を作成
    msg = message.EmailMessage()
    msg.set_content('Book1st Ranking') # メールの本文
    msg['Subject'] = 'Book1st Ranking' + update # 件名
    msg['From'] = from_email # メール送信元
    msg['To'] = to_email #メール送信先
    msg['Bcc'] = bcc_email #bcc送信先

    #添付ファイルを作成する。
    mine={'type':'text','subtype':'comma-separated-values'}
    attach_file={'name':'Book1stRankingBooks.csv','path':'./Book1stRankingBooks.csv'}
    file = open(attach_file['path'],'rb')
    file_read = file.read()
    msg.add_attachment(file_read, maintype=mine['type'],
    subtype=mine['subtype'],filename=attach_file['name'])
    file.close()

    # メールサーバーへアクセス
    server = smtplib.SMTP(smtp_host, smtp_port)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(username, password)
    server.send_message(msg)
    server.quit()

#一連の実行関数

def main():
    urls = pages()
    soups = soup_url(urls)
    B1_df, update = get_ranking(soups)

    with open("Book1stRankingBooks.csv",mode="w",encoding="cp932",errors="ignore")as f:
        B1_df.to_csv(f)
    mail(update)

    with open("Book1stRankingBooks.csv",mode="w",encoding="utf-8",errors="ignore")as f:
        B1_df.to_csv(f)
    mail(update)

    
if __name__ == '__main__':
    main()
