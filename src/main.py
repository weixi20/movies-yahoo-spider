#!/usr/bin/python


import os
import sys
import json
import requests
import sqlite3
from lxml import etree
from fake_useragent import UserAgent

def get_value(items):
    if not items:
        return ""
    else:
        return items[0]

def getHTMLTextW(url):
    #headers = {"User-Agent": UserAgent().chrome}
    #r = requests.get(url, headers = headers, timeout=50)
    r = requests.get(url, timeout=50, allow_redirects=False)
    if r.status_code != 200:
        print(url + " : no data")
        return 404
    else:
        print(url)
        r.encoding = r.apparent_encoding
        return r.text

def getCSVLine(conn, film_no, review_no, et_html, review_head):

    review_head_json = json.loads(review_head)
    c = conn.cursor()
    # print("Opened database successfully")

    # 映画番号
    #film_no

    # 映画名
    film_name = et_html.xpath("//meta[@name='description']/@content")
    film_name = get_value(film_name)
    if film_name != "":
        film_name = film_name.replace(" のユーザーレビュー。映画を見るならレビューをチェック！","")

    #レビュー番号
    #review_no

    #評価タイトル
    review_title = review_head_json['name']

    #投稿時間
    #timestamp = et_html.xpath("//i[@title='投稿日時']/../text()")
    review_time = et_html.xpath("//i[@class='icon-clock']/../text()")
    review_time = get_value(review_time)

    #総合評価
    star = et_html.xpath("//strong[text()='総合評価']/../../li[2]/span/i/@class")
    star = get_value(star)
    if star != "":
        star = int(star.replace("star-actived rate-",""))//40

    #閲覧数
    views = et_html.xpath("//i[@title='閲覧数']/../strong/text()")
    views = get_value(views)

    #役立ち度
    yakutachido = et_html.xpath("//i[@title='役立ち度']/../strong/text()")
    yakutachido = get_value(yakutachido)

    #本文
    review_text = review_head_json['reviewBody']

    #イメージワード
    imagewords_list = list()
    imagewords = et_html.xpath("//h4[text()='イメージワード']/../ul/li/span/text()")
    for item in imagewords:
        imagewords_list.append(item)

    #詳細評価
    points = et_html.xpath("//canvas[@data-chart-label='物語,配役,演出,映像,音楽']/@data-chart-val-user")
    points = get_value(points)
    if points != "":
        monogatari_star = points[0:1]
        haiyaku_star    = points[2:3]
        enshutu_star    = points[4:5]
        eizou_star      = points[6:7]
        onngaku_star    = points[8:9]
    else:
        monogatari_star = ""
        haiyaku_star    = ""
        enshutu_star    = ""
        eizou_star      = ""
        onngaku_star    = ""

    sql = "INSERT INTO FILM (\
            film_no, \
            film_name, \
            review_no, \
            review_title, \
            review_time, \
            star, \
            views, \
            yakutachido, \
            review_text, \
            monogatari_star, \
            haiyaku_star, \
            enshutu_star,  \
            eizou_star, \
            onngaku_star"

    for im_no in range(0,len(imagewords_list)):
        imageword_no = "imageword" + str(im_no + 1)
        sql = sql + ", " + imageword_no

    sql = sql + \
        ") VALUES (" \
            + str(film_no)              + ", " + \
            "'" + film_name + "'"       + ", " + \
            str(review_no)              + ", " + \
            "'" + review_title + "'"    + ", " + \
            "'" + review_time  + "'"    + ", " + \
            str(star)                   + ", " + \
            str(views)                  + ", " + \
            str(yakutachido)            + ", " + \
            "'" + review_text + "'"     + ", " + \
            str(monogatari_star)        + ", " + \
            str(haiyaku_star)           + ", " + \
            str(enshutu_star)           + ", " + \
            str(eizou_star)             + ", " + \
            str(onngaku_star)
            
    for im_no in range(0,len(imagewords_list)):
        imageword_value = imagewords_list[im_no]
        sql = sql + ", '" + imageword_value + "'"

    sql = sql + ");"
    #print(sql)
    c.execute(sql)

    conn.commit()
    return 0

if __name__ == "__main__":
    # filmNo = 367239 冰雪奇缘2
    # filmNo = 368007 这个电影只有45条评论，测试用

    conn = sqlite3.connect('film.db')
    print("connect database successfully")

    cur_del = conn.cursor()
    cur_del.execute("DELETE FROM FILM;")
    conn.commit()
    print("data delete successfully")

    film_list = list()
    film_list.append(1234)
    film_list.append(1235)
    for film_no in film_list:
    #for film_no in range(368007,368008):
        url = "https://movies.yahoo.co.jp/movie/" + str(film_no) + "/review/"
        html = getHTMLTextW(url)
        if html == 404:
            continue

        review_list = list()
        et_html = etree.HTML(html)

        review_cnt = et_html.xpath("//div[@class='list-controller align-center']/span/small[2]/text()")
        review_cnt = get_value(review_cnt)
        if review_cnt == "":
            continue
        else:
            review_cnt = review_cnt.replace("件/","").replace("件中","").replace(",","")
            page_cnt = int(review_cnt)//10 + 2 # range的特殊性所以+2
        
        print(review_cnt + "条评论")

        for page_cur in range(1,page_cnt):
            print(page_cur)
            url = "https://movies.yahoo.co.jp/movie/" + str(film_no) + "/review/?page=" + str(page_cur)
            html = getHTMLTextW(url)
            et_html = etree.HTML(html)
            review_urls = et_html.xpath("//a[@class='listview__element--right-icon']/@href")

            for item in review_urls:
                item = "https://movies.yahoo.co.jp/" + item
                review_list.append(item)
        
        for review_url in review_list:

            html = getHTMLTextW(review_url)
            if html == 404:
                continue
            
            view_no = review_url.split("/")[7]

            et_html = etree.HTML(html)
            id_json = et_html.xpath("//script[@type='application/ld+json']/text()")
            
            if not id_json:
                continue
            else:
                id_json = get_value(id_json)
                if id_json != "":
                    csv_line = getCSVLine(conn, film_no, view_no, et_html, id_json)
        
        
    conn.close()
    print("database connection close successfully")