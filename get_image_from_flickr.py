#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""Search & get images from flickr

Example
-------
::
    $ ./get_image_from_flickr.py -w hogehoge --per_page 5
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from logging import getLogger, StreamHandler, FileHandler, DEBUG
from datetime import datetime

import json
import requests
import argparse
import os
import re


# setup logger
logger = getLogger(__name__)
log_file_name = "{date}.log".format(
    date=datetime.now().strftime("%Y%m%d_%H%M%S"))
f_handler = FileHandler(log_file_name)
f_handler.setLevel(DEBUG)
s_handler = StreamHandler()
s_handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(f_handler)
logger.addHandler(s_handler)
logger.info('FlickrImageSearcher start')


class UrlTemplate:
    """URLの文字列テンプレート
    固定値はこのクラスの中で定義すること
    """
    """REST APIのエンドポイント"""
    URL_ENDPOINT = 'https://api.flickr.com/services/rest'
    """API種別"""
    METHOD = 'flickr.photos.search'


class FlickrImageSearcherHttpError(Exception):
    """HTTPアクセスに関するエラー

    Example
    -------
    ::
        raise FlickrImageSearcherHttpError(status_code, error_message)

    Returns
    -------
    string
        "HTTP Response: {code} {mes}"
    """

    def __init__(self, http_status_code, error_message):
        self.error_message = error_message
        self.http_status_code = http_status_code

    def __str__(self):
        return(
            "HTTP Response: {code} {mes}".format(
                code=self.http_status_code,
                mes=self.error_message
            ))


class FlickrImageSearcherPageError(Exception):
    pass


class FlickrImageSearcher:
    """Flickr API 画像検索/ダウンロードクラス
    Example
    -------
    ::
        searcher = FlickrImageSearcher('{word|file}', api_key)
    """

    def __init__(self, api_key):
        self.api_key = api_key

    def create_payload(self, word, page, per_page, lic):
        payload = {}
        payload['text'] = word
        payload['api_key'] = self.api_key
        payload['license'] = lic
        payload['per_page'] = per_page
        payload['page'] = page
        payload['method'] = UrlTemplate.METHOD
        payload['content_type'] = '1'
        payload['format'] = 'json'
        payload['nojsoncallback'] = '1'
        payload['extras'] = 'url_o,url_m'

        return payload

    def invoke_request(self, payload):
        response = requests.post(
            UrlTemplate.URL_ENDPOINT,
            payload
        )
        return response.json()

    def create_url_list(self, response):
        url_list = []
        for ph in response['photos']['photo']:
            try:
                url_list.append(
                    {
                        'key': ph['id'],
                        'url_o': ph['url_o'],
                        'url_m': ph['url_m']
                    })
            except KeyError as ex:
                logger.error('key error occurred')
                pass

        return url_list

    def download_image(self, url, filepath):
        response = requests.get(url, stream=True)
        if not response.status_code == 200:
            logger.error("server error response:{status_code} {url}".format(
                status_code=response.status_code, url=url))
            raise FlickrImageSearcherHttpError(
                response.status_code,
                'download failure'
            )
        with open(filepath, 'wb') as fp:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    fp.write(chunk)
                    fp.flush


def load_api_key(key_file_path):
    """APIキーファイルの読み込み
    指定されたファイルの1行目をAPIキーとして読み込む
    """
    with open(key_file_path, 'r') as key_file:
        api_key = key_file.readline().rstrip('\n')
        return api_key


def load_word_list(word_file_path):
    """検索ワードの読み込み
    検索ワードが改行区切りで格納されたファイルを読み込む
    """
    with open(word_file_path, 'r') as word_file:
        word_list = word_file.readlines()
        return word_list


def execute_search_query(
        searcher,
        word,
        output_dir,
        lic,
        per_page,
        page,
        originalsize):
    """単語検索/ダウンロードの内部処理
    """
    payload = searcher.create_payload(word, page, per_page, lic)
    response = searcher.invoke_request(payload)

    json_file_path = "{output_dir}/{word}_{page}.json".format(
        output_dir=output_dir,
        word=re.sub(r'\s+', '_', word),
        page=page
    )
    with open(json_file_path, 'w') as fp:
        json.dump(response, fp, indent=4)

    image_url_list = searcher.create_url_list(response)
    json_url_list_path = "{output_dir}/{word}_{page}_url.json".format(
        output_dir=output_dir,
        word=re.sub(r'\s+', '_', word),
        page=page
    )
    with open(json_url_list_path, 'w') as fp:
        json.dump(image_url_list, fp, indent=4, sort_keys=True)

    try:
        for count, image_url in enumerate(image_url_list):
            if originalsize:
                target_url = image_url['url_o']
            else:
                target_url = image_url['url_m']
            image_file_path = "{output_dir}/{file_name}".format(
                output_dir=output_dir,
                file_name=target_url.split('/')[-1]
            )
            logger.info("downloading {url} {num}/{max}".format(
                url=target_url,
                num=count + 1,
                max=str(len(response['photos']['photo']))
            ))
            searcher.download_image(target_url, image_file_path)
    except FlickrImageSearcherHttpError as ex:
        logger.error('http error occurred')
        pass

    if int(response['photos']['page']) >= int(response['photos']['pages']):
        raise(FlickrImageSearcherPageError)


def execute_word_search(
        searcher,
        word,
        output_dir,
        lic,
        per_page,
        start_page,
        max_page,
        originalsize=False):
    """単語検索/ダウンロードを実行
    """
    if start_page >= 8:
        execute_search_query(
            searcher,
            word,
            output_dir,
            lic,
            int(per_page),
            int(start_page),
            originalsize
        )
    else:
        for page in range(start_page, max_page):
            logger.info("start download {word} page {page}".format(
                word=word,
                page=page)
            )
            try:
                execute_search_query(
                    searcher,
                    word,
                    output_dir,
                    lic,
                    int(per_page),
                    int(page),
                    originalsize
                )
            except FlickrImageSearcherPageError as ex:
                break


def execute_file_search(searcher, args):
    """ファイルから検索ワードリストを読み込んで検索
    ファイル内のテキストを1行毎に検索ワードとして認識する
    """
    word_list = load_word_list(args.inputfile)
    for word in word_list:
        output_dir_name = "{output_dir}/{word}".format(
            output_dir=args.output,
            word=re.sub(r'\s+', '_', word.rstrip('\n'))
        )
        if not os.path.exists(output_dir_name):
            os.mkdir(output_dir_name)

        execute_word_search(
            searcher,
            word.rstrip('\n'),
            output_dir_name,
            args.license,
            int(args.per_page),
            int(args.start_page),
            int(args.max_page),
            args.originalsize
        )


def parsepargs():
    parser = argparse.ArgumentParser(
        description='Search & get images from flickr')
    # 検索ワードか入力ファイルのどちらか一方は必須
    group_input = parser.add_mutually_exclusive_group(required=True)
    group_input.add_argument(
        '-w',
        '--word',
        help='search query word'
    )
    group_input.add_argument(
        '-i',
        '--inputfile',
        help='search query list file'
    )

    parser.add_argument(
        '-o',
        '--output',
        default='./download',
        help='download target dir'
    )
    parser.add_argument(
        '-k',
        '--keyfile',
        default='key.txt',
        help='api key file'
    )
    parser.add_argument(
        '-l',
        '--license',
        default=4,
        help='license level at \
        www.flickr.com/services/api/flickr.photos.licenses.getInfo.html'
    )
    parser.add_argument(
        '--per_page',
        default=500,
        help='number of photos to return per page'
    )
    parser.add_argument(
        '--start_page',
        default=1,
        help='number of pages to start downloading'
    )
    parser.add_argument(
        '--max_page',
        default=8,
        help='maximum number of pages to download'
    )
    parser.add_argument(
        '--originalsize',
        action='store_true',
        help='download original image(warning: give a heavy load to network!!)'
    )

    return parser.parse_args()


def main():
    args = parsepargs()
    api_key = load_api_key(args.keyfile)

    if not os.path.exists(args.output):
        os.mkdir(args.output)

    searcher = FlickrImageSearcher(api_key)

    if args.inputfile is not None:
        execute_file_search(searcher, args)
    else:
        execute_word_search(searcher, args.word, args.originalsize)


if __name__ == '__main__':
    main()
