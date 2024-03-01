import json
import logging
import os

import httpx

# Maximum attempts
exceed_attempt = 5
# uma domain
uma_domain = 'umamusume.jp'
# adapt
com_str = ['grass', 'mud', 'short', 'mile', 'middle', 'long', 'run_away', 'first', 'center', 'chase']
logging.basicConfig(level=logging.INFO)
dir_name = os.path.dirname(__file__)
# headers
default_headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br',
    'Origin': f'https://{uma_domain}',
    'Referer': f'https://{uma_domain}/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0'
}


# Copy the cache file content to a real configuration file
async def replace_config(current_dir_tmp: str, current_dir: str):
    with open(current_dir_tmp, 'r', encoding='UTF-8') as f:
        uma_data = json.load(f)
        f.close()
    with open(current_dir, 'w', encoding='UTF-8') as af:
        json.dump(uma_data, af, indent=4, ensure_ascii=False)


# send async request
async def async_request(url, method='GET', headers=None, params=None, json_data=None, timeout=None):
    logging.info(f'url = {url}')
    async with httpx.AsyncClient(headers=headers, params=params, timeout=timeout) as client:
        if method == 'GET':
            response = await client.get(url)
        elif method == 'POST':
            response = await client.post(url, json=json_data)
        elif method == 'PUT':
            response = await client.put(url, json=json_data)
        elif method == 'DELETE':
            response = await client.delete(url)
        else:
            raise ValueError('Unsupported HTTP method')
        return response


# 下载文件
async def download_file(url, download_dir, file_name):
    file_path = os.path.join(download_dir, file_name)
    if not url:
        return
    if os.path.exists(file_path):
        logging.warning(f'{file_name} already exist!')
        return
    res = await async_request(url)
    if 200 == res.status_code:
        with open(file_path, 'wb') as fd:
            fd.write(res.content)
        logging.info(f'{file_name} download success!')
    else:
        logging.error(f'{file_name} download fail: code {res.status_code}!')
